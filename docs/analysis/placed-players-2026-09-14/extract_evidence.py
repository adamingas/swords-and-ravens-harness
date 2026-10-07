"""Read-only follow-up: ranks two and three, with three complete case histories.

Run from any directory with Python 3.9+. No provider calls or game mutations.
Reuses the previous investigation's closed-database guard and game census.
"""

import collections
import hashlib
import json
from pathlib import Path
import runpy
import statistics

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
previous = runpy.run_path(str(OUT.parent / "stark-expansion-2026-09-14/extract_evidence.py"))
read_db = previous["read_db"]
CASES = {
    ("gpt-oss-120b-house-test-b4279fb/game-01/attempt-01", "martell"): "D",
    ("gpt-oss-120b-house-test-b4279fb/game-01/attempt-01", "greyjoy"): "E",
    ("model-tournament-ebae98a/game-03/attempt-02", "greyjoy"): "F",
}


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def main():
    census = previous["census"]()
    standings, cases = [], {}
    for game_result in census:
        path = ROOT / Path(game_result["result_path"]).parent
        relative = str(path.relative_to(ROOT / "data/evaluations"))
        conn = read_db(path / "harness.db")
        messages = {}
        for row in conn.execute("SELECT id, session_id, message_data FROM agent_messages"):
            item = json.loads(row["message_data"])
            content = item.get("content")
            if isinstance(content, str) and content.startswith("A new decision starts"):
                messages[(row["session_id"], sha(content))] = (row["id"], content)
        houses = {s["house"]: s for s in game_result["standings"] if s["placement"] in (2, 3)}
        grouped = collections.defaultdict(list)
        for row in conn.execute("SELECT * FROM agent_runs ORDER BY created_at, id"):
            stored = json.loads(row["observation_json"])
            house = stored.get("you", {}).get("houseId")
            if house not in houses:
                continue
            context = json.loads(row["context_json"] or "{}")
            matched = messages.get(("raven-agent-" + row["agent_id"], context.get("currentInputSha256")))
            obs = json.loads(matched[1].split("\n\n", 1)[1]) if matched else stored
            grouped[house].append({
                "id": row["id"], "history_id": row["history_id"],
                "round": obs["game"]["round"], "phase": obs["game"]["phase"],
                "status": row["status"], "input_verified": bool(matched),
                "sdk_message_id": matched[0] if matched else None,
                "input_sha256": context.get("currentInputSha256"),
                "observation": obs, "accepted_action": row["tool_name"],
                "accepted_arguments": json.loads(row["tool_arguments_json"] or "null"),
                "response": json.loads(row["response_json"] or "[]"), "error": row["error"],
            })
        conn.close()
        game = json.loads((path / "game.json").read_text())
        logs = game["childGameState"]["gameLogManager"]["logs"]
        for house, records in grouped.items():
            standing = houses[house]
            orders = [r for r in records if r["accepted_action"] == "submit_orders"]
            no_march = [r["round"] for r in orders if not any(x["order"] == "march" for x in r["accepted_arguments"]["applied_orders"])]
            battles = [
                {"index": i, **item["data"]} for i, item in enumerate(logs)
                if item["data"]["type"] == "combat-result"
                and any(s["house"] == house for s in item["data"]["stats"])
            ]
            stat = {
                "artifact_directory": str(path.relative_to(ROOT)), **standing,
                "initial_land": records[0]["observation"]["you"]["controlledLandAreas"],
                "initial_vp": records[0]["observation"]["you"]["currentVictoryPoints"],
                "run_count": len(records), "hash_verified_inputs": sum(r["input_verified"] for r in records),
                "no_march_order_rounds": no_march,
                "accepted_marches": sum(r["accepted_action"] == "resolve_march" for r in records),
                "battles": len(battles), "battle_wins": sum(b["winner"] == house for b in battles),
            }
            standings.append(stat)
            label = CASES.get((relative, house))
            if not label:
                continue
            assert all(r["input_verified"] for r in records)
            map_reference = records[0]["observation"]["map"]
            for i, record in enumerate(records, 1):
                record["ref"] = f"{label}{i:02d}"
                obs = record["observation"]
                record["reasoning_text"] = [
                    part["text"] for item in record["response"] if item.get("type") == "reasoning"
                    for part in item.get("content", []) if part.get("text")
                ]
                # Keep decision facts and full returned response; put the static
                # map once per case and avoid repeating full session history.
                record["observation"] = {
                    k: v for k, v in obs.items()
                    if k in {"game", "you", "statePath", "pendingDecision", "board", "revealedOrders", "tracks", "actionGuidance", "planningConstraints"}
                }
                record["model_plan"] = obs.get("strategicMemory", {}).get("modelPlan")
            cases[label] = {
                "summary": stat, "map": map_reference,
                "result_sha256": sha((path / "result.json").read_text()),
                "game_sha256": sha((path / "game.json").read_text()),
                "runs": records, "combat_results": battles,
                "game_logs": [
                    {"index": i, **item} for i, item in enumerate(logs)
                    if house in json.dumps(item["data"])
                    and item["data"]["type"] not in {"orders-revealed", "player-action", "user-house-assignments"}
                ],
                "final_units": [
                    {"region": region["id"], "units": [u for u in region.get("units", []) if u["allegiance"] == house]}
                    for region in game["childGameState"]["game"]["world"]["regions"]
                    if any(u["allegiance"] == house for u in region.get("units", []))
                ],
            }
    by_placement = {}
    for place in (2, 3):
        rows = [r for r in standings if r["placement"] == place]
        by_placement[str(place)] = {
            "count": len(rows), "average_final_vp": statistics.mean(r["victoryPoints"] for r in rows),
            "average_final_land": statistics.mean(r["landAreas"] for r in rows),
            "average_net_land": statistics.mean(r["landAreas"] - r["initial_land"] for r in rows),
            "vp_range": [min(r["victoryPoints"] for r in rows), max(r["victoryPoints"] for r in rows)],
            "net_land_at_most_one": sum(r["landAreas"] - r["initial_land"] <= 1 for r in rows),
        }
    assert len(standings) == 22
    assert [len(cases[k]["runs"]) for k in "DEF"] == [35, 40, 41]
    assert cases["D"]["final_units"] == []
    assert cases["E"]["runs"][20]["accepted_action"] == "skip_mustering"
    assert cases["F"]["summary"]["battles"] == 6 and cases["F"]["summary"]["battle_wins"] == 0
    output = {"scope": "Second- and third-place players in eleven saved full games", "by_placement": by_placement, "standings": standings, "cases": cases}
    (OUT / "evidence.json").write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"by_placement": by_placement, "detailed_cases": {k: v["summary"] for k, v in cases.items()}}, indent=2))


if __name__ == "__main__":
    main()
