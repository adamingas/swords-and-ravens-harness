"""Replay the first model request through StrategicHarness/OpenAIAgentRunner.

Default: validate stored inputs without network access. --live makes one request
per case and asserts equality of tool names and parsed arguments. Tool dispatch
is intercepted: this tests model decisions, not game-server acceptance. A failed
decision assertion is NOT by itself evidence of faulty storage or harness code.
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import importlib.metadata
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
from raven_harness.harness.strategic import StrategicHarness
from raven_harness.models import openai_agent as model_module
from raven_harness.schemas import AgentRecord

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def canonical(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def operations(items):
    result = []
    for item in items:
        if item.get("type") == "function_call":
            result.append({"name": item["name"], "arguments": json.loads(item["arguments"])})
        elif item.get("type") == "partial_model_response":
            result.extend(operations(item["output"]))
    return result


def load_case(case):
    path = ROOT / case["database"]
    wal = Path(str(path) + "-wal")
    assert not wal.exists() or not wal.stat().st_size, "Nonempty source WAL"
    with sqlite3.connect(path.resolve().as_uri() + "?mode=ro&immutable=1", uri=True) as db:
        db.row_factory = sqlite3.Row
        run = dict(db.execute("SELECT * FROM agent_runs WHERE id=?", (case["run_id"],)).fetchone())
        # Credentials are unnecessary for request-only replay; never read them.
        record = dict(db.execute(
            "SELECT id,name,model,system_prompt,game_id,user_id,created_at FROM agents WHERE id=?",
            (run["agent_id"],),
        ).fetchone())
        row = db.execute("SELECT session_id,message_data FROM agent_messages WHERE id=?", (case["sdk_message_id"],)).fetchone()
        assert row["session_id"] == "raven-agent-" + record["id"]
        message = json.loads(row["message_data"])
    manifest = json.loads(run["context_json"])
    assert len(manifest["modelRequestInputs"]) == 1, "Selection must have one original request"
    expected = manifest["modelRequestInputs"][0]
    assert digest(message["content"]) == manifest["currentInputSha256"] == case["original_input_sha256"]
    assert digest(run["instructions"]) == expected["instructionsSha256"] == case["original_instructions_sha256"]
    inputs = manifest["selectedHistoryItems"] + [message]
    assert digest(canonical(inputs)) == expected["inputSha256"]
    assert len(inputs) == expected["inputItemCount"]
    assert len(canonical(inputs)) == expected["inputCharacters"]
    evaluation_manifest = json.loads((path.parents[2] / "manifest.json").read_text())
    attempt_directory = str(path.parent.relative_to(path.parents[2]))
    attempt = next(a for g in evaluation_manifest["games"] for a in g["attempts"] if a["directory"] == attempt_directory)
    provenance = attempt.get("provenance") or evaluation_manifest["provenance"]
    observation = json.loads(message["content"].split("\n\n", 1)[1])
    models = provenance["models"]
    routing = models.get("retryProviderRoutingByModel" if observation.get("previousAttemptError") else "primaryProviderRoutingByModel", {}).get(case["model"], models.get("providerRouting"))
    assert routing, "Missing historical provider routing"
    assert record["model"] == run["model"] == case["model"]
    return dict(case=case, record=record, run=run, manifest=manifest, inputs=inputs,
                observation=observation, tools=json.loads(run["tools_json"]),
                provenance=provenance, routing=routing, expected=expected)


class DecisionCaptured(RuntimeError):
    """Stop before invoking a tool or making another model request."""


async def replay(data, directory, *, transport=None, full_rules=False):
    case, run = data["case"], data["run"]
    settings = Settings()
    assert settings.model_api_key, "Model API key not configured"
    assert settings.model_base_url.rstrip("/") == data["provenance"]["models"]["baseUrl"].rstrip("/")
    historical = data["provenance"]["harness"]
    instructions = run["instructions"]
    expected_request = copy.deepcopy(data["expected"])
    captured = []
    outbound = []
    input_checks = []

    def capture(name):
        async def invoke(context, arguments):
            captured.append({"name": name, "arguments": json.loads(arguments)})
            raise DecisionCaptured("Replay captured tool invocation before execution")
        return invoke

    tools = [FunctionTool(name=t["name"], description=t["description"],
                          params_json_schema=copy.deepcopy(t["parameters"]),
                          strict_json_schema=t["strict"], on_invoke_tool=capture(t["name"]))
             for t in data["tools"]]
    assert describe_tools(tools) == data["tools"]

    class HistoricalContextFilter(model_module._SessionContextFilter):
        def __call__(self, history_items, new_items):
            assert history_items == [], "Replay session must be isolated"
            assert new_items == data["inputs"][-1:]
            return copy.deepcopy(data["inputs"])

        def manifest(self):
            restored = copy.deepcopy(data["manifest"])
            restored["modelRequestInputs"] = copy.deepcopy(self.model_request_inputs)
            restored["replayRestoredHistoricalContext"] = True
            return restored

    class VerifyingRecorder(model_module._ModelInputRecorder):
        def __call__(self, value):
            result = super().__call__(value)
            assert len(self.request_inputs) == 1, "Stop after first historical request"
            assert self.request_inputs[0] == expected_request, "SDK input/instructions mismatch"
            input_checks.append(True)
            return result

    async def check_wire(request):
        if request.method != "POST":
            raise AssertionError("Unexpected replay HTTP request")
        body = json.loads(request.content)
        assert input_checks == [True]
        assert not outbound, "One provider request per case"
        assert body["tools"] == data["tools"], "Wire tool definitions differ"
        assert body["instructions"] == instructions
        assert body["model"] == case["model"]
        assert body["provider"] == data["routing"]
        assert body["max_output_tokens"] == historical["maxOutputTokens"]
        assert body["reasoning"]["effort"] == historical["reasoningEffort"]
        assert body["tool_choice"] == historical["toolChoice"]
        assert body["parallel_tool_calls"] == historical["parallelToolCalls"]
        assert body["store"] == historical["store"]
        assert "seed" not in body and "temperature" not in body
        outbound.append(body)
        # Save body only. HTTP authentication headers must never be persisted.
        write_json(directory / "request.json", body)

    with tempfile.TemporaryDirectory(prefix="raven-replay-") as scratch:
        runner = model_module.OpenAIAgentRunner(
            api_key=settings.model_api_key, base_url=settings.model_base_url,
            max_output_tokens=historical["maxOutputTokens"],
            request_timeout_seconds=historical["requestTimeoutSeconds"],
            run_timeout_seconds=historical["runTimeoutSeconds"],
            session_database_path=Path(scratch) / "session.db",
            session_history_items=historical["sessionHistoryItems"],
            provider_routing_by_model={case["model"]: data["routing"]},
        )
        if transport is not None:
            import httpx
            await runner.client._client.aclose()
            runner.client._client = httpx.AsyncClient(transport=transport)
        runner.client._client.event_hooks["request"].append(check_wire)
        database = Database(Path(scratch) / "harness.db")
        harness = StrategicHarness(runner, AgentStore(database))
        if full_rules:
            instructions = harness.build_instructions(
                data["record"]["system_prompt"], historical_instructions=run["instructions"],
            )
            assert instructions.startswith(run["instructions"].rstrip() + "\n\n# Rules\n")
            expected_request["instructionsCharacters"] = len(instructions)
            expected_request["instructionsSha256"] = digest(instructions)
        record = AgentRecord(**data["record"], game_server_url="ws://replay.invalid",
                             auth_token="", game_password="")
        context = HarnessRunContext(client=SimpleNamespace(connection_generation=0), user_id=record.user_id)
        cache_material = json.dumps({"model": record.model, "instructions": instructions, "tools": data["tools"]}, sort_keys=True)
        prepared = PreparedTurn(observation=data["observation"], tools=tools,
                                instructions=instructions,
                                game_tool_names=[t["name"] for t in data["tools"] if t["name"] not in {"recall_game_state", "remember_strategy", "ask_rules_oracle"}],
                                prompt_cache_key="raven-" + digest(cache_material)[:32])
        prefix = data["inputs"][-1]["content"].split("\n\n", 1)[0] + "\n\n"
        error = None
        result = None
        try:
            with patch.object(model_module, "OBSERVATION_INPUT_PREFIX", prefix), \
                 patch.object(model_module, "_SessionContextFilter", HistoricalContextFilter), \
                 patch.object(model_module, "_ModelInputRecorder", VerifyingRecorder):
                result = await harness.run_turn(record, prepared, context, run["id"])
        except model_module.ModelRunError as exc:
            result = exc.partial_result
            if not captured:
                error = str(exc)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        finally:
            await harness.shutdown()
            database.connection.close()
    old = operations(json.loads(run["response_json"]))
    new = operations(result.response_items) if result else []
    assertion = None
    if error is None:
        try:
            assert new == old, "Tool name/parsed arguments differ from historical decision"
            assert captured == new, "Captured dispatch differs from recorded model response"
        except AssertionError as exc:
            assertion = str(exc)
    report = {
        "promptVariant": "full-rules" if full_rules else "historical",
        "instructionsSha256": digest(instructions),
        "instructionsCharacters": len(instructions),
        "case": case["case"], "model": case["model"], "house": case["house"],
        "round": case["round"], "inputHashVerified": bool(input_checks),
        "wireToolsVerified": bool(outbound),
        "status": "error" if error else "different" if assertion else "same",
        "assertionFailure": assertion, "error": error,
        "originalOperations": old, "replayOperations": new,
        "historicalAcceptedAction": {"name": case["accepted_action"], "arguments": case["accepted_arguments"]},
        "gameToolsExecuted": False,
        "usage": result.usage if result else {},
        "rawUsage": result.raw_usage if result else [],
        "responseItems": result.response_items if result else [],
        "historicalRequestHash": data["expected"]["inputSha256"],
        "replayContextManifest": result.context_manifest if result else None,
    }
    write_json(directory / "result.json", report)
    return report


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--cases", type=int, nargs="+")
    parser.add_argument("--manifest", type=Path, default=OUT / "cases.json")
    parser.add_argument("--full-rules", action="store_true", help="Append the rules using the production harness prompt builder")
    parser.add_argument("--output", type=Path, default=OUT / "results")
    args = parser.parse_args()
    selected = [c for c in json.loads(args.manifest.read_text())["cases"] if not args.cases or c["case"] in args.cases]
    data = [load_case(c) for c in selected]
    print(f"Verified historical observation, full SDK input and instructions: {len(data)}/{len(data)}", flush=True)
    if not args.live:
        return
    args.output.mkdir(parents=True, exist_ok=True)
    reports = []
    for item in data:
        directory = args.output / f"case-{item['case']['case']:02d}"
        directory.mkdir(exist_ok=False)
        print(f"Replaying case {item['case']['case']} through StrategicHarness", flush=True)
        result = await replay(item, directory, full_rules=args.full_rules)
        reports.append(result)
        write_json(args.output / "summary.json", {
            "sdkVersions": {p: importlib.metadata.version(p) for p in ["openai", "openai-agents"]},
            "method": "Historical SDK input and tool definitions; current harness/SDK; stop before tool execution",
            "promptVariant": "full-rules" if args.full_rules else "historical",
            "limitations": ["Original HTTP bodies were not stored; request settings restored from attempt provenance.",
                            "Historical runs did not pin seed or temperature; provider/model defaults can change.",
                            "Different model choices do not establish a storage/harness defect.",
                            "Game server acceptance and tool normalization are not exercised."],
            "cases": [{k: v for k, v in r.items() if k not in {"responseItems", "replayContextManifest"}} for r in reports],
        })
        print(f"Case {result['case']}: {result['status']}" + (f" ({result['error']})" if result['error'] else ""), flush=True)
    if args.full_rules:
        assert all(r["status"] != "error" for r in reports), "One or more model requests failed; see summary.json"
    else:
        assert all(r["status"] == "same" for r in reports), "One or more replays differed or failed; see results/summary.json"


if __name__ == "__main__":
    asyncio.run(main())
