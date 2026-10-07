"""Build private, read-only replay inputs from hash-verified audit observations."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess

from raven_harness.harness.observation import build_context, build_observation
from raven_harness.game.state import state_path
from raven_harness.harness.reachability_tools import movement_reachability
from raven_harness.harness.context_experiments import dump, render

ROOT = Path(__file__).resolve().parents[2]
CASES = {
    "D048": (
        "How many power tokens does mustering cost? Does upgrading a footman increase army size?",
        ["0", "no"],
    ),
    "D068": (
        "Can your land army currently move from Crackclaw Point to Riverrun in one march using your ships? Can The Reach support a battle at Riverrun?",
        ["no", "no"],
    ),
    "D076": (
        "What is the current Wildling strength? Is the other houses' total bid known to you now?",
        ["4", "no"],
    ),
    "D110": (
        "Did your last mustering action create a footman in The Reach? How many recruitments were omitted for Supply?",
        ["no", "1"],
    ),
    "D116": (
        "At the current battle, how much confirmed support strength does Baratheon have? Can Kingswood or Shipbreaker Bay support that battlefield?",
        ["0", "no"],
    ),
    "D120": (
        "Where is the CURRENT battle? Are you attacker or defender? What is your army strength before cards?",
        ["harrenhal", "defender", "0"],
    ),
    "D141": (
        "How many scoring areas would capturing Castle Black add? Can The Shivering Sea support a battle at Moat Cailin?",
        ["0", "no"],
    ),
    "D150": (
        "What does selecting a card do in this decision? Answer replacement_combat_card or discard_to_draw.",
        ["replacement_combat_card"],
    ),
    "D154": (
        "What are Lannister's and Baratheon's current combat totals without spending the blade? Who wins if Baratheon uses the blade?",
        ["4", "3", "baratheon"],
    ),
    "D160": (
        "How many scoring areas TOTAL does Lannister control? How many further rounds remain after the current round?",
        ["4", "0"],
    ),
}


def archived_input_hash(observation):
    """Reconstruct the audited run's original input envelope, not today's prompt."""
    obs = dict(observation)
    briefing = obs.pop("decisionBriefing")
    text = (
        "Read the current board state, then follow the decision instructions below."
        + "\n\nCurrent observation:\n"
        + json.dumps(obs, separators=(",", ":"))
        + "\n\nCurrent decision:\n"
        + briefing
        + "\n\nHow to complete this decision:\n"
        + "You MUST call submit_action to submit your gameplay action. A text response "
        + "does not submit anything. Use the exact fields and enum values in the current "
        + "submit_action schema. Explore liberally with the other tools whenever they can "
        + "test a route, target, threat, rule, memory, or assumption. Inspect the results, "
        + "then call submit_action. Exploration tools do not submit an action."
    )
    return hashlib.sha256(text.encode()).hexdigest()


def prepare(source: Path, output: Path):
    rows = json.loads(
        (
            source / "docs/analysis/oss-full-run-audit-2026-09-23/inventory.json"
        ).read_text()
    )
    db_path = (
        source
        / "data/evaluations/reachable-routes-oss-cerebras-20260922-medium/harness.db"
    )
    db = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    cases = []
    for row in rows:
        if row["key"] not in CASES:
            continue
        assert row["inputVerification"]["reconstructedHashMatches"]
        run = db.execute(
            "SELECT * FROM agent_runs WHERE id=?", (row["runId"],)
        ).fetchone()
        raw = db.execute(
            "SELECT snapshot_json FROM player_snapshots WHERE agent_id=? AND leaf_state_id=? AND created_at<=? ORDER BY id DESC LIMIT 1",
            (run["agent_id"], row["observation"]["game"]["stateId"], run["created_at"]),
        ).fetchone()
        snapshot = json.loads(raw[0])
        obs = row["observation"]
        assert (
            archived_input_hash(obs)
            == json.loads(run["context_json"])["currentInputSha256"]
        )
        # Leaf choices were sometimes mutated in the archived observation. Use
        # the hash-verified input leaf, never a later submitted choice.
        leaf = state_path(snapshot)[-1]
        leaf.clear()
        leaf.update(
            {
                k: v
                for k, v in obs["pendingDecision"].items()
                if k not in {"currentTrack", "bidFieldMeaning"}
            }
        )
        context = build_context(snapshot, obs["you"]["userId"])
        built = build_observation(context)
        for key in (
            "board",
            "houses",
            "you",
            "tracks",
            "revealedOrders",
            "houseCardStatus",
        ):
            assert built[key] == obs[key], (
                f"{row['key']}: snapshot/input disagree on {key}"
            )
        prior = next(
            (
                r
                for r in reversed(rows[: rows.index(row)])
                if r["house"] == row["house"]
                and r["observation"]["game"]["stateId"] != obs["game"]["stateId"]
            ),
            None,
        )
        if prior:
            prior_run = db.execute(
                "SELECT context_json FROM agent_runs WHERE id=?", (prior["runId"],)
            ).fetchone()
            assert (
                archived_input_hash(prior["observation"])
                == json.loads(prior_run[0])["currentInputSha256"]
            )
            prior = {
                k: prior[k]
                for k in ("key", "observation", "action", "arguments", "status")
            }
        cases.append(
            dict(
                key=row["key"],
                snapshot=snapshot,
                observation=obs,
                previous=prior,
                question=CASES[row["key"]][0],
                expected=CASES[row["key"]][1],
                observationSha256=hashlib.sha256(dump(obs).encode()).hexdigest(),
            )
        )
    server = ROOT / "swords-and-ravens/agot-bg-game-server"
    result = subprocess.run(
        [
            str(server / "node_modules/.bin/ts-node"),
            "--transpile-only",
            "--project",
            str(server / "tsconfig.json"),
            str(Path(__file__).with_name("engine_context.ts")),
        ],
        cwd=server,
        input=dump(cases),
        text=True,
        capture_output=True,
        check=True,
    )
    engines = {e["key"]: e for e in json.loads(result.stdout)}
    import tiktoken

    encoding = tiktoken.get_encoding("o200k_base")
    for case in cases:
        case["engine"] = engines[case["key"]]
        context = build_context(case["snapshot"], case["observation"]["you"]["userId"])
        case["routes"] = {
            area: movement_reachability(context, area)
            for area in ("crackclaw-point", "winterfell")
        }
        case["prompts"] = {
            policy: render(
                policy, case["observation"], case["engine"], case["previous"]
            )
            for policy in (
                "baseline",
                "briefing",
                "continuity",
                "progressive",
                "verified",
            )
        }
        case["estimatedContextTokens"] = {
            p: len(encoding.encode(text)) for p, text in case["prompts"].items()
        }
    output.mkdir(parents=True, exist_ok=True)
    (output / "cases.json").write_text(json.dumps(cases, indent=2) + "\n")
    for case in cases:
        for policy, prompt in case["prompts"].items():
            (output / f"{case['key']}-{policy}.txt").write_text(prompt + "\n")
    print(
        json.dumps(
            {
                c["key"]: {
                    "combat": c["engine"]["combat"],
                    "tokens": c["estimatedContextTokens"],
                }
                for c in cases
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "data/context-experiment")
    args = parser.parse_args()
    prepare(args.source, args.output)
