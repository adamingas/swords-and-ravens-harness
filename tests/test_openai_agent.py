import asyncio
from collections.abc import AsyncIterator
from types import SimpleNamespace
from typing import Any

import pytest
from agents import ModelResponse, ModelSettings, Usage
from agents.models.interface import Model
from openai.types.responses import (
    ResponseFunctionToolCall,
    ResponseOutputMessage,
    ResponseOutputText,
)

from raven_harness.game.client import GameConnectionLost
from raven_harness.harness.actions import HarnessRunContext, available_tools
from raven_harness.harness.decision import build_decision_contract
from raven_harness.harness.observation import build_observation
from raven_harness.models.openai_agent import (
    SUBMISSION_REMINDER,
    ModelRunCancelled,
    ModelRunError,
    OpenAIAgentRunner,
    OpenRouterAgentRunner,
    PermanentModelError,
    TransientProviderCapacityError,
    _UsageCapturingResponsesModel,
    _partial_result,
)
from raven_harness.schemas import AgentCreate, AgentRecord

from conftest import lobby_snapshot


class FakeClient:
    def __init__(self) -> None:
        self.snapshot = lobby_snapshot()
        self.recent_events: list[dict[str, Any]] = []
        self.sent: list[dict[str, Any]] = []
        self.connection_generation = 1

    async def send(self, message, *, require_auth=True, expected_generation=None):
        del require_auth
        if expected_generation != self.connection_generation:
            raise GameConnectionLost("stale connection generation")
        self.sent.append(message)

    async def sync_snapshot(self, timeout=10, *, expected_generation=None):
        del timeout
        if expected_generation != self.connection_generation:
            raise GameConnectionLost("stale connection generation")
        message = self.sent[-1]
        if message["type"] == "choose-house":
            self.snapshot["childGameState"]["players"].append([message["house"], "2"])
        return self.snapshot


def _message(text: str, number: int) -> ResponseOutputMessage:
    return ResponseOutputMessage(
        id=f"message-{number}",
        content=[
            ResponseOutputText(
                annotations=[], logprobs=[], text=text, type="output_text"
            )
        ],
        role="assistant",
        status="completed",
        type="message",
    )


class SubmittingModel(Model):
    def __init__(self, *, text_completions: int = 0) -> None:
        self.text_completions = text_completions
        self.inputs: list[list[dict[str, Any]]] = []
        self.settings: ModelSettings | None = None

    async def get_response(self, *args, **kwargs) -> ModelResponse:
        del args
        self.inputs.append(kwargs["input"])
        self.settings = kwargs["model_settings"]
        number = len(self.inputs)
        assert [tool.name for tool in kwargs["tools"]] == ["submit_action"]
        output = (
            [_message("I have chosen Stark.", number)]
            if number <= self.text_completions
            else [
                ResponseFunctionToolCall(
                    arguments=(
                        '{"house_id":"stark",'
                        '"strategic_handoff":"Secure Winterfell next."}'
                    ),
                    call_id=f"submit-{number}",
                    name="submit_action",
                    type="function_call",
                )
            ]
        )
        return ModelResponse(
            output=output,
            usage=Usage(requests=1, input_tokens=20, output_tokens=5, total_tokens=25),
            response_id=f"response-{number}",
        )

    async def stream_response(self, *args, **kwargs) -> AsyncIterator[Any]:
        if False:
            yield None


class FailingModel(Model):
    def __init__(self, error: BaseException) -> None:
        self.error = error

    async def get_response(self, *args, **kwargs) -> ModelResponse:
        raise self.error

    async def stream_response(self, *args, **kwargs) -> AsyncIterator[Any]:
        if False:
            yield None


def turn_arguments(record: AgentRecord, context: HarnessRunContext) -> dict[str, Any]:
    game_context = context.current_game_context()
    decision = build_decision_contract(game_context, available_tools(game_context))
    assert decision is not None
    context.decision = decision
    observation = build_observation(game_context)
    observation["decisionBriefing"] = "Choose your available house."
    return {
        "agent_record": record,
        "observation": observation,
        "context": context,
        "tools": [],
        "instructions": record.system_prompt,
        "prompt_cache_key": "test-cache-key",
        "trace_metadata": {
            "agent_id": record.id,
            "game_id": record.game_id,
            "run_id": "test-run",
        },
    }


