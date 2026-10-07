"""Summarize exploration usage and its associated decisions without model calls."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sqlite3


def flatten(items):
    for item in items:
        if item.get("type") == "partial_model_response":
            yield from flatten(item.get("output", []))
        else:
            yield item


def audit(directory):
    connection = sqlite3.connect((directory / "harness.db").resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    rows = connection.execute("SELECT * FROM agent_runs ORDER BY created_at").fetchall()
    connection.close()
    tools, by_house, by_phase = Counter(), Counter(), Counter()
    route_queries, rejected = [], []
    for row in rows:
        observation = json.loads(row["observation_json"])
        items = list(flatten(json.loads(row["response_json"] or "[]")))
        outputs = {i["call_id"]: i["output"] for i in items if i.get("type") == "function_call_output"}
        house = observation["you"].get("houseId")
        seen = set()
        for call in items:
            if call.get("type") != "function_call" or call.get("call_id") in seen:
                continue
            seen.add(call.get("call_id"))
            name = call["name"]
            tools[name] += 1
            raw = outputs.get(call.get("call_id"))
            try:
                output = json.loads(raw) if isinstance(raw, str) else raw
            except (ValueError, TypeError):
                output = raw
            if name == "submit_action" and isinstance(output, dict) and output.get("accepted") is False:
                rejected.append({"runId": row["id"], "house": house, "round": observation["game"].get("round"), "output": output})
            if name != "reachable_areas":
                continue
            by_house[house] += 1
            by_phase[observation["statePath"][-1]] += 1
            arguments = json.loads(call["arguments"]) if isinstance(call["arguments"], str) else call["arguments"]
            source = output.get("source", {}).get("id") if isinstance(output, dict) else None
            units = next((r.get("units", []) for r in observation.get("board", []) if r["id"] == source), [])
            route_queries.append({
                "runId": row["id"], "house": house, "round": observation["game"].get("round"),
                "phase": observation["statePath"][-1], "arguments": arguments,
                "sourceUnitCountAtDecisionStart": len(units),
                "sourceUnitOwnersAtDecisionStart": sorted({u["allegiance"] for u in units}),
                "output": output, "action": row["tool_name"],
                "actionArguments": json.loads(row["tool_arguments_json"] or "{}"),
                "runStatus": row["status"], "error": row["error"],
            })
    result = {"tools": dict(tools), "routeQueriesByHouse": dict(by_house),
              "routeQueriesByPhase": dict(by_phase), "routeQueries": route_queries,
              "rejectedActions": rejected, "runStatuses": dict(Counter(r["status"] for r in rows))}
    (directory / "reachability-audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in {"routeQueries", "rejectedActions"}}, indent=2))
    print(json.dumps({"rejectedActions": len(rejected), "emptyOriginQueries": sum(q["sourceUnitCountAtDecisionStart"] == 0 for q in route_queries)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    audit(parser.parse_args().directory)
