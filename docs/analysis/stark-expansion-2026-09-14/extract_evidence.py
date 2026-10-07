"""Reproduce the Stark investigation from closed local evaluation artifacts.

Run from any directory with Python 3.9+: python3 /path/to/extract_evidence.py
Uses SQLite read-only immutable access; refuses databases with a nonempty WAL.
Does not call models, start games, or expose agents' authentication columns.
"""

import collections
import hashlib
import json
from pathlib import Path
import sqlite3


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
CASES = {
    "A": "gpt-oss-120b-house-test-b4279fb/game-01/attempt-01",
    "B": "gpt-oss-120b-house-test-4747688/game-01/attempt-01",
    "C": "model-tournament-ebae98a/game-03/attempt-02",
}
NORTH = {
    "winterfell", "white-harbor", "castle-black", "karhold", "moat-cailin",
    "the-stony-shore", "widows-watch", "bay-of-ice", "the-shivering-sea",
    "the-narrow-sea", "flints-finger", "seagard", "greywater-watch",
    "port-of-winterfell",
}


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def read_db(path):
    wal = Path(str(path) + "-wal")
    if wal.exists() and wal.stat().st_size:
        raise RuntimeError(f"Nonempty WAL: take a consistent snapshot first: {wal}")
    conn = sqlite3.connect(path.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def extract_case(label, relative):
    directory = ROOT / "data/evaluations" / relative
    result = json.loads((directory / "result.json").read_text())
    game = json.loads((directory / "game.json").read_text())
    conn = read_db(directory / "harness.db")
    # Match immutable serialized SDK inputs, rather than the mutable observation
    # object serialized into agent_runs only after the action has completed.
    messages = {}
    for row in conn.execute("SELECT id, session_id, message_data FROM agent_messages"):
        item = json.loads(row["message_data"])
        content = item.get("content")
        if isinstance(content, str) and content.startswith("A new decision starts"):
            messages[(row["session_id"], digest(content))] = (row["id"], content)

    records = []
    for row in conn.execute("SELECT * FROM agent_runs ORDER BY created_at, id"):
        saved = json.loads(row["observation_json"])
        if saved.get("you", {}).get("houseId") != "stark":
            continue
        manifest = json.loads(row["context_json"] or "{}")
        key = ("raven-agent-" + row["agent_id"], manifest.get("currentInputSha256"))
        matched = messages.get(key)
        original = json.loads(matched[1].split("\n\n", 1)[1]) if matched else None
        # Unmatched failures remain explicitly unverified; never silently
        # represent a saved post-run object as the provider's original input.
        obs = original or saved
        response = json.loads(row["response_json"] or "[]")
        reasoning = [
            text["text"]
            for item in response if item.get("type") == "reasoning"
            for text in item.get("content", []) if text.get("text")
        ]
        calls = [
            {"name": item["name"], "arguments": json.loads(item["arguments"])}
            for item in response if item.get("type") == "function_call"
        ]
        tool_errors = [
            item["output"] for item in response
            if item.get("type") == "function_call_output"
            and isinstance(item.get("output"), str)
            and ("An error occurred" in item["output"] or '"ok": false' in item["output"])
        ]
        map_regions = {region["id"]: region for region in obs["map"]["regions"]}
        you = {k: v for k, v in obs["you"].items() if k != "availableHouseCards"}
        controlled_land = [
            region for region in you.get("controlledRegions", [])
            if map_regions[region]["type"] == "land"
        ]
        memory = obs.get("strategicMemory", {})
        records.append({
            "ref": f"{label}{len(records) + 1:02d}",
            "run_id": row["id"], "history_id": row["history_id"],
            "agent_id": row["agent_id"], "model": row["model"],
            "created_at": row["created_at"], "status": row["status"],
            "round": obs["game"]["round"], "phase": obs["game"]["phase"],
            "accepted_action": row["tool_name"],
            "accepted_arguments": json.loads(row["tool_arguments_json"] or "null"),
            "error": row["error"], "reasoning_text": reasoning,
            "model_calls": calls, "tool_errors": tool_errors,
            "sdk_message_id": matched[0] if matched else None,
            "input_sha256": manifest.get("currentInputSha256"),
            "input_hash_verified": bool(matched),
            "saved_observation_changed_fields": (
                [k for k in original if original[k] != saved.get(k)] if original else None
            ),
            "instructions_sha256": digest(row["instructions"] or ""),
            "tools_available": [t["name"] for t in json.loads(row["tools_json"] or "[]")],
            "context_policy": manifest.get("policy"),
            "model_request_inputs": manifest.get("modelRequestInputs", []),
            "observation_excerpt": {
                "game": obs["game"], "you": you, "controlled_land": controlled_land,
                "statePath": obs["statePath"], "pendingDecision": obs["pendingDecision"],
                "planningConstraints": obs.get("planningConstraints"),
                "actionGuidance": obs.get("actionGuidance"),
                "north_board": [r for r in obs["board"] if r["id"] in NORTH],
                "modelPlan": memory.get("modelPlan"),
                "situationAssessment": memory.get("situationAssessment"),
                "lessons": memory.get("lessons"),
                "map_region_count": len(map_regions), "board_region_count": len(obs["board"]),
            },
        })
    conn.close()
    own_standing = next(s for s in result["standings"] if s["house"] == "stark")
    logs = game["childGameState"]["gameLogManager"]["logs"]
    relevant_logs = [
        {"index": i, "time": item["time"], "data": item["data"]}
        for i, item in enumerate(logs)
        if "stark" in json.dumps(item["data"])
        and item["data"]["type"] in {
            "march-resolved", "leave-power-token-choice", "consolidate-power-order-resolved",
            "player-mustered", "attack", "combat-result", "raid-done", "wildling-bidding",
            "mammoth-riders-destroy-units", "the-horde-descends-units-killed",
            "crow-killers-footman-upgraded",
        }
    ]
    calls = collections.Counter(c["name"] for r in records for c in r["model_calls"])
    no_march = [
        r["round"] for r in records if r["accepted_action"] == "submit_orders"
        and not any(o["order"] == "march" for o in r["accepted_arguments"]["applied_orders"])
    ]
    return {
        "artifact_directory": str(directory.relative_to(ROOT)),
        "result_sha256": digest((directory / "result.json").read_text()),
        "game_sha256": digest((directory / "game.json").read_text()),
        "completed_at": result["completedAt"], "random_seed": result["randomSeed"],
        "end_round": result["round"], "winner": result["winner"],
        "stark_standing": {k: v for k, v in own_standing.items() if k != "metrics"},
        "north_map": [r for r in map_regions.values() if r["id"] in NORTH],
        "statistics": {
            "runs": len(records),
            "status_counts": dict(collections.Counter(r["status"] for r in records)),
            "hash_verified_inputs": sum(r["input_hash_verified"] for r in records),
            "saved_observations_with_changes": sum(bool(r["saved_observation_changed_fields"]) for r in records),
            "runs_with_reasoning_text": sum(bool(r["reasoning_text"]) for r in records),
            "model_tool_call_counts": dict(calls), "no_march_order_rounds": no_march,
        },
        "stark_game_logs": relevant_logs, "runs": records,
    }


def census():
    results = []
    for path in sorted((ROOT / "data/evaluations").glob("**/result.json")):
        result = json.loads(path.read_text())
        if not result.get("standings") or not (path.parent / "game.json").exists():
            continue
        game = json.loads((path.parent / "game.json").read_text())
        ingame = game.get("childGameState", {})
        settings = ingame.get("game", {})
        # Classify by configured limits and terminal state, independently of
        # the actual ending round, so early victories would also be counted.
        if (settings.get("maxTurns") != 10
                or settings.get("victoryPointsCountNeededToWin") != 7
                or ingame.get("childGameState", {}).get("type") != "game-ended"):
            continue
        results.append({
            "result_path": str(path.relative_to(ROOT)), "round": result["round"],
            "winner": result["winner"],
            "standings": [
                {k: s.get(k) for k in ("house", "model", "placement", "victoryPoints", "landAreas")}
                for s in result["standings"]
            ],
        })
    return results


def main():
    evidence = {
        "scope": "Local completed-game forensic review, 2026-09-14",
        "input_verification": "SHA-256 of the exact serialized SDK user-message content, matched against agent_runs.context_json.currentInputSha256",
        "completed_full_games": census(),
        "cases": {label: extract_case(label, relative) for label, relative in CASES.items()},
    }
    # Validate the material findings against independently recorded game logs.
    a, b, c = (evidence["cases"][label] for label in "ABC")
    assert [a["statistics"]["hash_verified_inputs"], b["statistics"]["hash_verified_inputs"], c["statistics"]["hash_verified_inputs"]] == [25, 37, 32]
    assert a["runs"][2]["accepted_arguments"]["leave_power_token"] is False
    assert a["runs"][3]["observation_excerpt"]["you"]["currentVictoryPoints"] == 1
    assert a["statistics"]["no_march_order_rounds"] == [2, 3, 4, 5, 6, 8, 9, 10]
    assert c["statistics"]["no_march_order_rounds"] == list(range(3, 11))
    assert c["statistics"]["model_tool_call_counts"]["skip_mustering"] == 4
    assert all(case["statistics"]["model_tool_call_counts"].get("ask_rules_oracle", 0) == 0 for case in (a, b, c))
    assert b["runs"][35]["accepted_arguments"]["moves"][0]["destination_region_id"] == "winterfell"
    sea_zero = [l for l in a["stark_game_logs"] if l["data"]["type"] == "consolidate-power-order-resolved" and l["data"]["powerTokenCount"] == 0]
    assert len(sea_zero) == 10
    (OUT / "evidence.json").write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"full_length_results": len(evidence["completed_full_games"]), "cases": {label: case["statistics"] for label, case in evidence["cases"].items()}}, indent=2))


if __name__ == "__main__":
    main()
