import asyncio
import copy
import json
from typing import Any

import pytest
from agents import ModelResponse, Usage
from agents.models.interface import Model
from agents.tool_context import ToolContext
from openai.types.responses import ResponseFunctionToolCall

from raven_harness.agent_store import AgentStore
from raven_harness.database import Database
from raven_harness.game.client import OrderSubmission
from raven_harness.game.map_reference import load_map_reference
from raven_harness.harness.actions import HarnessRunContext
from raven_harness.harness.observation import build_context
from raven_harness.harness.strategic import StrategicHarness, remember_strategy
from raven_harness.models.openai_agent import ModelRunResult, OpenAIAgentRunner
from raven_harness.schemas import AgentCreate

from conftest import lobby_snapshot, planning_snapshot


def final_answer(value):
    payload = value.get('decision', value)
    payload['strategic_handoff'] = "Continue the current plan next decision."
    return ResponseFunctionToolCall(
        arguments=json.dumps(value),
        call_id="final-action",
        name="submit_action",
        type="function_call",
    )


class FakeClient:
    def __init__(self, snapshot: dict[str, Any]) -> None:
        self.snapshot = snapshot
        self.recent_events: list[dict[str, Any]] = []
        self.sent: list[dict[str, Any]] = []
        self.connection_generation = 1

    async def send(
        self,
        message: dict[str, Any],
        *,
        require_auth: bool = True,
        expected_generation: int | None = None,
    ) -> None:
        del require_auth
        assert expected_generation == self.connection_generation
        self.sent.append(message)

    async def sync_snapshot(
        self,
        timeout: float = 10,
        *,
        expected_generation: int | None = None,
    ) -> dict[str, Any]:
        del timeout
        assert expected_generation == self.connection_generation
        message = self.sent[-1]
        if message["type"] == "choose-house":
            self.snapshot["childGameState"]["players"].append([message["house"], "2"])
        return self.snapshot


class HarnessStubRunner:
    rules_oracle_available = False

    async def run_once(
        self,
        *,
        agent_record,
        observation,
        context,
        tools,
        instructions,
        prompt_cache_key,
        trace_metadata,
    ):
        raise AssertionError("The model should not run in this test")

    async def shutdown(self) -> None:
        pass


class MapThenOrdersModel(Model):
    def __init__(self):
        self.calls = 0

    async def get_response(self, *args, **kwargs):
        self.calls += 1
        assert kwargs["model_settings"].tool_choice == "auto"
        assert kwargs["output_schema"] is None
        assert "submit_orders" not in {tool.name for tool in kwargs["tools"]}
        assert "submit_action" in {tool.name for tool in kwargs["tools"]}
        if self.calls == 1:
            name, arguments = "check_neighbours", {"area": "Castle Black"}
            output = ResponseFunctionToolCall(
                arguments=json.dumps(arguments),
                call_id="map-turn-1",
                name=name,
                type="function_call",
            )
        else:
            assert self.calls == 2
            map_output = next(
                item["output"]
                for item in kwargs["input"]
                if isinstance(item, dict)
                and item.get("type") == "function_call_output"
                and item.get("call_id") == "map-turn-1"
            )
            assert "winterfell" in {area["id"] for area in json.loads(map_output)}
            arguments = {
                "assignments": [
                    {
                        "region_id": region,
                        "preferred_order": "march",
                        "starred_preference": "avoid",
                        "priority": 50,
                    }
                    for region in ("winterfell", "white-harbor")
                ]
            }
            output = final_answer(arguments)
        return ModelResponse(
            output=[output],
            usage=Usage(requests=1, input_tokens=30, output_tokens=10, total_tokens=40),
            response_id=f"map-response-{self.calls}",
        )

    async def stream_response(self, *args, **kwargs):
        raise NotImplementedError
        yield


