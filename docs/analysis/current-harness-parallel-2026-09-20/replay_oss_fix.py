"""Verify one OSS decision from an isolated copy of the failed live game."""

import argparse
import asyncio
import json
from pathlib import Path
import shutil
import sqlite3

from raven_harness.agent_store import AgentStore
from raven_harness.config import Settings
from raven_harness.database import Database
from raven_harness.errors import safe_error_text
from raven_harness.evaluation import (
    _now, _runtime_fingerprint, _start_game_server, _stop_process,
    _wait_for_server, _write_json,
)
from raven_harness.harness.actions import available_tools
from raven_harness.harness.decision import build_decision_contract
from raven_harness.harness.observation import build_context, build_observation
from raven_harness.harness.strategic import StrategicHarness
from raven_harness.manager import AgentManager
from raven_harness.rulebook import Rulebook

from run_game import CerebrasOnlyRunner


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--game-port", type=int, default=5193)
    args = parser.parse_args()
    args.source = args.source.resolve()
    args.output = args.output.resolve()
    source_manifest = json.loads((args.source / "manifest.json").read_text())
    assert source_manifest["status"] == "failed", "Only replay a stopped source game"
    args.output.mkdir(parents=True, exist_ok=False)
    shutil.copy2(args.source / "game.json", args.output / "game.json")
    with sqlite3.connect((args.source / "harness.db").as_uri() + "?mode=ro&immutable=1", uri=True) as source:
        with sqlite3.connect(args.output / "harness.db") as target:
            source.backup(target)
            target.execute("UPDATE agents SET game_server_url=?", (f"ws://127.0.0.1:{args.game_port}",))
    settings = Settings()
    runner = CerebrasOnlyRunner(
        api_key=settings.openrouter_token,
        base_url=settings.openrouter_base_url,
        provider_blocklist=settings.openrouter_blocked_providers,
        rulebook=Rulebook.load_optional(settings.resolved_rules_path),
    )
    requests = []

    async def capture_request(request):
        if request.method != "POST" or not request.url.path.endswith("/responses"):
            return
        body = json.loads(request.content)
        requests.append({
            "model": body.get("model"), "provider": body.get("provider"),
            "reasoning": body.get("reasoning"),
            "maxOutputTokens": body.get("max_output_tokens"),
            "submitAction": next((tool for tool in body.get("tools", []) if tool.get("name") == "submit_action"), None),
        })

    runner.client._client.event_hooks["request"].append(capture_request)
    database = Database(args.output / "harness.db")
    store = AgentStore(database)
    manager = AgentManager(
        store=store, harness=StrategicHarness(runner, store),
        durable_game_path=args.output / "game.json",
    )
    report = {
        "status": "running", "startedAt": _now(),
        "source": str(args.source), "runtimeSha256": _runtime_fingerprint(),
        "sourceRuntimeSha256": source_manifest["provenance"]["harness"]["runtimeSha256"],
        "scope": "One required decision, same saved board and private memory; original artifacts unchanged",
    }
    _write_json(args.output / "replay.json", report)
    process = None
    with (args.output / "game-server.log").open("wb") as log:
        try:
            process = await _start_game_server(
                game_path=args.output / "game.json", port=args.game_port,
                max_rounds=None, random_seed=102, log=log,
            )
            await _wait_for_server(process, args.game_port, timeout=20)
            for record in store.list_agents():
                await manager.start(record.id)
            record = next(record for record in store.list_agents() if record.user_id == "1")
            session = manager.sessions[record.id]
            context = build_context(session.client.snapshot, record.user_id, list(session.client.recent_events))
            contract = build_decision_contract(context, available_tools(context))
            assert contract is not None
            before = build_observation(context)
            schema = contract.submission_tool().params_json_schema
            _write_json(args.output / "observation-before.json", before)
            _write_json(args.output / "submit-action-schema.json", schema)
            assert before["game"]["round"] == 3
            assert before["you"]["houseId"] == "baratheon"
            try:
                contract.output_schema.validate_json(json.dumps({
                    "moves": [{"destination_region_id": "storms-end", "unit_ids": [9, 10]}],
                    "strategic_handoff": "Replay the formerly accepted invalid destination.",
                }))
            except ValueError:
                report["oldInvalidActionRejectedBySchema"] = True
            else:
                raise AssertionError("Blocked destination remains in the schema")
            print(json.dumps({"status": "replaying", "oldInvalidActionRejectedBySchema": True}), flush=True)
            report["attempts"] = []
            for _ in range(settings.autoplay_max_consecutive_failures):
                try:
                    result = await manager.run_once(record.id)
                except Exception as error:
                    report["attempts"].append({"error": safe_error_text(error)})
                    continue
                report["attempts"].append(result)
                report["status"] = "accepted"
                report["runId"] = result["runId"]
                report["result"] = result
                _write_json(args.output / "model-trace.json", store.get_run(record.id, result["runId"]))
                break
            else:
                report["status"] = "failed"
            _write_json(args.output / "observation-after.json", manager.get_observation(record.id))
            parent_requests = [request for request in requests if request["submitAction"]]
            assert parent_requests
            assert all(request["submitAction"]["parameters"] == schema for request in parent_requests)
            report["wireSchemaMatchesContract"] = True
            report["requests"] = requests
        except BaseException as error:
            report.update(status="failed", error=safe_error_text(error))
            raise
        finally:
            await manager.stop_all()
            manager.telemetry.shutdown()
            database.close()
            if process:
                await _stop_process(process)
            report["finishedAt"] = _now()
            _write_json(args.output / "replay.json", report)
    print(json.dumps({key: report.get(key) for key in ("status", "runId", "wireSchemaMatchesContract")}), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
