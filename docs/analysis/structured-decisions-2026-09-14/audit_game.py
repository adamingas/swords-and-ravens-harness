"""Summarize actual accepted actions using hash-verified model observations."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sqlite3

from raven_harness.game.map_reference import observation_map_reference


def reasoning(items):
    for item in items:
        if item.get("type") == "partial_model_response":
            yield from reasoning(item["output"])
        elif item.get("type") == "reasoning":
            for content in item.get("content", []):
                if isinstance(content, dict) and isinstance(content.get("text"), str):
                    yield content["text"]


def audit(directory):
    path = (directory / "harness.db").resolve()
    with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        db.execute("BEGIN")
        messages = db.execute("SELECT message_data FROM agent_messages").fetchall()
        runs = [dict(row) for row in db.execute(
            "SELECT id,status,tool_name,tool_arguments_json,context_json,observation_json,"
            "response_json,error,created_at FROM agent_runs ORDER BY created_at"
        )]
    inputs = {}
    exploration_calls = Counter()
    for row in messages:
        message = json.loads(row[0])
        if message.get("type") == "function_call":
            exploration_calls[message.get("name")] += 1
        content = message.get("content")
        if message.get("role") == "user" and isinstance(content, str) and "\n\nCurrent observation:\n" in content:
            observation_text = content.split("\n\nCurrent observation:\n", 1)[1].split("\n\nCurrent decision:\n", 1)[0].split("\n\nFinal action format for this decision:\n", 1)[0]
            inputs[hashlib.sha256(content.encode()).hexdigest()] = json.loads(observation_text)
    accepted, errors, flags = [], [], []
    for run in runs:
        if run["status"] != "completed":
            errors.append({"run": run["id"], "error": run["error"]})
            continue
        manifest = json.loads(run["context_json"] or "{}")
        observation = inputs.get(manifest.get("currentInputSha256"))
        verified = observation is not None
        if observation is None:
            observation = json.loads(run["observation_json"])
        action = run["tool_name"]
        arguments = json.loads(run["tool_arguments_json"] or "{}")
        entry = {"run": run["id"], "round": observation["game"]["round"],
                 "house": observation["you"]["houseId"], "action": action,
                 "arguments": arguments, "inputHashVerified": verified}
        stages = [item.get("stage") for item in manifest.get("modelRequestInputs", [])]
        entry["requestStages"] = stages
        if action == "resolve_march" and verified:
            source_id = arguments["starting_region_id"]
            guidance = observation.get("actionGuidance", {})
            sources = guidance.get("legalOrderRegions", [])
            source = next((s for s in sources if s["regionId"] == source_id), None)
            if source:
                destinations = {d["regionId"]: d for d in source["reachableRegions"]}
                moves = arguments.get("moves", [])
                moved = {u for m in moves for u in m["unit_ids"]}
                gained = sum(destinations[m["destination_region_id"]].get("castleAreasGainedIfCaptured", 0) for m in moves)
                lost = source.get("castleAreasLostIfEmptiedWithoutToken", 0) if moved == set(source["unitIds"]) and not arguments["leave_power_token"] else 0
                combat = any(destinations[m["destination_region_id"]]["triggersCombat"] for m in moves)
                entry.update(castlesGainedIfSuccessful=gained, sourceCastlesLost=lost, combat=combat)
                easy_castles = [d["regionId"] for d in source["reachableRegions"]
                                if d.get("castleAreasGainedIfCaptured", 0) and not d["triggersCombat"]
                                and not d["neutralForce"] and d.get("supplySafeUnitIdGroupsWhenChosenAlone")]
                if lost > gained or (not moves and easy_castles):
                    flags.append({**entry, "reviewReason": "castle loss or pass with an undefended castle reachable",
                                  "reachableCastles": easy_castles,
                                  "returnedReasoning": list(reasoning(json.loads(run["response_json"] or "[]")))})
        elif action == "select_units":
            board = {u["id"]: {**u, "region": r["id"]} for r in observation.get("board", []) for u in r.get("units", [])}
            entry["selectedPieces"] = [board.get(u, {"id": u}) for u in arguments.get("unit_ids", [])]
            entry["event"] = observation["statePath"]
            entry["returnedReasoning"] = list(reasoning(json.loads(run["response_json"] or "[]")))
        elif action == "submit_orders":
            static = {a["id"]: a for a in observation_map_reference(observation)["regions"]}
            entry["landMarchAreas"] = [a["region_id"] for a in arguments.get("applied_orders", [])
                                       if a["order"] == "march" and static[a["region_id"]]["type"] == "land"]
            if not entry["landMarchAreas"]:
                flags.append({**entry, "reviewReason": "planning has no land March",
                              "returnedReasoning": list(reasoning(json.loads(run["response_json"] or "[]")))})
        accepted.append(entry)
    report = {"accepted": accepted, "failedRuns": errors, "requiresHumanReview": flags,
              "explorationToolCalls": dict(exploration_calls),
              "counts": {"accepted": len(accepted), "verifiedInputs": sum(e["inputHashVerified"] for e in accepted),
                         "twoStageAccepted": sum(bool(e["requestStages"]) and e["requestStages"][-1] == "submission"
                                                 and e["requestStages"].count("submission") == 1
                                                 and "exploration" in e["requestStages"] for e in accepted),
                         "failed": len(errors), "reviewFlags": len(flags)}}
    (directory / "decision-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    result = audit(parser.parse_args().directory)
    print(json.dumps(result["counts"]))