@pytest.mark.asyncio
async def test_strategic_harness_checks_map_then_submits_orders(monkeypatch, tmp_path):
    model = MapThenOrdersModel()
    monkeypatch.setattr(
        "raven_harness.models.openai_agent._response_model", lambda **_kwargs: model
    )
    database = Database(tmp_path / "map.db")
    store = AgentStore(database)
    record = store.create_agent(
        AgentCreate(name="Wolf", model="test-model", user_id="2", auth_token="secret")
    )
    client = FakeClient(planning_snapshot())

    async def submit_orders(orders, *, expected_generation):
        assert expected_generation == client.connection_generation
        message = {"type": "submit-orders", "orders": orders}
        client.sent.append(message)
        return OrderSubmission(message, {"accepted": True}, client.snapshot)

    monkeypatch.setattr(client, "submit_orders", submit_orders, raising=False)
    harness = StrategicHarness(
        OpenAIAgentRunner(api_key="test-key", base_url="https://api.test/v1"), store
    )
    prepared = harness.prepare_turn(record, build_context(client.snapshot, "2"), None)
    context = HarnessRunContext(client=client, user_id="2")
    try:
        await harness.run_turn(record, prepared, context, "map-test")
        assert model.calls == 2
        assert context.action_taken.name == "submit_orders"
        assert len(client.sent) == 1
        assert "check_neighbours" not in {
            tool.name
            for tool in harness.preview_tools(build_context(lobby_snapshot(), "2"))
        }
    finally:
        await harness.shutdown()
        database.close()


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
            output = final_answer({"house_id": "stark"})
        return ModelResponse(
            output=[output],
            usage=Usage(requests=1, input_tokens=30, output_tokens=10, total_tokens=40),
            response_id=f"recall-resp-{self.calls}",
        )

    async def stream_response(self, *args, **kwargs):
        if False:
            yield None


class RememberThenActionModel(Model):
    def __init__(self, *, fail_after_note: bool = False) -> None:
        self.calls = 0
        self.fail_after_note = fail_after_note

    async def get_response(self, *args, **kwargs) -> ModelResponse:
        self.calls += 1
        if self.calls == 1:
            output = ResponseFunctionToolCall(
                arguments=json.dumps(
                    {"note": "  Hold Winterfell, then pressure the eastern castles.  "}
                ),
                call_id="remember-1",
                name="remember_strategy",
                type="function_call",
            )
        elif self.fail_after_note:
            raise RuntimeError("provider failed after strategy note")
        else:
            output = final_answer({"house_id": "stark"})
        return ModelResponse(
            output=[output],
            usage=Usage(requests=1, input_tokens=30, output_tokens=10, total_tokens=40),
            response_id=f"remember-resp-{self.calls}",
        )

    async def stream_response(self, *args, **kwargs):
        if False:
            yield None


class PendingOutcomeRunner(HarnessStubRunner):
    def __init__(self, outcome: str) -> None:
        self.outcome = outcome

    async def run_once(self, *, context, **_kwargs) -> ModelRunResult:
        context.pending_strategy_note = "This must not be persisted."
        if self.outcome == "cancelled":
            raise asyncio.CancelledError
        return ModelRunResult(
            response_id=None,
            output_text="",
            usage={
                "requests": 0,
                "inputTokens": 0,
                "outputTokens": 0,
                "totalTokens": 0,
            },
            response_items=[],
            raw_usage=[],
        )


def test_strategic_harness_prepares_prompt_tools_and_decision(tmp_path) -> None:
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
        runner=HarnessStubRunner(),
        store=store,
    )
    context = build_context(planning_snapshot(), "2")
    prepared = harness.prepare_turn(record, context, previous_error=None)
    names = [tool.name for tool in prepared.tools]
    assert "submit_orders" not in names
    assert "check_neighbours" in names
    assert "reachable_areas" in names
    assert prepared.instructions.count("\n# Map\n") == 1
    assert "castle-black [land; crown=1]:" in prepared.instructions
    assert "map" not in prepared.observation
    assert prepared.observation["mapVariant"] == "westeros"
    assert "placing planning orders" in prepared.observation["decisionBriefing"]
    assert "check_neighbours looks up" in prepared.observation["decisionBriefing"]
    assert "reachable_areas finds" in prepared.observation["decisionBriefing"]
    assert "not limited to one tool call" in prepared.observation["decisionBriefing"]
    assert "`submit_action`" in prepared.instructions
    assert "placing planning orders" not in prepared.instructions
    assert "\n# Rules\n" in prepared.instructions
    submit_schema = prepared.decision.output_schema.json_schema()
    assignment = submit_schema["properties"]["assignments"]["items"]["properties"]
    assert assignment["region_id"]["enum"] == ["winterfell", "white-harbor"]

    later_snapshot = copy.deepcopy(planning_snapshot())
    later_snapshot["leafStateId"] = "leaf-later"
    later_snapshot["childGameState"]["game"]["turn"] = 2
    later = harness.prepare_turn(
        record, build_context(later_snapshot, "2"), previous_error=None
    )
    assert later.prompt_cache_key == prepared.prompt_cache_key
    assert later.instructions == prepared.instructions

    retry = harness.prepare_turn(
        record,
        build_context(later_snapshot, "2"),
        previous_error="The model returned text instead of a game action",
    )
    assert (
        "call submit_action with corrected arguments"
        in retry.observation["retryInstruction"]
    )
    alternate_snapshot = copy.deepcopy(later_snapshot)
    alternate_snapshot["gameSettings"]["addPortToTheEyrie"] = True
    alternate = harness.prepare_turn(
        record, build_context(alternate_snapshot, "2"), previous_error=None
    )
    assert alternate.observation["mapVariant"] == "ffc-eyrie-with-port"
    assert "Variant: ffc-eyrie-with-port." in alternate.instructions
    assert alternate.prompt_cache_key != prepared.prompt_cache_key
    database.close()