def _record() -> AgentRecord:
    return AgentRecord.from_create(
        AgentCreate(name="Wolf", model="test-model", user_id="2", auth_token="secret")
    )


@pytest.mark.asyncio
async def test_runner_submits_the_dynamic_action_tool(monkeypatch) -> None:
    model = SubmittingModel()
    monkeypatch.setattr(
        "raven_harness.models.openai_agent._response_model", lambda **_: model
    )
    client = FakeClient()
    context = HarnessRunContext(client=client, user_id="2", game_password="wolf")

    result = await OpenAIAgentRunner(
        api_key="test-key", base_url="https://api.openai.test/v1"
    ).run_once(**turn_arguments(_record(), context))

    assert context.action_taken is not None
    assert context.action_taken.name == "choose_house"
    assert client.sent == [
        {"type": "choose-house", "house": "stark", "password": "wolf"}
    ]
    assert result.usage["requests"] == 1
    assert model.settings is not None
    assert model.settings.tool_choice == "auto"
    assert model.settings.reasoning.effort == "high"


@pytest.mark.asyncio
async def test_text_completion_continues_the_same_decision_until_submission(
    monkeypatch,
) -> None:
    model = SubmittingModel(text_completions=1)
    monkeypatch.setattr(
        "raven_harness.models.openai_agent._response_model", lambda **_: model
    )
    context = HarnessRunContext(client=FakeClient(), user_id="2", game_password="wolf")

    result = await OpenAIAgentRunner(
        api_key="test-key", base_url="https://api.openai.test/v1"
    ).run_once(**turn_arguments(_record(), context))

    assert context.action_taken is not None
    assert len(model.inputs) == 2
    assert model.inputs[1][-1] == {"role": "user", "content": SUBMISSION_REMINDER}
    assert "Current observation:" in model.inputs[1][0]["content"]
    assert any(item.get("role") == "assistant" for item in model.inputs[1])
    assert result.usage["requests"] == 2


@pytest.mark.asyncio
async def test_repeated_text_completions_stop_with_traceable_usage(monkeypatch) -> None:
    model = SubmittingModel(text_completions=10)
    monkeypatch.setattr(
        "raven_harness.models.openai_agent._response_model", lambda **_: model
    )
    client = FakeClient()
    context = HarnessRunContext(client=client, user_id="2", game_password="wolf")
    with pytest.raises(ModelRunError, match="three times without submitting") as caught:
        await OpenAIAgentRunner(
            api_key="test-key", base_url="https://api.openai.test/v1"
        ).run_once(**turn_arguments(_record(), context))
    assert len(model.inputs) == 3
    assert caught.value.partial_result.usage["requests"] == 3
    assert context.action_taken is None
    assert client.sent == []


@pytest.mark.asyncio
async def test_stale_connection_stops_without_replaying_action(monkeypatch) -> None:
    model = SubmittingModel()
    monkeypatch.setattr(
        "raven_harness.models.openai_agent._response_model", lambda **_: model
    )
    client = FakeClient()
    context = HarnessRunContext(client=client, user_id="2", game_password="wolf")
    client.connection_generation += 1

    with pytest.raises(GameConnectionLost, match="stale connection generation"):
        await OpenAIAgentRunner(
            api_key="test-key", base_url="https://api.openai.test/v1"
        ).run_once(**turn_arguments(_record(), context))
    assert client.sent == []


