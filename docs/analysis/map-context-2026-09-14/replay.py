"""Ten-case map experiment using the production harness and read-only tools."""

import argparse
import asyncio
import copy
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from agents import FunctionTool

from raven_harness.agent_store import AgentStore
from raven_harness.config import Settings
from raven_harness.database import Database
from raven_harness.harness.actions import HarnessRunContext, describe_tools
from raven_harness.harness.interface import PreparedTurn
from raven_harness.harness.map_tools import check_neighbours, neighbouring_areas
from raven_harness.harness.observation import build_context, build_observation
from raven_harness.harness.strategic import StrategicHarness, MEMORY_TOOLS
from raven_harness.models import openai_agent as model_module
from raven_harness.rulebook import Rulebook
from raven_harness.schemas import AgentRecord

OUT = Path(__file__).resolve().parent
BASE = OUT.parent / "replay-baseline-2026-09-14"
SPEC = importlib.util.spec_from_file_location("baseline_replay", BASE / "replay.py")
baseline = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(baseline)
AUXILIARY = {
    "recall_game_state",
    "remember_strategy",
    "ask_rules_oracle",
    "check_neighbours",
    "inspect_house_card",
}


def load_snapshot(data):
    """Find a persisted snapshot matching all visible decision/board facts."""
    observation = data["observation"]
    path = baseline.ROOT / data["case"]["database"]
    with sqlite3.connect(path.resolve().as_uri() + "?mode=ro&immutable=1", uri=True) as db:
        db.row_factory = sqlite3.Row
        rows = db.execute(
            "SELECT * FROM player_snapshots WHERE agent_id=? AND leaf_state_id=? ORDER BY id",
            (data["record"]["id"], observation["game"]["stateId"]),
        ).fetchall()
        history = [dict(row) for row in db.execute(
            "SELECT * FROM game_state_history WHERE agent_id=? AND id<=? ORDER BY id",
            (data["record"]["id"], data["run"]["history_id"]),
        )]
    matches = []
    for row in rows:
        snapshot = json.loads(row["snapshot_json"])
        context = build_context(snapshot, data["record"]["user_id"], observation["recentEvents"])
        rebuilt = build_observation(context)
        keys = ("board", "revealedOrders", "pendingDecision", "you", "houses",
                "tracks", "statePath", "game", "isYourTurn")
        if all(rebuilt.get(key) == observation.get(key) for key in keys):
            # Candidates may differ in unrelated log entries. All data exposed by
            # the new tool must agree, including empty areas and control tokens.
            neighbourhoods = [neighbouring_areas(context, area["id"])
                              for area in observation["map"]["regions"]]
            matches.append((row, snapshot, neighbourhoods))
    assert matches, "No snapshot matches the historical observation"
    assert all(item[2] == matches[0][2] for item in matches), "Ambiguous map tool state"
    row, snapshot, _ = matches[0]
    return snapshot, {"id": row["id"], "sha256": row["content_sha256"]}, history


