"""Read-only trace audit of the two self-play games; safe during live play."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3


def response_items(items):
    for item in items:
        if item.get("type") == "partial_model_response":
            yield from response_items(item.get("output", []))
        else:
            yield item


def audit(directory):
    manifest = json.loads((directory / "manifest.json").read_text())
    database = (directory / "harness.db").resolve()
    # Closed, checkpointed databases need no WAL sidecar creation by SQLite.
    checkpointed = (
        manifest["status"] != "running"
        and not database.with_name(database.name + "-wal").exists()
    )
    connection = sqlite3.connect(
        database.as_uri() + "?mode=ro" + ("&immutable=1" if checkpointed else ""),
        uri=True,
    )
    connection.row_factory = sqlite3.Row
    with connection:
        connection.execute("BEGIN")
        rows = connection.execute(
            "SELECT * FROM agent_runs ORDER BY created_at"
        ).fetchall()
        latest_event = connection.execute(
            "SELECT kind, payload_json, created_at FROM agent_events "
            "WHERE kind LIKE 'model-%' ORDER BY id DESC LIMIT 1"
        ).fetchone()
    connection.close()
    decisions = []
    tools = Counter()
    providers = Counter()
    models = Counter()
    totals = Counter()
    seen_responses = set()
    for row in rows:
        observation = json.loads(row["observation_json"])
        items = list(response_items(json.loads(row["response_json"] or "[]")))
        calls = []
        seen_calls = set()
        handoff = None
        reasoning = []
        for item in items:
            if item.get("type") == "function_call":
                identity = item.get("call_id") or item.get("id")
                if identity in seen_calls:
                    continue
                seen_calls.add(identity)
                name = item.get("name")
                tools[name] += 1
                arguments = item.get("arguments", {})
                if isinstance(arguments, str):
                    try:
                        arguments = json.loads(arguments)
                    except json.JSONDecodeError:
                        arguments = {"unparsed": arguments}
                calls.append({"name": name, "arguments": arguments})
                if name == "submit_action":
                    handoff = arguments.get("strategic_handoff")
            elif item.get("type") == "reasoning":
                reasoning.extend(
                    content["text"]
                    for content in item.get("content", [])
                    if isinstance(content, dict) and content.get("text")
                )
        usage = json.loads(row["raw_usage_json"] or "[]")
        for record in usage:
            identity = record.get("response_id")
            if identity and identity in seen_responses:
                continue
            if identity:
                seen_responses.add(identity)
            totals["responses"] += 1
            totals["inputTokens"] += record.get("input_tokens", 0)
            totals["outputTokens"] += record.get("output_tokens", 0)
            totals["cachedInputTokens"] += (
                record.get("input_tokens_details") or {}
            ).get("cached_tokens", 0)
            totals["reasoningTokens"] += (
                record.get("output_tokens_details") or {}
            ).get("reasoning_tokens", 0)
            if record.get("cost") is not None:
                totals["reportedCostUsd"] += record["cost"]
                totals["responsesWithCost"] += 1
            providers[record.get("response_provider") or "not returned"] += 1
            models[record.get("response_model") or "not returned"] += 1
        decisions.append({
            "runId": row["id"], "status": row["status"],
            "round": observation["game"].get("round"),
            "house": observation["you"].get("houseId"),
            "phase": observation["statePath"],
            "createdAt": row["created_at"], "durationMs": row["duration_ms"],
            "action": row["tool_name"],
            "arguments": json.loads(row["tool_arguments_json"] or "{}"),
            "error": row["error"], "strategicHandoff": handoff,
            "previousPlan": observation.get("strategicMemory", {}).get("modelPlan"),
            "modelRequests": len(usage), "toolCalls": calls,
            "returnedReasoning": reasoning,
        })
    latest = json.loads(rows[-1]["observation_json"]) if rows else {}
    report = {
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "status": manifest["status"], "model": manifest["model"],
        "roundAtLatestRecordedDecision": latest.get("game", {}).get("round"),
        "statusCounts": dict(Counter(row["status"] for row in rows)),
        "totalsForPersistedRuns": dict(totals),
        "toolCalls": dict(tools), "returnedProviders": dict(providers),
        "returnedModels": dict(models),
        "latestEvent": dict(latest_event) if latest_event else None,
        "progress": json.loads((directory / "progress.json").read_text()),
        "decisions": decisions,
    }
    (directory / "decision-audit.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    return {key: value for key, value in report.items()
            if key not in ("decisions", "progress", "latestEvent")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    print(json.dumps(audit(parser.parse_args().directory), indent=2))
