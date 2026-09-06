import copy
import json
from typing import Any

import pytest
from agents import ModelResponse, Usage
from agents.models.interface import Model
from openai.types.responses import ResponseFunctionToolCall

from raven_harness.agent_store import AgentStore
from raven_harness.database import Database
from raven_harness.harness.actions import HarnessRunContext
from raven_harness.harness.interface import PlayerHarness
from raven_harness.harness.observation import build_context
from raven_harness.harness.strategic import StrategicHarness
from raven_harness.models.openai_agent import OpenAIAgentRunner
from raven_harness.schemas import AgentCreate

from conftest import lobby_snapshot, planning_snapshot


class FakeClient:
    def __init__(self, snapshot: dict[str, Any]) -> None:
        self.snapshot = snapshot
        self.recent_events: list[dict[str, Any]] = []
        self.sent: list[dict[str, Any]] = []

    async def send(self, message: dict[str, Any], *, require_auth: bool = True) -> None:
        self.sent.append(message)

    async def sync_snapshot(self, timeout: float = 10) -> dict[str, Any]:
        del timeout
        message = self.sent[-1]
        if message["type"] == "choose-house":
            self.snapshot["childGameState"]["players"].append(
                [message["house"], "2"]
            )
        return self.snapshot


class HarnessStubRunner:
    rules_oracle_available = False


class RecallThenActionModel(Model):
    def __init__(self) -> None:
        self.calls = 0

    async def get_response(self, *args, **kwargs) -> ModelResponse:
        self.calls += 1
        if self.calls == 1:
            output = ResponseFunctionToolCall(
                arguments='{"turns_ago":1}',
                call_id="recall-1",
                name="recall_game_state",
                type="function_call",
            )
        else:
            output = ResponseFunctionToolCall(
                arguments='{"house_id":"stark"}',
                call_id="action-after-recall",
                name="choose_house",
                type="function_call",
            )
        return ModelResponse(
            output=[output],
            usage=Usage(requests=1, input_tokens=30, output_tokens=10, total_tokens=40),
            response_id=f"recall-resp-{self.calls}",
        )

    async def stream_response(self, *args, **kwargs):
        if False:
            yield None


def test_strategic_harness_implements_interface_and_prepares_memory(tmp_path) -> None:
    database = Database(tmp_path / "strategic.db")
    store = AgentStore(database)
    record = store.create_agent(
        AgentCreate(
            name="Wolf",
            model="test-model",
            user_id="2",
            auth_token="secret",
        )
    )
    harness = StrategicHarness(
        runner=HarnessStubRunner(),  # type: ignore[arg-type]
        store=store,
    )
    assert isinstance(harness, PlayerHarness)

    context = build_context(planning_snapshot(), "2")
    prepared = harness.prepare_turn(record, context, previous_error=None)
    names = [tool.name for tool in prepared.tools]
    assert "submit_orders" in names
    assert "recall_game_state" in names
    assert "update_strategic_memory" not in names
    assert prepared.metadata["promptCacheKey"].startswith("raven-")
    assert prepared.observation["strategicMemory"]["revision"] == 0
    assert prepared.observation["strategicMemory"]["roundNumber"] is None
    assert prepared.observation["strategicOverview"]["round"] == 1
    submit_schema = next(
        tool.params_json_schema for tool in prepared.tools if tool.name == "submit_orders"
    )
    assignment = submit_schema["$defs"]["OrderAssignment"]["properties"]
    assert assignment["region_id"]["enum"] == ["winterfell", "white-harbor"]
    assert store.recall_state(record.id, 0)["stateId"] == "leaf-2"  # type: ignore[index]

    later_snapshot = copy.deepcopy(planning_snapshot())
    later_snapshot["leafStateId"] = "leaf-later"
    later_snapshot["childGameState"]["game"]["turn"] = 2
    later = harness.prepare_turn(
        record, build_context(later_snapshot, "2"), previous_error=None
    )
    assert later.metadata["promptCacheKey"] == prepared.metadata["promptCacheKey"]
    submit_orders = next(tool for tool in later.tools if tool.name == "submit_orders")
    assert "winterfell" not in submit_orders.description.lower()
    assert later.metadata["gameToolNames"] == ["submit_orders"]
    database.close()


@pytest.mark.asyncio
async def test_strategic_harness_recalls_exact_prior_state_then_acts(
    monkeypatch, tmp_path
) -> None:
    fake_model = RecallThenActionModel()
    monkeypatch.setattr(
        "raven_harness.models.openai_agent.OpenAIResponsesModel",
        lambda **_kwargs: fake_model,
    )
    database_path = tmp_path / "recall.db"
    database = Database(database_path)
    store = AgentStore(database)
    record = store.create_agent(
        AgentCreate(
            name="Wolf",
            model="test-model",
            user_id="2",
            auth_token="secret",
        )
    )
    store.record_state(
        record.id,
        {"game": {"stateId": "prior-state", "round": 2, "phase": "march"}},
    )
    client = FakeClient(lobby_snapshot())
    game_context = build_context(client.snapshot, "2")
    harness = StrategicHarness(
        OpenAIAgentRunner(api_key="test-key", base_url="https://api.test/v1"),
        store,
    )
    prepared = harness.prepare_turn(record, game_context, previous_error=None)
    run_context = HarnessRunContext(client=client, user_id="2", game_password="wolf")

    result = await harness.run_turn(record, prepared, run_context, "run-with-recall")

    assert fake_model.calls == 2
    assert run_context.action_taken is not None
    assert run_context.action_taken.name == "choose_house"
    conversation = result.response_items
    recall_output = next(
        item["output"]
        for item in conversation
        if item.get("call_id") == "recall-1"
        and item.get("type") == "function_call_output"
    )
    recalled = json.loads(recall_output)
    assert recalled["found"] is True
    assert recalled["stateId"] == "prior-state"
    assert recalled["observation"]["game"]["round"] == 2
    automatic_memory = store.get_strategic_memory(record.id)
    assert automatic_memory["roundNumber"] == 0
    assert "used choose_house" in automatic_memory["commitments"][-1]
    await harness.shutdown()
    database.close()
