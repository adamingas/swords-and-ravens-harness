"""Refresh the experiment report until both existing game processes stop."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
import time

from audit import audit


LABELS = ("oss-cerebras", "deepseek-flash")


def refresh(root):
    reports = {}
    manifests = {}
    for label in LABELS:
        directory = root / label
        manifests[label] = json.loads((directory / "manifest.json").read_text())
        audit(directory)
        reports[label] = json.loads((directory / "decision-audit.json").read_text())

    lines = [
        "# Current harness: two three-player self-play games",
        "",
        f"Updated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "Both games began concurrently on 2026-09-20, using seed 102 and the native "
        "three-player base game: Baratheon, Lannister, and Stark. The production "
        "harness is commit `3839f91d6e15984058df883c7296be4f03f53cdd`. "
        "The no-provider protocol smoke passed before launch. "
        "No gameplay runtime or prompt was changed for this experiment.",
        "",
        "GPT-OSS uses `openai/gpt-oss-120b`, restricted to Cerebras with fallback "
        "disabled. DeepSeek uses `deepseek/deepseek-v4.1-flash` with the existing "
        "provider exclusions: together, gmicloud, alibaba, novita, makora, siliconflow. "
        "Both use reasoning effort high, required tools, submit_action, normal "
        "simultaneous-player concurrency, and the current retry settings. "
        "There is no harness output-token cap. Each launcher segment has a "
        "six-hour wall-clock limit, with saves and traces retained on interruption.",
        "",
        "| Game | Status | Round | Accepted decisions | Failed / cancelled attempts | "
        "Reported cost | Median accepted decision |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for label in LABELS:
        report = reports[label]
        manifest = manifests[label]
        counts = report["statusCounts"]
        accepted = [d for d in report["decisions"] if d["status"] == "completed"]
        median = statistics.median(d["durationMs"] for d in accepted) / 1000
        round_number = manifest.get("result", {}).get(
            "round", report["roundAtLatestRecordedDecision"]
        )
        lines.append(
            f"| {label} | {manifest['status']} | {round_number} | "
            f"{counts.get('completed', 0)} | {counts.get('failed', 0)} / "
            f"{counts.get('cancelled', 0)} | "
            f"${report['totalsForPersistedRuns'].get('reportedCostUsd', 0):.4f} | "
            f"{median:.1f} s |"
        )
    lines += [
        "",
        "Counts and costs include persisted attempts across resumes. Active requests "
        "may incur usage that is not yet persisted or returned by the provider. "
        "A running game's round is from its latest recorded decision. "
        "Provider responses identify the expected model IDs but do not return "
        "upstream provider attribution; the requested routing is recorded in each manifest.",
        "",
        "## Observed decision quality",
        "",
        "These are qualitative observations from the saved decisions, not a controlled "
        "old-versus-new-harness comparison. Two different models playing different "
        "self-play trajectories cannot establish aggregate improvement from the harness change.",
        "",
        "### GPT-OSS / Cerebras",
        "",
        "The game stopped in round 3 after 34 accepted decisions. Baratheon repeatedly "
        "submitted Dragonstone -> Storm's End, describing it as an uncontested castle, "
        "despite the observation showing a 1,000-strength garrison. The server rejected "
        "the move. The same failure repeated after one unchanged-runtime resume. "
        "Provider responses eventually ended with `max_output_tokens`; the failing "
        "responses reported 8,192 output tokens despite the harness imposing no output cap.",
        "",
        "This also exposes a harness guidance weakness: Storm's End was present in "
        "`actionGuidance.legalOrderRegions[].reachableRegions`, with `neutralForce: null`, "
        "although the garrison and static rules show that it is impassable. The rejection "
        "message only said that the authoritative state did not reflect the action. "
        "The failure should not be attributed solely to model quality.",
        "",
        "Evidence: failed run `0ffe7d1b-c69c-4f4f-9944-d726cf8067d0` and resumed failure "
        "`4ff9c144-fe0f-45f6-8bf9-ac2347f2c549` in `oss-cerebras/harness.db`. "
        "There is no winner or completed-game result.",
        "",
        "### DeepSeek V4.1 Flash",
        "",
        "The first segment completed 94 decisions through round 6. At its last recorded "
        "decision, Lannister held 5 castle areas, Baratheon 4, and Stark 3. It reached "
        "the six-hour launcher limit and was resumed with the same runtime, routing, "
        "model, seed, and persisted private memories.",
        "",
        "Concrete positive examples:",
        "",
        "- Round 1 Baratheon planned and executed two separate marches to take "
        "Crackclaw Point and The Reach while leaving a token to retain Kingswood. "
        "Runs `ea838acf-dbdd-43ed-acc5-a0430a707ec6` and "
        "`eea40725-870e-40a2-b5f6-ccb63284ce01`.",
        "- Round 5 Lannister chose Cersei in a battle it could win with a zero-strength "
        "card, then carried the plan through the ability prompt to remove Winterfell's "
        "starred Consolidate Power order. This denied Stark the opportunity to muster "
        "or collect power there. Runs `bc89b371-631e-44c9-b5ec-b4132956982c`, "
        "`3d2ae859-d05a-491a-9915-cdce65d8f9e5`, and "
        "`e5cbbf58-6f1e-4c80-83d9-63ab6115f97d`.",
        "- Round 6 Lannister changed Seagard's defense order to a raid, removed "
        "Moat Cailin's stronger support order, and transported one knight from "
        "Flint's Finger to Riverrun to strengthen support for two threatened castles, "
        "while retaining Flint's Finger. Runs `d30a9438-92c1-4150-9072-52c4b3317005`, "
        "`13f8ff39-7a80-407c-b899-79d26d576d6b`, and "
        "`c8ae9d3a-e8a4-4e9b-a8bc-2176138a38d2`.",
        "",
        "Limitations already observed: the first segment's median accepted decision "
        "took 261 seconds; one accepted Raven decision took over 17 minutes. The "
        "interrupted Stark decision spent almost 20 minutes reconsidering its march "
        "without submitting. One accepted handoff was literally `PLACEHOLDER` "
        "(run `f9ce8a9a-d05d-45bd-a635-c732acdeb13b`). More thinking and more tool calls "
        "therefore do not consistently produce useful decisions or memory.",
        "",
        "## Current results and artifacts",
        "",
    ]
    for label in LABELS:
        manifest = manifests[label]
        lines += [f"### {label}", ""]
        if manifest["status"] == "completed":
            result = manifest["result"]
            lines += [f"Winner: **{result['winner']}**, round {result['round']}.", ""]
            for standing in result["standings"]:
                lines.append(
                    f"- {standing['house']}: {standing['victoryPoints']} castle areas, "
                    f"placement {standing['placement']}."
                )
            lines.append("")
        elif manifest["status"] == "running":
            lines += ["The resumed game is still running; no winner is established.", ""]
        else:
            lines += [f"Stop reason: {manifest.get('error', 'not recorded')}", ""]
        for filename in ("manifest.json", "progress.json", "decision-audit.json", "harness.db", "game.json"):
            lines.append(f"- [{filename}]({(root / label / filename).resolve()})")
        lines.append("")
    (root / "REPORT.md").write_text("\n".join(lines) + "\n")
    return {label: manifest["status"] for label, manifest in manifests.items()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    previous = None
    while True:
        signature = []
        for label in LABELS:
            directory = args.directory / label
            manifest = json.loads((directory / "manifest.json").read_text())
            progress = json.loads((directory / "progress.json").read_text())
            signature.append((manifest["status"], tuple(
                agent["runCount"] for agent in progress["agents"]
            )))
        if signature != previous:
            statuses = refresh(args.directory)
            print(json.dumps(statuses), flush=True)
            previous = signature
            if args.once or all(status != "running" for status in statuses.values()):
                break
        time.sleep(30)