@pytest.mark.asyncio
async def test_strategic_harness_recalls_exact_prior_state_then_acts(
    monkeypatch, tmp_path
) -> None:
    fake_model = RecallThenActionModel()
    monkeypatch.setattr(
        "raven_harness.models.openai_agent._response_model",
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
        {
            "game": {"stateId": "prior-state", "round": 2, "phase": "march"},
            "map": load_map_reference(6),
        },
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
    assert "map" not in recalled["observation"]
    assert recalled["observation"]["mapVariant"] == "westeros"
    automatic_memory = store.get_strategic_memory(record.id)
    assert automatic_memory["roundNumber"] == 0
    assert "used choose_house" in automatic_memory["commitments"][-1]
    await harness.shutdown()
    database.close()


@pytest.mark.asyncio
async def test_remember_strategy_has_bounded_plain_text_schema() -> None:
    schema = remember_strategy.params_json_schema
    assert schema["additionalProperties"] is False
    assert schema["properties"]["note"] == {
        "description": (
            "Concise replacement for your durable multi-round strategic plan. "
            "Use only when the plan materially changes."
        ),
        "maxLength": 2_000,
        "minLength": 1,
        "title": "Note",
        "type": "string",
    }

    client = FakeClient(lobby_snapshot())
    context = HarnessRunContext(client=client, user_id="2")
    maximum = json.dumps({"note": "x" * 2_000})
    accepted = await remember_strategy.on_invoke_tool(
        ToolContext(
            context=context,
            tool_call_id="remember-maximum",
            tool_name=remember_strategy.name,
            tool_arguments=maximum,
        ),
        maximum,
    )
    assert json.loads(accepted)["pending"] is True
    assert context.pending_strategy_note == "x" * 2_000

    too_long_context = HarnessRunContext(client=client, user_id="2")
    too_long = json.dumps({"note": "x" * 2_001})
    await remember_strategy.on_invoke_tool(
        ToolContext(
            context=too_long_context,
            tool_call_id="remember-too-long",
            tool_name=remember_strategy.name,
            tool_arguments=too_long,
        ),
        too_long,
    )
    assert too_long_context.pending_strategy_note is None


@pytest.mark.asyncio
async def test_strategy_note_commits_only_after_accepted_gameplay_action(
    monkeypatch, tmp_path
) -> None:
    fake_model = RememberThenActionModel()
    monkeypatch.setattr(
        "raven_harness.models.openai_agent._response_model",
        lambda **_kwargs: fake_model,
    )
    database = Database(tmp_path / "strategy-success.db")
    store = AgentStore(database)
    record = store.create_agent(
        AgentCreate(name="Wolf", model="test-model", user_id="2", auth_token="secret")
    )
    client = FakeClient(lobby_snapshot())
    harness = StrategicHarness(
        OpenAIAgentRunner(api_key="test-key", base_url="https://api.test/v1"),
        store,
    )
    prepared = harness.prepare_turn(
        record, build_context(client.snapshot, "2"), previous_error=None
    )
    run_context = HarnessRunContext(client=client, user_id="2", game_password="wolf")

    await harness.run_turn(record, prepared, run_context, "strategy-success")

    assert fake_model.calls == 2
    assert run_context.action_taken is not None
    memory = store.get_strategic_memory(record.id)
    assert memory["modelPlan"] == "Continue the current plan next decision."
    assert memory["decisionJournal"][-1].endswith(
        "Continue the current plan next decision."
    )
    assert memory["revision"] == 1
    await harness.shutdown()
    database.close()


@pytest.mark.asyncio
async def test_strategy_note_is_not_committed_when_parent_model_fails(
    monkeypatch, tmp_path
) -> None:
    fake_model = RememberThenActionModel(fail_after_note=True)
    monkeypatch.setattr(
        "raven_harness.models.openai_agent._response_model",
        lambda **_kwargs: fake_model,
    )
    database = Database(tmp_path / "strategy-failure.db")
    store = AgentStore(database)
    record = store.create_agent(
        AgentCreate(name="Wolf", model="test-model", user_id="2", auth_token="secret")
    )
    original = store.set_strategic_memory(record.id, {"modelPlan": "Original plan"})
    client = FakeClient(lobby_snapshot())
    harness = StrategicHarness(
        OpenAIAgentRunner(api_key="test-key", base_url="https://api.test/v1"),
        store,
    )
    prepared = harness.prepare_turn(
        record, build_context(client.snapshot, "2"), previous_error=None
    )
    run_context = HarnessRunContext(client=client, user_id="2", game_password="wolf")

    with pytest.raises(RuntimeError, match="provider failed after strategy note"):
        await harness.run_turn(record, prepared, run_context, "strategy-failure")

    memory = store.get_strategic_memory(record.id)
    assert memory["modelPlan"] == "Original plan"
    assert memory["revision"] == original["revision"]
    await harness.shutdown()
    database.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("outcome", ["no-action", "cancelled"])
async def test_pending_strategy_is_not_committed_without_returned_accepted_action(
    outcome, tmp_path
) -> None:
    database = Database(tmp_path / f"strategy-{outcome}.db")
    store = AgentStore(database)
    record = store.create_agent(
        AgentCreate(name="Wolf", model="test-model", user_id="2", auth_token="secret")
    )
    original = store.set_strategic_memory(record.id, {"modelPlan": "Original plan"})
    client = FakeClient(lobby_snapshot())
    harness = StrategicHarness(PendingOutcomeRunner(outcome), store)
    prepared = harness.prepare_turn(
        record, build_context(client.snapshot, "2"), previous_error=None
    )
    run_context = HarnessRunContext(client=client, user_id="2", game_password="wolf")

    if outcome == "cancelled":
        with pytest.raises(asyncio.CancelledError):
            await harness.run_turn(record, prepared, run_context, f"strategy-{outcome}")
    else:
        await harness.run_turn(record, prepared, run_context, f"strategy-{outcome}")

    memory = store.get_strategic_memory(record.id)
    assert memory["modelPlan"] == "Original plan"
    assert memory["revision"] == original["revision"]
    database.close()


def test_base_game_instructions_are_identical_for_all_six_houses(tmp_path):
    database = Database(tmp_path / 'shared-instructions.db')
    store = AgentStore(database)
    runner = HarnessStubRunner()
    runner.rules_oracle_available = True
    harness = StrategicHarness(runner, store)
    prompts = []
    try:
        for house in ['stark', 'lannister', 'baratheon', 'greyjoy', 'tyrell', 'martell']:
            snapshot = planning_snapshot()
            ingame = snapshot['childGameState']
            ingame['players'][0]['houseId'] = house
            ingame['game']['houses'][0]['id'] = house
            for region in ingame['game']['world']['regions']:
                for unit in region['units']:
                    unit['allegiance'] = house
            record = store.create_agent(AgentCreate(
                name=house, user_id='2', auth_token='test', model='openai/gpt-oss-120b',
            ))
            prepared = harness.prepare_turn(record, build_context(snapshot, '2'), None)
            prompts.append(prepared.instructions)
            assert 'Base-game decision reference' in prepared.instructions
            assert prepared.display_observation['you']['powerTokens'] == 5
            assert prepared.observation['you'] == {'houseId': house}
        assert len(set(prompts)) == 1
    finally:
        database.close()
