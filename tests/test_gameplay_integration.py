import asyncio
import json

import httpx
import pytest

from raven_harness.agent_store import AgentStore
from raven_harness.database import Database
from raven_harness.harness.actions import HarnessRunContext
from raven_harness.harness.observation import build_context
from raven_harness.models.results import (
    ModelRunCancelled,
    ModelRunError,
    PermanentModelError,
    TransientProviderCapacityError,
)
from raven_harness.schemas import AgentCreate

from conftest import make_harness
from test_decision import Client, action, selection_snapshot


@pytest.mark.parametrize("mode", ["structured", "two-stage"])
@pytest.mark.parametrize(
    "outcome",
    ["invalid", "stale", "cancelled", "failed", "capacity", "quota"],
)
async def test_canonical_pipeline_preserves_features_across_modes(
    tmp_path, mode, outcome
):
    router = mode == "two-stage"
    database = Database(tmp_path / "game.db")
    store = AgentStore(database)
    record = store.create_agent(
        AgentCreate(name="Stark", model="test-model", user_id="2", auth_token="unused")
    )
    client = Client(selection_snapshot())
    harness = make_harness(
        store,
        mode=mode,
        max_output_tokens=40960,
        provider_blocklist=["Together", "novita", "Together"] if router else None,
    )
    activities = []
    context = HarnessRunContext(
        client=client,
        user_id="2",
        activity_sink=lambda kind, data: activities.append((kind, data)),
    )
    prepared = harness.prepare_turn(record, build_context(client.snapshot, "2"), None)
    requests = []
    final_request = 3 if mode == "two-stage" else 2

    def respond(request):
        body = json.loads(request.content)
        requests.append(body)
        number = len(requests)
        assert number <= final_request
        assert body["max_output_tokens"] == 40960
        assert body["reasoning"]["effort"] == "high"
        assert body["prompt_cache_key"] == prepared.prompt_cache_key
        assert body["instructions"] == prepared.instructions
        assert "submit_action" not in json.dumps(body)
        if router:
            assert body["provider"]["ignore"] == ["together", "novita"]
            assert body["session_id"] == f"raven-agent-{record.id}"
        else:
            assert "provider" not in body and "session_id" not in body
        final_stage = mode == "two-stage" and number == final_request
        names = {tool["name"] for tool in body.get("tools", [])}
        assert names == (
            set() if final_stage else {tool.name for tool in prepared.tools}
        )
        output_format = body.get("text", {}).get("format", {})
        if mode == "structured" or final_stage:
            assert output_format["type"] == "json_schema"
            assert (
                output_format["schema"] == prepared.decision.output_schema.json_schema()
            )
        else:
            assert output_format.get("type") != "json_schema"
        if final_stage:
            assert "tool_choice" not in body and "parallel_tool_calls" not in body
        assert client.sent == []
        if number > 1:
            result = next(
                i for i in body["input"] if i.get("type") == "function_call_output"
            )
            assert "castle-black" in {
                area["id"] for area in json.loads(result["output"])
            }
        if number == final_request:
            if outcome == "cancelled":
                raise asyncio.CancelledError
            if outcome in {"capacity", "quota"}:
                return httpx.Response(
                    503 if outcome == "capacity" else 402,
                    json={
                        "error": {
                            "message": "provider capacity unavailable"
                            if outcome == "capacity"
                            else "spending limit exhausted",
                        }
                    },
                )
            if outcome == "stale":
                client.snapshot["leafStateId"] = "changed-during-thinking"
        if number == 1:
            output = [
                {
                    "type": "function_call",
                    "name": "check_neighbours",
                    "call_id": "map",
                    "arguments": '{"area":"Winterfell"}',
                }
            ]
        else:
            text = "Ready to choose losses."
            if number == final_request:
                text = json.dumps(
                    action(
                        unit_ids_to_destroy=[99, 2] if outcome == "invalid" else [1, 2]
                    )
                )
            output = [
                {
                    "type": "message",
                    "id": f"answer-{number}",
                    "role": "assistant",
                    "status": "completed",
                    "content": [
                        {"type": "output_text", "text": text, "annotations": []}
                    ],
                }
            ]
        failed = outcome == "failed" and number == final_request
        return httpx.Response(
            200,
            headers={"x-request-id": f"request-{number}"},
            json={
                "id": f"response-{number}",
                "object": "response",
                "created_at": 0,
                "status": "failed" if failed else "completed",
                "model": "test-model",
                "provider": "Test Provider",
                "error": {"code": "server_error", "message": "Generation failed"}
                if failed
                else None,
                "output": [] if failed else output,
                "usage": {
                    "input_tokens": 100,
                    "output_tokens": 30,
                    "total_tokens": 130,
                    "cost": 0.001,
                },
            },
        )

    await harness.provider.client._client.aclose()
    harness.provider.client._client = httpx.AsyncClient(
        transport=httpx.MockTransport(respond)
    )
    try:
        error_type = {
            "cancelled": ModelRunCancelled,
            "capacity": TransientProviderCapacityError,
            "quota": PermanentModelError,
        }.get(outcome, ModelRunError)
        with pytest.raises(error_type) as failure:
            await harness.run_turn(record, prepared, context, "run-1")
        result = failure.value.partial_result
        assert client.sent == [] and context.action_taken is None
        assert not store.get_strategic_memory(record.id).get("revision")
        completed = final_request - (outcome in {"cancelled", "capacity", "quota"})
        assert result.usage == {
            "requests": completed,
            "inputTokens": 100 * completed,
            "outputTokens": 30 * completed,
            "totalTokens": 130 * completed,
        }
        assert len(result.raw_usage) == completed
        assert all(item["response_model"] == "test-model" for item in result.raw_usage)
        assert all(
            item["response_provider"] == "Test Provider" for item in result.raw_usage
        )
        assert sum(item["cost"] for item in result.raw_usage) == pytest.approx(
            0.001 * completed
        )
        assert len(result.context_manifest["modelRequestInputs"]) == final_request
        assert (
            result.context_manifest["actionOutputSchema"]
            == prepared.decision.output_schema.json_schema()
        )
        assert len(requests) == final_request
        assert any(kind == "model-tool-completed" for kind, _ in activities)
    finally:
        await harness.shutdown()
        database.close()