@pytest.mark.asyncio
async def test_provider_failures_are_classified_and_redacted(monkeypatch) -> None:
    capacity = RuntimeError("provider capacity unavailable")
    capacity.status_code = 503  # type: ignore[attr-defined]
    cases = [
        (RuntimeError("provider failed"), ModelRunError),
        (capacity, TransientProviderCapacityError),
        (
            RuntimeError(
                "spending limit exhausted; https://provider.test/settings/keys/private-key-id"
            ),
            PermanentModelError,
        ),
    ]
    for error, expected_type in cases:
        monkeypatch.setattr(
            "raven_harness.models.openai_agent._response_model",
            lambda error=error, **_: FailingModel(error),
        )
        context = HarnessRunContext(client=FakeClient(), user_id="2")
        with pytest.raises(expected_type) as raised:
            await OpenAIAgentRunner(
                api_key="test-key", base_url="https://api.openai.test/v1"
            ).run_once(**turn_arguments(_record(), context))
        assert "private-key-id" not in str(raised.value)


@pytest.mark.asyncio
async def test_cancellation_preserves_partial_trace(monkeypatch) -> None:
    monkeypatch.setattr(
        "raven_harness.models.openai_agent._response_model",
        lambda **_: FailingModel(asyncio.CancelledError()),
    )
    context = HarnessRunContext(client=FakeClient(), user_id="2")
    with pytest.raises(ModelRunCancelled) as raised:
        await OpenAIAgentRunner(
            api_key="test-key", base_url="https://api.openai.test/v1"
        ).run_once(**turn_arguments(_record(), context))
    assert raised.value.partial_result.usage["requests"] == 0


def test_openrouter_routes_around_blocked_providers_with_cache_affinity() -> None:
    runner = OpenRouterAgentRunner(
        api_key="test-key",
        base_url="https://openrouter.ai/api/v1",
        provider_blocklist=["Together", "novita", "together"],
    )
    settings = runner._model_settings(
        max_tokens=None, prompt_cache_key="cache-key", metadata=None, user="agent-id"
    )
    assert settings.extra_body == {
        "session_id": "raven-agent-agent-id",
        "provider": {"ignore": ["together", "novita"]},
    }


class TerminalUsage:
    requests = 1
    input_tokens = 100
    output_tokens = 16
    total_tokens = 116

    def model_dump(self, **_kwargs: Any) -> dict[str, Any]:
        return {"input_tokens": 100, "output_tokens": 16, "total_tokens": 116}


@pytest.mark.asyncio
async def test_failed_response_preserves_provider_error_details() -> None:
    async def create(**_kwargs: Any) -> Any:
        return SimpleNamespace(
            id="failed-1",
            status="failed",
            model="test-model",
            provider="Example Provider",
            service_tier="priority",
            _request_id="request-1",
            usage=TerminalUsage(),
            incomplete_details=None,
            error={"code": "server_error", "message": "Generation failed"},
            output=[],
        )

    responses = []
    model = _UsageCapturingResponsesModel(
        model="test-model",
        openai_client=SimpleNamespace(responses=SimpleNamespace(create=create)),
        response_sink=responses,
    )
    with pytest.raises(RuntimeError, match="Generation failed"):
        await model._fetch_response(
            None, [], ModelSettings(), [], None, [], stream=False
        )
    result = _partial_result([], {}, provider_responses=responses)
    assert result.response_items[0]["providerError"]["code"] == "server_error"


@pytest.mark.asyncio
async def test_parent_output_allowance_does_not_change_oracle_settings():
    runner = OpenRouterAgentRunner(
        api_key="test-key", base_url="https://openrouter.ai/api/v1",
        provider_blocklist=["novita"], max_output_tokens=40960,
    )
    try:
        from raven_harness.models.openai_agent import RULES_ORACLE_MAX_OUTPUT_TOKENS

        oracle = runner._model_settings(max_tokens=RULES_ORACLE_MAX_OUTPUT_TOKENS, prompt_cache_key=None, metadata=None)
        assert oracle.max_tokens == 16384
        assert oracle.reasoning.effort == "high"
        assert oracle.extra_body["provider"]["ignore"] == ["novita"]
    finally:
        await runner.shutdown()


@pytest.mark.parametrize("limit", [0, -1])
def test_invalid_explicit_output_allowance_is_rejected(limit):
    with pytest.raises(ValueError, match="positive"):
        OpenAIAgentRunner(api_key="test-key", base_url="https://api.test/v1", max_output_tokens=limit)
