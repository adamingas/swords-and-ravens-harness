"""Replay saved positions with production prepare_turn/run_turn and final JSON actions.

Uses current context policy, prompts, schemas and exploration tools. Captures the
validated game command before network transmission; does not simulate acceptance.
"""

import argparse
import asyncio
import copy
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile

import httpx

from raven_harness.agent_store import AgentStore
from raven_harness.config import Settings
from raven_harness.database import Database
from raven_harness.game.client import OrderSubmission
from raven_harness.game.map_reference import observation_map_reference
from raven_harness.harness.actions import HarnessRunContext, describe_tools
from raven_harness.harness.observation import build_context
from raven_harness.harness.strategic import StrategicHarness
from raven_harness.models.openai_agent import ModelRunError
from raven_harness.models.runner import create_llm_runner
from raven_harness.rulebook import Rulebook
from raven_harness.schemas import AgentRecord, DEFAULT_PROMPT

OUT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "map_replay", OUT.parent / "map-context-2026-09-14" / "replay.py"
)
map_replay = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(map_replay)
baseline = map_replay.baseline


def load_current_game_case(path, run_id):
    with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        run = dict(
            db.execute("SELECT * FROM agent_runs WHERE id=?", (run_id,)).fetchone()
        )
        record = dict(
            db.execute(
                "SELECT id,name,model,system_prompt,game_id,user_id,created_at FROM agents WHERE id=?",
                (run["agent_id"],),
            ).fetchone()
        )
        manifest = json.loads(run["context_json"])
        messages = [
            json.loads(row[0])
            for row in db.execute(
                "SELECT message_data FROM agent_messages WHERE session_id=?",
                ("raven-agent-" + record["id"],),
            )
        ]
    content = next(
        m["content"]
        for m in messages
        if isinstance(m.get("content"), str)
        and baseline.digest(m["content"]) == manifest["currentInputSha256"]
    )
    observation = json.loads(
        content.split("\n\nCurrent observation:\n", 1)[1]
        .split("\n\nCurrent decision:\n", 1)[0]
        .split("\n\nFinal action format for this decision:\n", 1)[0]
    )
    observation["map"] = observation_map_reference(observation)
    provenance = json.loads((path.parent / "manifest.json").read_text())["provenance"]
    case = {
        "case": 100,
        "database": str(path.resolve()),
        "model": record["model"],
        "house": observation["you"]["houseId"],
        "round": observation["game"]["round"],
    }
    return {
        "case": case,
        "record": record,
        "run": run,
        "observation": observation,
        "provenance": provenance,
    }


class CaptureClient:
    def __init__(self, snapshot, events):
        self.snapshot = snapshot
        self.recent_events = events
        self.connection_generation = 0
        self.commands = []

    async def send(self, message, **kwargs):
        self.commands.append(message)
        return None

    async def sync_snapshot(self, **kwargs):
        self.snapshot = copy.deepcopy(self.snapshot)
        self.snapshot["leafStateId"] = "isolated-replay-accepted-action"
        return self.snapshot

    async def submit_orders(self, orders, **kwargs):
        message = {"type": "submit-orders", "orders": orders}
        self.commands.append(message)
        snapshot = await self.sync_snapshot()
        return OrderSubmission(message, {"accepted": True}, snapshot)


def final_answers(items):
    answers = []
    for item in items:
        if item.get("type") == "partial_model_response":
            answers.extend(final_answers(item["output"]))
        elif item.get("type") == "message" and item.get("role") == "assistant":
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    answers.append(content["text"])
    return answers


