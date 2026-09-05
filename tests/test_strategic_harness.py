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


class MemoryThenActionModel(Model):
    def __init__(self) -> None:
        self.calls = 0

    async def get_response(self, *args, **kwargs) -> ModelResponse:
        self.calls += 1
        if self.calls == 1:
            output = ResponseFunctionToolCall(
                arguments=(
                    '{"notes":{"roundNumber":0,'
                    '"situationAssessment":"Take the North",'
                    '"objectives":["Hold Winterfell"],"opponentModels":[],'
                    '"commitments":[],"lessons":[]}}'
                ),
                call_id="memory-1",
                name="update_strategic_memory",
                type="function_call",
            )
        else:
            output = ResponseFunctionToolCall(
                arguments='{"house_id":"stark"}',
                call_id="action-1",
                name="choose_house",
                type="function_call",
            )
        return ModelResponse(
            output=[output],
            usage=Usage(requests=1, input_tokens=30, output_tokens=10, total_tokens=40),
            response_id=f"resp-{self.calls}",
        )

    async def stream_response(self, *args, **kwargs):
        if False:
            yield None


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
            harness_id="strategic-v1",
            user_id="2",
            auth_token="secret",
        )
    )
    harness = StrategicHarness(
        runner=object(),  # type: ignore[arg-type]
        store=store,
        database_path=str(tmp_path / "strategic.db"),
    )
    assert isinstance(harness, PlayerHarness)

    context = build_context(planning_snapshot(), "2")
    prepared = harness.prepare_turn(record, context, previous_error=None)
    names = [tool.name for tool in prepared.tools]
    assert "submit_orders" in names
    assert "recall_game_state" in names
    assert "update_strategic_memory" in names
    assert prepared.metadata["promptCacheKey"].startswith("raven-")
    assert prepared.observation["strategicMemory"]["revision"] == 0
    assert prepared.observation["strategicMemory"]["roundNumber"] is None
    assert prepared.observation["strategicOverview"]["round"] == 1
    assert prepared.observation["availableGameTools"] == ["submit_orders"]
    assert prepared.observation["legalActions"] == [
        {
            "name": "submit_orders",
            "legalValues": {
                "region_ids": ["winterfell", "white-harbor"],
                "max_starred": 0,
                "restricted_orders": [],
            },
        }
    ]
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
    assert later.observation["legalActions"][0]["legalValues"]["region_ids"] == [
        "winterfell",
        "white-harbor",
    ]
    database.close()


@pytest.mark.asyncio
async def test_strategic_harness_keeps_memory_call_and_game_action_in_one_run(
    monkeypatch, tmp_path
) -> None:
    fake_model = MemoryThenActionModel()
    monkeypatch.setattr(
        "raven_harness.models.openai_agent.OpenAIResponsesModel",
        lambda **_kwargs: fake_model,
    )
    database_path = tmp_path / "strategic.db"
    database = Database(database_path)
    store = AgentStore(database)
    record = store.create_agent(
        AgentCreate(
            name="Wolf",
            model="test-model",
            harness_id="strategic-v1",
            user_id="2",
            auth_token="secret",
        )
    )
    client = FakeClient(lobby_snapshot())
    game_context = build_context(client.snapshot, "2")
    harness = StrategicHarness(
        OpenAIAgentRunner(api_key="test-key", base_url="https://api.test/v1"),
        store,
        str(database_path),
    )
    prepared = harness.prepare_turn(record, game_context, previous_error=None)
    run_context = HarnessRunContext(client=client, user_id="2", game_password="wolf")

    result = await harness.run_turn(record, prepared, run_context, "run-1")

    assert fake_model.calls == 2
    assert result.usage["totalTokens"] == 80
    assert run_context.action_taken is not None
    assert run_context.action_taken.name == "choose_house"
    assert store.get_strategic_memory(record.id)["objectives"] == ["Hold Winterfell"]
    conversation = store.list_conversation_items(record.id)
    assert any(
        item["item"].get("name") == "update_strategic_memory" for item in conversation
    )
    assert any(item["item"].get("name") == "choose_house" for item in conversation)
    await harness.shutdown()
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
            harness_id="strategic-v1",
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
        str(database_path),
    )
    prepared = harness.prepare_turn(record, game_context, previous_error=None)
    run_context = HarnessRunContext(client=client, user_id="2", game_password="wolf")

    await harness.run_turn(record, prepared, run_context, "run-with-recall")

    assert fake_model.calls == 2
    assert run_context.action_taken is not None
    assert run_context.action_taken.name == "choose_house"
    conversation = store.list_conversation_items(record.id)
    recall_output = next(
        item["item"]["output"]
        for item in conversation
        if item["item"].get("call_id") == "recall-1"
        and item["item"].get("type") == "function_call_output"
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