async def replay(data, directory, *, transport=None):
    snapshot, snapshot_info, history = load_snapshot(data)
    observation = copy.deepcopy(data["observation"])
    reference = observation.pop("map")
    observation["mapVariant"] = reference["variant"]
    assert {k: v for k, v in observation.items() if k != "mapVariant"} == {
        k: v for k, v in data["observation"].items() if k != "map"
    }
    prefix = data["inputs"][-1]["content"].split("\n\n", 1)[0] + "\n\n"
    current_input = prefix + json.dumps(observation, separators=(",", ":"))
    inputs = copy.deepcopy(data["inputs"])
    inputs[-1]["content"] = current_input
    assert inputs[:-1] == data["inputs"][:-1]
    settings = Settings()
    historical = data["provenance"]["harness"]
    assert settings.model_api_key
    assert settings.model_base_url.rstrip("/") == data["provenance"]["models"]["baseUrl"].rstrip("/")
    instructions = StrategicHarness.build_instructions(
        data["record"]["system_prompt"], historical_instructions=data["run"]["instructions"],
        map_reference=reference,
    )
    captured, outbound, verified, verification_errors = [], [], [], []
    memory_tools = {tool.name: tool for tool in MEMORY_TOOLS}

    def capture(name):
        async def invoke(context, arguments):
            captured.append({"name": name, "arguments": json.loads(arguments)})
            raise baseline.DecisionCaptured("Captured before gameplay execution")
        return invoke

    tools = [FunctionTool(
        name=t["name"], description=t["description"],
        params_json_schema=copy.deepcopy(t["parameters"]), strict_json_schema=t["strict"],
        on_invoke_tool=(memory_tools[t["name"]].on_invoke_tool
                        if t["name"] in memory_tools else capture(t["name"])),
    ) for t in data["tools"]]
    assert describe_tools(tools) == data["tools"]
    tools.append(check_neighbours)
    expected_tools = describe_tools(tools)

    class HistoricalContextFilter(model_module._SessionContextFilter):
        def __call__(self, history_items, new_items):
            assert history_items == []
            assert new_items == inputs[-1:]
            return copy.deepcopy(inputs)

        def manifest(self):
            result = super().manifest()
            result["replayRestoredHistoricalContext"] = True
            result["historicalInputSha256"] = data["expected"]["inputSha256"]
            return result

    class VerifyingRecorder(model_module._ModelInputRecorder):
        def __call__(self, value):
            result = super().__call__(value)
            if value.agent is self.parent_agent:
                assert value.model_data.input[:len(inputs)] == inputs, "Context changed unexpectedly"
                assert value.model_data.instructions == instructions
                verified.append(True)
            return result

    async def check_wire(request):
        assert request.method == "POST"
        body = json.loads(request.content)
        parent = body["instructions"] == instructions
        assert body["model"] == data["case"]["model"]
        assert body["provider"] == data["routing"]
        if parent:
            assert verified
            assert body["tools"] == expected_tools, (
                "Wire tool definitions changed: "
                + str([t["name"] for t, expected in zip(body["tools"], expected_tools)
                       if t != expected])
            )
            assert body["max_output_tokens"] == historical["maxOutputTokens"]
            for key, historical_key in (("tool_choice", "toolChoice"),
                                        ("parallel_tool_calls", "parallelToolCalls"),
                                        ("store", "store")):
                assert body[key] == historical[historical_key]
            assert body["reasoning"]["effort"] == historical["reasoningEffort"]
        else:
            assert any(tool["name"] == "ask_rules_oracle" for tool in expected_tools)
        assert "seed" not in body and "temperature" not in body
        outbound.append({"scope": "player" if parent else "oracle", "body": body})
        baseline.write_json(directory / f"request-{len(outbound):02d}.json", body)

    async def checked_wire(request):
        try:
            await check_wire(request)
        except Exception as exc:
            verification_errors.append(f"{type(exc).__name__}: {exc}")
            raise

    with tempfile.TemporaryDirectory(prefix="raven-map-replay-") as scratch:
        rulebook = Rulebook.load(settings.resolved_rules_path)
        build_oracle = rulebook.build_oracle_tool
        oracle_schema = next(t for t in data["tools"] if t["name"] == "ask_rules_oracle")

        def historical_oracle_schema(**kwargs):
            tool = build_oracle(**kwargs)
            tool.description = oracle_schema["description"]
            tool.params_json_schema = copy.deepcopy(oracle_schema["parameters"])
            tool.strict_json_schema = oracle_schema["strict"]
            return tool

        rulebook.build_oracle_tool = historical_oracle_schema
        runner = model_module.OpenAIAgentRunner(
            api_key=settings.model_api_key, base_url=settings.model_base_url,
            max_output_tokens=historical["maxOutputTokens"],
            request_timeout_seconds=historical["requestTimeoutSeconds"],
            run_timeout_seconds=historical["runTimeoutSeconds"],
            session_database_path=Path(scratch) / "session.db",
            session_history_items=historical["sessionHistoryItems"],
            provider_routing_by_model={data["case"]["model"]: data["routing"]},
            rulebook=rulebook,
        )
        if transport is not None:
            import httpx
            await runner.client._client.aclose()
            runner.client._client = httpx.AsyncClient(transport=transport)
        runner.client._client.event_hooks["request"].append(checked_wire)
        database = Database(Path(scratch) / "harness.db")
        record = AgentRecord(**data["record"], game_server_url="ws://replay.invalid",
                             auth_token="", game_password="")
        # Restore private memory in an isolated database, without credentials or
        # future decisions. The current entry uses the verified pre-action input.
        values = record.model_dump(mode="json")
        values.update(auth_token="", game_password="")
        columns = [row[1] for row in database.connection.execute("PRAGMA table_info(agents)")]
        database.connection.execute(
            f"INSERT INTO agents ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
            [values[column] for column in columns],
        )
        for row in history:
            if row["id"] == data["run"]["history_id"]:
                row.update(observation_json=json.dumps(observation), action_name=None,
                           action_arguments_json=None)
            database.connection.execute(
                f"INSERT INTO game_state_history ({','.join(row)}) VALUES ({','.join('?' for _ in row)})",
                list(row.values()),
            )
        database.connection.commit()
        harness = StrategicHarness(runner, AgentStore(database))
        client = SimpleNamespace(snapshot=snapshot, recent_events=data["observation"]["recentEvents"],
                                 connection_generation=0)
        context = HarnessRunContext(client=client, user_id=record.user_id)
        cache_material = json.dumps({"model": record.model, "instructions": instructions,
                                     "tools": expected_tools}, sort_keys=True)
        prepared = PreparedTurn(
            observation=observation, tools=tools, instructions=instructions,
            game_tool_names=[t.name for t in tools if t.name not in AUXILIARY],
            prompt_cache_key="raven-" + baseline.digest(cache_material)[:32],
        )
        result, error = None, None
        try:
            with patch.object(model_module, "OBSERVATION_INPUT_PREFIX", prefix), \
                 patch.object(model_module, "_SessionContextFilter", HistoricalContextFilter), \
                 patch.object(model_module, "_ModelInputRecorder", VerifyingRecorder):
                result = await harness.run_turn(record, prepared, context, data["run"]["id"])
        except model_module.ModelRunError as exc:
            result = exc.partial_result
            if not captured:
                error = str(exc)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        finally:
            await harness.shutdown()
            database.close()
    operations = baseline.operations(result.response_items) if result else []
    if verification_errors:
        error = "; ".join(verification_errors)
    gameplay = [op for op in operations if op["name"] not in AUXILIARY]
    if not error and (not gameplay or captured != gameplay):
        error = "No unique captured gameplay decision, or captured dispatch differs"
    report = {
        "case": data["case"]["case"], "model": record.model,
        "house": data["case"]["house"], "round": data["case"]["round"],
        "promptVariant": "full-rules-compact-map-and-neighbours-tool",
        "snapshot": snapshot_info, "snapshotBoardVerified": True,
        "inputVerified": bool(verified), "wireToolsVerified": bool(outbound),
        "error": error, "gameToolsExecuted": False,
        "requestCount": len(outbound), "playerRequestCount": sum(r["scope"] == "player" for r in outbound),
        "mapCalls": [op for op in operations if op["name"] == "check_neighbours"],
        "originalOperations": baseline.operations(json.loads(data["run"]["response_json"])),
        "replayOperations": gameplay, "allOperations": operations,
        "usage": result.usage if result else {}, "rawUsage": result.raw_usage if result else [],
        "responseItems": result.response_items if result else [],
        "replayContextManifest": result.context_manifest if result else None,
    }
    baseline.write_json(directory / "result.json", report)
    return report


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--cases", type=int, nargs="+")
    parser.add_argument("--output", type=Path, default=OUT / "results")
    args = parser.parse_args()
    cases = json.loads((BASE / "test-set.json").read_text())["cases"]
    data = [baseline.load_case(c) for c in cases if not args.cases or c["case"] in args.cases]
    for item in data:
        load_snapshot(item)
    print(f"Verified historical inputs and matching snapshots: {len(data)}/{len(data)}", flush=True)
    if not args.live:
        return
    args.output.mkdir(parents=True, exist_ok=True)
    reports = []
    for item in data:
        directory = args.output / f"case-{item['case']['case']:02d}"
        directory.mkdir(exist_ok=False)
        print(f"Replaying case {item['case']['case']}", flush=True)
        report = await replay(item, directory)
        reports.append(report)
        baseline.write_json(args.output / "summary.json", {"cases": reports})
        print(json.dumps({k: report[k] for k in ("case", "error", "requestCount", "mapCalls", "replayOperations")}), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