async def replay(
    data, directory, *, transport=None, previous_error=None, omit_native_format=False
):
    snapshot, snapshot_info, history = map_replay.load_snapshot(data)
    settings = Settings()
    requests = []
    client = CaptureClient(snapshot, data["observation"]["recentEvents"])
    with tempfile.TemporaryDirectory(prefix="raven-structured-replay-") as scratch:
        database = Database(Path(scratch) / "harness.db")
        values = {**data["record"], "system_prompt": DEFAULT_PROMPT}
        record = AgentRecord(
            **values,
            game_server_url="ws://replay.invalid",
            auth_token="",
            game_password="",
        )
        values = record.model_dump(mode="json")
        columns = [
            row[1] for row in database.connection.execute("PRAGMA table_info(agents)")
        ]
        database.connection.execute(
            f"INSERT INTO agents ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
            [values[column] for column in columns],
        )
        # Only past completed decisions are restored. prepare_turn records the
        # current observation itself, with no future action leaking into history.
        for row in history:
            if row["id"] == data["run"]["history_id"]:
                continue
            database.connection.execute(
                f"INSERT INTO game_state_history ({','.join(row)}) VALUES ({','.join('?' for _ in row)})",
                list(row.values()),
            )
        memory = copy.deepcopy(data["observation"].get("strategicMemory", {}))
        revision = memory.pop("revision", 0)
        updated = memory.pop("updatedAt", None)
        if revision and updated:
            database.connection.execute(
                "INSERT INTO strategic_memories VALUES (?,?,?,?)",
                (record.id, json.dumps(memory), revision, updated),
            )
        database.connection.commit()
        store = AgentStore(database)
        runner = create_llm_runner(
            settings,
            rulebook=Rulebook.load(settings.resolved_rules_path),
        )
        if transport is not None:
            await runner.client._client.aclose()
            runner.client._client = httpx.AsyncClient(transport=transport)
        harness = StrategicHarness(runner, store)
        prepared = harness.prepare_turn(
            record,
            build_context(snapshot, record.user_id, client.recent_events),
            previous_error,
        )
        assert prepared.decision is not None
        assert set(t.name for t in prepared.tools) <= map_replay.AUXILIARY
        assert prepared.observation["decisionBriefing"] not in prepared.instructions
        expected_tools = describe_tools(
            [*prepared.tools, prepared.decision.submission_tool()]
        )

        async def record_request(request):
            body = json.loads(request.content)
            if body.get("instructions") == prepared.instructions:
                assert body["tool_choice"] == "required"
                assert "schema" not in body.get("text", {}).get("format", {})
                assert {t["name"] for t in body.get("tools", [])} == {
                    t["name"] for t in expected_tools
                }
                assert body["provider"] == {
                    "ignore": settings.openrouter_blocked_providers
                }
                assert body["session_id"] == f"raven-agent-{record.id}"
                assert body["reasoning"]["effort"] == "high"
                assert any(
                    prepared.observation["decisionBriefing"]
                    in str(item.get("content", ""))
                    for item in body["input"]
                    if item.get("role") == "user"
                )
                if omit_native_format:
                    # Diagnostic only: retain the user-visible schema and production
                    # parsing/validation, but remove provider-side constrained decoding.
                    body.pop("text", None)
                    payload = json.dumps(body).encode()
                    request._content = payload
                    # The installed SDK uses httpx2, while test transports use httpx.
                    # Preserve the request's concrete byte-stream implementation.
                    request.stream = type(request.stream)(payload)
                    request.headers["content-length"] = str(len(payload))
            requests.append(body)
            baseline.write_json(directory / f"request-{len(requests):02d}.json", body)

        runner.client._client.event_hooks["request"].append(record_request)
        baseline.write_json(
            directory / "prepared.json",
            {
                "observation": prepared.observation,
                "instructions": prepared.instructions,
                "tools": expected_tools,
                "outputSchema": prepared.decision.output_schema.json_schema(),
            },
        )
        result, error = None, None
        error_chain = []
        try:
            result = await harness.run_turn(
                record,
                prepared,
                HarnessRunContext(client=client, user_id=record.user_id),
                data["run"]["id"],
            )
        except ModelRunError as exc:
            result = exc.partial_result
            if not client.commands:
                error = str(exc)
                cause = exc
                while cause is not None:
                    error_chain.append(
                        {"type": type(cause).__name__, "message": str(cause)}
                    )
                    cause = cause.__cause__ or cause.__context__
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        finally:
            await harness.shutdown()
            database.close()
    answers = final_answers(result.response_items) if result else []
    if not error and len(client.commands) != 1:
        error = f"Expected one captured command, got {len(client.commands)}"
    report = {
        "case": data["case"]["case"],
        "model": record.model,
        "house": data["case"]["house"],
        "round": data["case"]["round"],
        "variant": "required-tools-with-submit-action",
        "snapshot": snapshot_info,
        "snapshotBoardVerified": True,
        "error": error,
        "serverActionsExecuted": False,
        "errorChain": error_chain,
        "previousAttemptError": previous_error,
        "nativeResponseFormatOmitted": omit_native_format,
        "commands": client.commands,
        "finalAnswers": answers,
        "requestCount": len(requests),
        "toolCalls": baseline.operations(result.response_items) if result else [],
        "explorationCalls": [
            call
            for call in (baseline.operations(result.response_items) if result else [])
            if call["name"] != "submit_action"
        ],
        "submissionCalls": [
            call
            for call in (baseline.operations(result.response_items) if result else [])
            if call["name"] == "submit_action"
        ],
        "usage": result.usage if result else {},
        "rawUsage": result.raw_usage if result else [],
        "responseItems": result.response_items if result else [],
        "contextManifest": result.context_manifest if result else None,
    }
    baseline.write_json(directory / "result.json", report)
    return report


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--cases", type=int, nargs="+")
    parser.add_argument(
        "--model", help="Diagnostic model override for the same saved position"
    )
    parser.add_argument("--game-database", type=Path)
    parser.add_argument("--game-run")
    parser.add_argument(
        "--retry-from",
        type=Path,
        help="Retry an unsuccessful run using its recorded error; never reroll an accepted decision",
    )
    parser.add_argument(
        "--omit-native-format",
        action="store_true",
        help="Diagnostic: omit provider-side output constraints; keep production final-answer validation",
    )
    parser.add_argument("--concurrency", type=int, default=3)
    parser.add_argument("--output", type=Path, default=OUT / "results-v1")
    args = parser.parse_args()
    cases = json.loads((baseline.OUT / "test-set.json").read_text())["cases"]
    data = [
        baseline.load_case(c)
        for c in cases
        if not args.cases or c["case"] in args.cases
    ]
    if args.game_database:
        data = [load_current_game_case(args.game_database, args.game_run)]
    previous_error = None
    if args.retry_from:
        failed = json.loads(args.retry_from.read_text())
        assert len(data) == 1 and data[0]["case"]["case"] == failed["case"]
        assert failed["error"] and not failed["commands"]
        previous_error = failed["error"]
    if args.model:
        for item in data:
            item["record"]["model"] = args.model
    for item in data:
        map_replay.load_snapshot(item)
    print(f"Verified {len(data)} historical positions", flush=True)
    if not args.live:
        return
    args.output.mkdir(parents=True, exist_ok=True)
    reports = []
    limit = asyncio.Semaphore(args.concurrency)

    async def run_item(item):
        async with limit:
            directory = args.output / f"case-{item['case']['case']:02d}"
            directory.mkdir(exist_ok=False)
            print(f"Replaying case {item['case']['case']}", flush=True)
            report = await replay(
                item,
                directory,
                previous_error=previous_error,
                omit_native_format=args.omit_native_format,
            )
            reports.append(report)
            baseline.write_json(
                args.output / "summary.json",
                {"cases": sorted(reports, key=lambda r: r["case"])},
            )
            print(
                json.dumps(
                    {
                        k: report[k]
                        for k in ("case", "error", "commands", "requestCount")
                    }
                ),
                flush=True,
            )

    await asyncio.gather(*(run_item(item) for item in data))


if __name__ == "__main__":
    asyncio.run(main())
