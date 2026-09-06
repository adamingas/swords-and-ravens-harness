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
from raven_harness.harness.actions import HarnessRunContext
from raven_harness.harness.interface import PlayerHarness
from raven_harness.harness.observation import build_context, build_observation
from raven_harness.harness import strategic as strategic_module
from raven_harness.harness.strategic import StrategicHarness, remember_strategy
from raven_harness.models.openai_agent import ModelRunResult, OpenAIAgentRunner
from raven_harness.schemas import AgentCreate

from conftest import lobby_snapshot, planning_snapshot


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
            self.snapshot["childGameState"]["players"].append(
                [message["house"], "2"]
            )
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
        max_turns,
        stop_at_tool_names,
        prompt_cache_key,
        trace_metadata,
    ):
        raise AssertionError("The model should not run in this test")

    async def shutdown(self) -> None:
        pass

    async def clear_session(self, agent_id: str) -> None:
        del agent_id


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
            output = ResponseFunctionToolCall(
                arguments='{"house_id":"stark"}',
                call_id="action-after-memory",
                name="choose_house",
                type="function_call",
            )
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


def test_strategic_harness_implements_interface_and_prepares_memory(
    tmp_path, monkeypatch
) -> None:
    observation_builds = 0
    action_spec_builds = 0
    build_action_specs = strategic_module.available_action_specs

    def count_observation_build(context):
        nonlocal observation_builds
        observation_builds += 1
        return build_observation(context)

    def count_action_spec_build(context):
        nonlocal action_spec_builds
        action_spec_builds += 1
        return build_action_specs(context)

    monkeypatch.setattr(strategic_module, "build_observation", count_observation_build)
    monkeypatch.setattr(
        strategic_module, "available_action_specs", count_action_spec_build
    )
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
    assert isinstance(harness, PlayerHarness)

    context = build_context(planning_snapshot(), "2")
    prepared = harness.prepare_turn(record, context, previous_error=None)
    assert observation_builds == 1
    assert action_spec_builds == 1
    names = [tool.name for tool in prepared.tools]
    assert "submit_orders" in names
    assert "recall_game_state" in names
    assert "remember_strategy" in names
    assert "update_strategic_memory" not in names
    assert prepared.prompt_cache_key.startswith("raven-")
    assert prepared.observation["strategicMemory"]["revision"] == 0
    assert prepared.observation["strategicMemory"]["roundNumber"] is None
    assert prepared.observation["strategicMemory"]["modelPlan"] == ""
    assert prepared.observation["strategicOverview"]["round"] == 1
    assert prepared.observation["planningConstraints"][
        "maxAssignmentsByOrderCategory"
    ] == {
        "march": 2,
        "defense": 2,
        "support": 2,
        "consolidate_power": 2,
        "raid": 2,
    }
    submit_schema = next(
        tool.params_json_schema for tool in prepared.tools if tool.name == "submit_orders"
    )
    assignment = submit_schema["properties"]["assignments"]["items"]["properties"]
    assert "$defs" not in submit_schema
    assert assignment["region_id"]["enum"] == ["winterfell", "white-harbor"]
    assert "defense=2" in assignment["order"]["description"]
    assert store.recall_state(record.id, 0)["stateId"] == "leaf-2"  # type: ignore[index]

    later_snapshot = copy.deepcopy(planning_snapshot())
    later_snapshot["leafStateId"] = "leaf-later"
    later_snapshot["childGameState"]["game"]["turn"] = 2
    later = harness.prepare_turn(
        record, build_context(later_snapshot, "2"), previous_error=None
    )
    assert observation_builds == 2
    assert action_spec_builds == 2
    assert later.prompt_cache_key == prepared.prompt_cache_key
    submit_orders = next(tool for tool in later.tools if tool.name == "submit_orders")
    assert "winterfell" not in submit_orders.description.lower()
    assert later.game_tool_names == ["submit_orders"]

    retry = harness.prepare_turn(
        record,
        build_context(later_snapshot, "2"),
        previous_error="The model returned text instead of a game action",
    )
    assert retry.observation["previousAttemptError"].startswith("The model returned")
    assert "actual function-tool mechanism" in retry.observation["retryInstruction"]
    assert [tool.name for tool in retry.tools] == ["submit_orders"]
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
        "raven_harness.models.openai_agent.OpenAIResponsesModel",
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
    assert memory["modelPlan"] == (
        "Hold Winterfell, then pressure the eastern castles."
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
        "raven_harness.models.openai_agent.OpenAIResponsesModel",
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
