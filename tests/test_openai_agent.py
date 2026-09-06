import asyncio
from collections.abc import AsyncIterator
import hashlib
import json
import sqlite3
from types import SimpleNamespace
from typing import Any

import pytest
from agents import ModelResponse, ModelSettings, Usage
from agents.memory import SQLiteSession
from agents.models.interface import Model
from openai.types.responses import ResponseFunctionToolCall

from raven_harness.agent_store import AgentStore
from raven_harness.database import Database
from raven_harness.game.client import GameConnectionLost
from raven_harness.harness.actions import HarnessRunContext, available_tools
from raven_harness.harness.observation import build_observation
from raven_harness.harness.strategic import remember_strategy
from raven_harness.models.openai_agent import (
    CONTEXT_POLICY_NAME,
    OBSERVATION_INPUT_PREFIX,
    ModelRunCancelled,
    ModelRunError,
    OpenAIAgentRunner,
    PermanentModelError,
    _SessionContextFilter,
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

    async def send(
        self,
        message: dict[str, Any],
        *,
        require_auth: bool = True,
        expected_generation: int | None = None,
    ) -> None:
        del require_auth
        if expected_generation != self.connection_generation:
            raise GameConnectionLost("stale connection generation")
        self.sent.append(message)

    async def sync_snapshot(
        self,
        timeout: float = 10,
        *,
        expected_generation: int | None = None,
    ) -> dict[str, Any]:
        del timeout
        if expected_generation != self.connection_generation:
            raise GameConnectionLost("stale connection generation")
        message = self.sent[-1]
        if message["type"] == "choose-house":
            self.snapshot["childGameState"]["players"].append(
                [message["house"], "2"]
            )
        return self.snapshot


class TerminalUsage:
    requests = 1
    input_tokens = 100
    output_tokens = 16
    total_tokens = 116

    def model_dump(self, **_kwargs: Any) -> dict[str, Any]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "cost": 0.01,
        }


class TerminalResponses:
    async def create(self, **_kwargs: Any) -> Any:
        return SimpleNamespace(
            id="incomplete-1",
            status="incomplete",
            usage=TerminalUsage(),
            incomplete_details=SimpleNamespace(reason="max_output_tokens"),
            output=[],
        )


@pytest.mark.asyncio
async def test_failed_terminal_response_keeps_usage_and_cost() -> None:
    terminal_responses: list[Any] = []
    model = _UsageCapturingResponsesModel(
        model="test-model",
        openai_client=SimpleNamespace(responses=TerminalResponses()),
        terminal_response_sink=terminal_responses,
    )

    with pytest.raises(RuntimeError, match="terminal status incomplete"):
        await model._fetch_response(
            None,
            [],
            ModelSettings(),
            [],
            None,
            [],
            stream=False,
        )
    result = _partial_result(
        [], {}, terminal_responses=terminal_responses
    )

    assert result.usage == {
        "requests": 1,
        "inputTokens": 100,
        "outputTokens": 16,
        "totalTokens": 116,
    }
    assert result.raw_usage == [
        {
            "input_tokens": 100,
            "output_tokens": 16,
            "total_tokens": 116,
            "cost": 0.01,
            "scope": "agent",
            "response_id": "incomplete-1",
        }
    ]


class ToolCallingModel(Model):
    def __init__(self, expected_tool_names: list[str] | None = None) -> None:
        self.model_settings: Any = None
        self.inputs: list[list[dict[str, Any]]] = []
        self.call_count = 0
        self.expected_tool_names = expected_tool_names or ["choose_house"]

    async def get_response(self, *args, **kwargs) -> ModelResponse:
        tools = kwargs["tools"]
        self.model_settings = kwargs["model_settings"]
        self.inputs.append(kwargs["input"])
        self.call_count += 1
        assert [tool.name for tool in tools] == self.expected_tool_names
        return ModelResponse(
            output=[
                ResponseFunctionToolCall(
                    arguments='{"house_id":"stark"}',
                    call_id=f"call-{self.call_count}",
                    name="choose_house",
                    type="function_call",
                )
            ],
            usage=Usage(requests=1, input_tokens=20, output_tokens=5, total_tokens=25),
            response_id=f"resp-{self.call_count}",
        )

    async def stream_response(self, *args, **kwargs) -> AsyncIterator[Any]:
        if False:
            yield None


class ConcurrentToolCallingModel(ToolCallingModel):
    def __init__(self, expected_concurrency: int) -> None:
        super().__init__()
        self.expected_concurrency = expected_concurrency
        self.active = 0
        self.peak_active = 0
        self.all_started = asyncio.Event()

    async def get_response(self, *args, **kwargs) -> ModelResponse:
        self.active += 1
        self.peak_active = max(self.peak_active, self.active)
        if self.active == self.expected_concurrency:
            self.all_started.set()
        try:
            await asyncio.wait_for(self.all_started.wait(), timeout=0.5)
            return await super().get_response(*args, **kwargs)
        finally:
            self.active -= 1


class CorrectingToolCallingModel(ToolCallingModel):
    async def get_response(self, *args, **kwargs) -> ModelResponse:
        self.model_settings = kwargs["model_settings"]
        self.inputs.append(kwargs["input"])
        self.call_count += 1
        assert [tool.name for tool in kwargs["tools"]] == self.expected_tool_names
        house_id = "greyjoy" if self.call_count == 1 else "stark"
        return ModelResponse(
            output=[
                ResponseFunctionToolCall(
                    arguments=json.dumps({"house_id": house_id}),
                    call_id=f"correcting-call-{self.call_count}",
                    name="choose_house",
                    type="function_call",
                )
            ],
            usage=Usage(requests=1, input_tokens=20, output_tokens=5, total_tokens=25),
            response_id=f"correcting-response-{self.call_count}",
        )


class RepeatingInvalidToolCallingModel(ToolCallingModel):
    async def get_response(self, *args, **kwargs) -> ModelResponse:
        self.model_settings = kwargs["model_settings"]
        self.inputs.append(kwargs["input"])
        self.call_count += 1
        return ModelResponse(
            output=[
                ResponseFunctionToolCall(
                    arguments='{"house_id":"greyjoy"}',
                    call_id=f"invalid-call-{self.call_count}",
                    name="choose_house",
                    type="function_call",
                )
            ],
            usage=Usage(requests=1, input_tokens=20, output_tokens=5, total_tokens=25),
            response_id=f"invalid-response-{self.call_count}",
        )


class FailingModel(Model):
    async def get_response(self, *args, **kwargs) -> ModelResponse:
        raise RuntimeError("provider failed")

    async def stream_response(self, *args, **kwargs) -> AsyncIterator[Any]:
        if False:
            yield None


class QuotaFailingModel(Model):
    async def get_response(self, *args, **kwargs) -> ModelResponse:
        raise RuntimeError(
            "spending limit exhausted; visit "
            "https://provider.test/settings/keys/private-key-id"
        )

    async def stream_response(self, *args, **kwargs) -> AsyncIterator[Any]:
        if False:
            yield None


class CancellingModel(Model):
    async def get_response(self, *args, **kwargs) -> ModelResponse:
        raise asyncio.CancelledError

    async def stream_response(self, *args, **kwargs) -> AsyncIterator[Any]:
        if False:
            yield None


class RememberThenFailModel(Model):
    def __init__(self) -> None:
        self.call_count = 0

    async def get_response(self, *args, **kwargs) -> ModelResponse:
        self.call_count += 1
        if self.call_count == 2:
            raise RuntimeError("provider failed after note")
        return ModelResponse(
            output=[
                ResponseFunctionToolCall(
                    arguments='{"note":"Uncommitted northern plan"}',
                    call_id="remember-1",
                    name="remember_strategy",
                    type="function_call",
                )
            ],
            usage=Usage(requests=1, input_tokens=20, output_tokens=5, total_tokens=25),
            response_id="remember-response",
        )

    async def stream_response(self, *args, **kwargs) -> AsyncIterator[Any]:
        if False:
            yield None


def turn_arguments(
    record: AgentRecord, context: HarnessRunContext
) -> dict[str, Any]:
    game_context = context.current_game_context()
    return {
        "agent_record": record,
        "observation": build_observation(game_context),
        "context": context,
        "tools": available_tools(game_context),
        "instructions": record.system_prompt,
        "max_turns": 1,
        "stop_at_tool_names": ["choose_house"],
        "prompt_cache_key": "test-cache-key",
        "trace_metadata": {
            "agent_id": record.id,
            "game_id": record.game_id,
            "run_id": "test-run",
        },
    }


@pytest.mark.asyncio
async def test_openai_runner_attaches_and_executes_agents_sdk_tools(
    monkeypatch,
) -> None:
    fake_model = ToolCallingModel()
    monkeypatch.setattr(
        "raven_harness.models.openai_agent._response_model",
        lambda **_kwargs: fake_model,
    )
    record = AgentRecord.from_create(
        AgentCreate(name="Wolf", user_id="2", auth_token="secret")
    )
    client = FakeClient()
    context = HarnessRunContext(client=client, user_id="2", game_password="wolf")

    runner = OpenAIAgentRunner(
        api_key="test-key",
        base_url="https://api.openai.test/v1",
        max_retries=4,
        provider_routing={
            "sort": "throughput",
            "allow_fallbacks": True,
            "require_parameters": False,
        },
    )
    result = await runner.run_once(**turn_arguments(record, context))

    assert result.response_id == "resp-1"
    assert result.usage["totalTokens"] == 25
    assert result.raw_usage == [{"scope": "agent", "response_id": "resp-1"}]
    request_input = json.dumps(
        fake_model.inputs[0], ensure_ascii=False, separators=(",", ":"), sort_keys=True
    )
    assert result.context_manifest == {
        "policy": CONTEXT_POLICY_NAME,
        "historyMode": "recent-accepted-actions",
        "sessionHistoryLimit": 32,
        "retrievedHistoryItemCount": 0,
        "discardedPrefixItemCount": 0,
        "removedObservationItemCount": 0,
        "removedObservationCharacters": 0,
        "removedSupportToolItemCount": 0,
        "removedSupportToolCharacters": 0,
        "removedRetryHistoryItemCount": 0,
        "removedRetryHistoryCharacters": 0,
        "selectedHistoryItems": [],
        "currentInputItemCount": 1,
        "currentInputCharacters": len(fake_model.inputs[0][0]["content"]),
        "currentInputSha256": hashlib.sha256(
            fake_model.inputs[0][0]["content"].encode("utf-8")
        ).hexdigest(),
        "modelRequestInputs": [
            {
                "requestIndex": 1,
                "inputItemCount": 1,
                "inputCharacters": len(request_input),
                "inputSha256": hashlib.sha256(
                    request_input.encode("utf-8")
                ).hexdigest(),
                "instructionsCharacters": len(record.system_prompt),
                "instructionsSha256": hashlib.sha256(
                    record.system_prompt.encode("utf-8")
                ).hexdigest(),
            }
        ],
    }
    assert context.action_taken is not None
    assert context.action_taken.name == "choose_house"
    assert runner.client.max_retries == 4
    assert fake_model.model_settings.tool_choice == "required"
    assert fake_model.model_settings.extra_body == {
        "provider": {
            "sort": "throughput",
            "allow_fallbacks": True,
            "require_parameters": False,
        }
    }
    assert client.sent == [
        {"type": "choose-house", "house": "stark", "password": "wolf"}
    ]


@pytest.mark.asyncio
async def test_runner_does_not_limit_simultaneous_agent_model_calls(
    monkeypatch,
) -> None:
    fake_model = ConcurrentToolCallingModel(expected_concurrency=6)
    monkeypatch.setattr(
        "raven_harness.models.openai_agent._response_model",
        lambda **_kwargs: fake_model,
    )
    runner = OpenAIAgentRunner(
        api_key="test-key",
        base_url="https://api.openai.test/v1",
    )
    calls = []
    for call_number in range(1, 7):
        record = AgentRecord.from_create(
            AgentCreate(
                name=f"Player {call_number}",
                user_id="2",
                auth_token="secret",
            )
        )
        context = HarnessRunContext(
            client=FakeClient(),
            user_id="2",
            game_password="wolf",
        )
        arguments = turn_arguments(record, context)
        arguments["trace_metadata"] = {
            **arguments["trace_metadata"],
            "agent_id": record.id,
            "run_id": f"run-{call_number}",
        }
        calls.append(runner.run_once(**arguments))

    await asyncio.wait_for(asyncio.gather(*calls), timeout=1)

    assert fake_model.peak_active == 6


@pytest.mark.asyncio
async def test_runner_aborts_stale_gameplay_tool_without_replay(
    monkeypatch,
) -> None:
    fake_model = ToolCallingModel()
    monkeypatch.setattr(
        "raven_harness.models.openai_agent._response_model",
        lambda **_kwargs: fake_model,
    )
    record = AgentRecord.from_create(
        AgentCreate(name="Wolf", user_id="2", auth_token="secret")
    )
    client = FakeClient()
    context = HarnessRunContext(client=client, user_id="2", game_password="wolf")
    client.connection_generation += 1
    runner = OpenAIAgentRunner(
        api_key="test-key",
        base_url="https://api.openai.test/v1",
    )

    with pytest.raises(GameConnectionLost, match="stale connection generation"):
        await runner.run_once(**turn_arguments(record, context))

    assert fake_model.call_count == 1
    assert client.sent == []


@pytest.mark.asyncio
async def test_retry_requires_a_tool_call(monkeypatch) -> None:
    fake_model = ToolCallingModel()
    monkeypatch.setattr(
        "raven_harness.models.openai_agent._response_model",
        lambda **_kwargs: fake_model,
    )
    record = AgentRecord.from_create(
        AgentCreate(name="Wolf", user_id="2", auth_token="secret")
    )
    context = HarnessRunContext(
        client=FakeClient(), user_id="2", game_password="wolf"
    )
    arguments = turn_arguments(record, context)
    arguments["observation"]["previousAttemptError"] = "No accepted game action"

    await OpenAIAgentRunner(
        api_key="test-key", base_url="https://api.openai.test/v1"
    ).run_once(**arguments)

    assert fake_model.model_settings.tool_choice == "required"


@pytest.mark.asyncio
async def test_retry_uses_only_the_current_observation(monkeypatch, tmp_path) -> None:
    fake_model = ToolCallingModel()
    monkeypatch.setattr(
        "raven_harness.models.openai_agent._response_model",
        lambda **_kwargs: fake_model,
    )
    record = AgentRecord.from_create(
        AgentCreate(name="Wolf", user_id="2", auth_token="secret")
    )
    client = FakeClient()
    runner = OpenAIAgentRunner(
        api_key="test-key",
        base_url="https://api.openai.test/v1",
        session_database_path=tmp_path / "retry-context.db",
    )

    await runner.run_once(
        **turn_arguments(
            record,
            HarnessRunContext(client=client, user_id="2", game_password="wolf"),
        )
    )
    retry_arguments = turn_arguments(
        record,
        HarnessRunContext(client=client, user_id="2", game_password="wolf"),
    )
    retry_arguments["observation"]["previousAttemptError"] = (
        "The prior action was not accepted"
    )
    result = await runner.run_once(**retry_arguments)

    assert len(fake_model.inputs[1]) == 1
    assert fake_model.inputs[1][0]["role"] == "user"
    assert fake_model.inputs[1][0]["content"].startswith(OBSERVATION_INPUT_PREFIX)
    manifest = result.context_manifest
    assert manifest["historyMode"] == "current-observation-only-retry"
    assert manifest["retrievedHistoryItemCount"] == 3
    assert manifest["removedRetryHistoryItemCount"] == 3
    assert manifest["removedRetryHistoryCharacters"] > 0
    assert manifest["selectedHistoryItems"] == []
    assert manifest["modelRequestInputs"][0]["inputItemCount"] == 1
    await runner.shutdown()


@pytest.mark.asyncio
async def test_openai_runner_reports_sanitized_request_and_tool_lifecycle(
    monkeypatch,
) -> None:
    fake_model = ToolCallingModel()
    monkeypatch.setattr(
        "raven_harness.models.openai_agent._response_model",
        lambda **_kwargs: fake_model,
    )
    record = AgentRecord.from_create(
        AgentCreate(name="Wolf", user_id="2", auth_token="secret")
    )
    activities: list[tuple[str, dict[str, Any]]] = []
    context = HarnessRunContext(
        client=FakeClient(),
        user_id="2",
        game_password="private-game-password",
        activity_sink=lambda kind, payload: activities.append((kind, payload)),
    )

    await OpenAIAgentRunner(
        api_key="private-api-key",
        base_url="https://api.openai.test/v1",
    ).run_once(**turn_arguments(record, context))

    assert [kind for kind, _payload in activities] == [
        "model-request-started",
        "model-request-completed",
        "model-tool-started",
        "model-tool-completed",
    ]
    assert activities[0][1] == {"requestIndex": 1, "inputItemCount": 1}
    assert activities[1][1]["responseId"] == "resp-1"
    assert activities[1][1]["usage"] == {
        "requests": 1,
        "inputTokens": 20,
        "outputTokens": 5,
        "totalTokens": 25,
    }
    assert activities[2][1] == {"tool": "choose_house", "sequence": 1}
    assert activities[3][1]["tool"] == "choose_house"
    assert activities[3][1]["sequence"] == 1
    assert activities[1][1]["durationMs"] >= 0
    assert activities[3][1]["durationMs"] >= 0
    serialized = json.dumps(activities)
    assert OBSERVATION_INPUT_PREFIX not in serialized
    assert "private-api-key" not in serialized
    assert "private-game-password" not in serialized
    assert "house_id" not in serialized
    assert '"result"' not in serialized


@pytest.mark.asyncio
async def test_tool_validation_error_can_be_corrected_in_the_same_run(
    monkeypatch,
) -> None:
    fake_model = CorrectingToolCallingModel()
    monkeypatch.setattr(
        "raven_harness.models.openai_agent._response_model",
        lambda **_kwargs: fake_model,
    )
    record = AgentRecord.from_create(
        AgentCreate(name="Wolf", user_id="2", auth_token="secret")
    )
    client = FakeClient()
    context = HarnessRunContext(client=client, user_id="2", game_password="wolf")
    arguments = turn_arguments(record, context)
    arguments["max_turns"] = 3

    result = await OpenAIAgentRunner(
        api_key="test-key", base_url="https://api.openai.test/v1"
    ).run_once(**arguments)

    assert fake_model.call_count == 2
    assert "must be one of" in json.dumps(fake_model.inputs[1])
    assert result.response_id == "correcting-response-2"
    assert context.action_taken is not None
    assert context.action_taken.arguments == {"house_id": "stark"}
    assert client.sent == [
        {"type": "choose-house", "house": "stark", "password": "wolf"}
    ]


@pytest.mark.asyncio
async def test_turn_limit_error_preserves_the_last_tool_validation_error(
    monkeypatch,
) -> None:
    fake_model = RepeatingInvalidToolCallingModel()
    monkeypatch.setattr(
        "raven_harness.models.openai_agent._response_model",
        lambda **_kwargs: fake_model,
    )
    record = AgentRecord.from_create(
        AgentCreate(name="Wolf", user_id="2", auth_token="secret")
    )
    context = HarnessRunContext(
        client=FakeClient(), user_id="2", game_password="wolf"
    )
    arguments = turn_arguments(record, context)
    arguments["max_turns"] = 2

    with pytest.raises(ModelRunError, match="last tool error:.*must be one of"):
        await OpenAIAgentRunner(
            api_key="test-key", base_url="https://api.openai.test/v1"
        ).run_once(**arguments)

    assert fake_model.call_count == 2
    assert context.last_tool_error is not None
    assert "must be one of" in context.last_tool_error


@pytest.mark.asyncio
async def test_failed_model_run_does_not_send_an_action(monkeypatch) -> None:
    monkeypatch.setattr(
        "raven_harness.models.openai_agent._response_model",
        lambda **_kwargs: FailingModel(),
    )
    record = AgentRecord.from_create(
        AgentCreate(name="Wolf", user_id="2", auth_token="secret")
    )
    client = FakeClient()
    context = HarnessRunContext(client=client, user_id="2", game_password="wolf")
    with pytest.raises(ModelRunError, match="provider failed") as raised:
        await OpenAIAgentRunner(
            api_key="test-key", base_url="https://api.openai.test/v1"
        ).run_once(**turn_arguments(record, context))

    assert client.sent == []
    assert context.action_taken is None
    assert raised.value.partial_result.context_manifest["policy"] == CONTEXT_POLICY_NAME
    assert raised.value.partial_result.context_manifest["currentInputItemCount"] == 1


@pytest.mark.asyncio
async def test_quota_error_is_terminal_and_redacted(monkeypatch) -> None:
    monkeypatch.setattr(
        "raven_harness.models.openai_agent._response_model",
        lambda **_kwargs: QuotaFailingModel(),
    )
    record = AgentRecord.from_create(
        AgentCreate(name="Wolf", user_id="2", auth_token="secret")
    )
    context = HarnessRunContext(client=FakeClient(), user_id="2")

    with pytest.raises(PermanentModelError) as raised:
        await OpenAIAgentRunner(
            api_key="test-key", base_url="https://api.openai.test/v1"
        ).run_once(**turn_arguments(record, context))

    assert "spending limit exhausted" in str(raised.value)
    assert "private-key-id" not in str(raised.value)
    assert "[redacted]" in str(raised.value)


@pytest.mark.asyncio
async def test_cancelled_model_run_carries_the_context_manifest(monkeypatch) -> None:
    monkeypatch.setattr(
        "raven_harness.models.openai_agent._response_model",
        lambda **_kwargs: CancellingModel(),
    )
    record = AgentRecord.from_create(
        AgentCreate(name="Wolf", user_id="2", auth_token="secret")
    )
    client = FakeClient()
    context = HarnessRunContext(client=client, user_id="2", game_password="wolf")

    with pytest.raises(ModelRunCancelled) as raised:
        await OpenAIAgentRunner(
            api_key="test-key", base_url="https://api.openai.test/v1"
        ).run_once(**turn_arguments(record, context))

    manifest = raised.value.partial_result.context_manifest
    assert manifest["policy"] == CONTEXT_POLICY_NAME
    assert manifest["currentInputItemCount"] == 1
    assert manifest["retrievedHistoryItemCount"] == 0


@pytest.mark.asyncio
async def test_runner_filters_old_observations_without_purging_the_session(
    monkeypatch, tmp_path
) -> None:
    fake_model = ToolCallingModel()
    monkeypatch.setattr(
        "raven_harness.models.openai_agent._response_model",
        lambda **_kwargs: fake_model,
    )
    record = AgentRecord.from_create(
        AgentCreate(name="Wolf", user_id="2", auth_token="secret")
    )
    client = FakeClient()
    context = HarnessRunContext(client=client, user_id="2", game_password="wolf")
    database_path = tmp_path / "conversation.db"
    runner = OpenAIAgentRunner(
        api_key="test-key",
        base_url="https://api.openai.test/v1",
        session_database_path=database_path,
        session_history_items=12,
    )

    first_result = await runner.run_once(**turn_arguments(record, context))
    first_input = fake_model.inputs[0]

    client.snapshot = lobby_snapshot()
    second_context = HarnessRunContext(
        client=client, user_id="2", game_password="wolf"
    )
    second_result = await runner.run_once(**turn_arguments(record, second_context))
    second_input = fake_model.inputs[1]

    with sqlite3.connect(database_path) as connection:
        rows = connection.execute(
            "SELECT message_data FROM agent_messages ORDER BY id"
        ).fetchall()
    stored_items = [json.loads(row[0]) for row in rows]

    assert len(stored_items) == 6
    assert sum(
        OBSERVATION_INPUT_PREFIX in item.get("content", "")
        for item in stored_items
    ) == 2
    assert sum(
        OBSERVATION_INPUT_PREFIX in item.get("content", "") for item in second_input
    ) == 1
    assert second_input[0]["type"] == "function_call"
    assert second_input[0]["call_id"] == "call-1"
    assert second_input[1]["type"] == "function_call_output"
    assert second_input[1]["call_id"] == "call-1"
    assert second_input[2]["role"] == "user"
    assert second_input[2]["content"].startswith(OBSERVATION_INPUT_PREFIX)

    manifest = second_result.context_manifest
    assert manifest["policy"] == CONTEXT_POLICY_NAME
    assert manifest["sessionHistoryLimit"] == 12
    assert manifest["retrievedHistoryItemCount"] == 3
    assert manifest["discardedPrefixItemCount"] == 0
    assert manifest["removedObservationItemCount"] == 1
    assert manifest["removedObservationCharacters"] == len(first_input[0]["content"])
    assert manifest["removedSupportToolItemCount"] == 0
    assert manifest["removedSupportToolCharacters"] == 0
    assert manifest["selectedHistoryItems"] == second_input[:2]
    assert manifest["currentInputItemCount"] == 1
    assert manifest["currentInputCharacters"] == len(second_input[2]["content"])
    assert manifest["currentInputSha256"] == hashlib.sha256(
        second_input[2]["content"].encode("utf-8")
    ).hexdigest()
    assert "test-key" not in json.dumps(manifest)
    assert first_result.context_manifest["retrievedHistoryItemCount"] == 0
    await runner.shutdown()


def test_session_context_filter_discards_an_orphaned_history_prefix() -> None:
    old_observation = {
        "role": "user",
        "content": OBSERVATION_INPUT_PREFIX + '{"game":{"round":1}}',
    }
    orphaned_output = {
        "type": "function_call_output",
        "call_id": "orphaned-call",
        "output": '{"ok":true}',
    }
    retained_call = {
        "type": "function_call",
        "call_id": "complete-call",
        "name": "choose_house",
        "arguments": '{"house_id":"stark"}',
    }
    retained_reasoning = {
        "type": "reasoning",
        "id": "reasoning-1",
        "summary": [],
    }
    retained_output = {
        "type": "function_call_output",
        "call_id": "complete-call",
        "output": '{"ok":true}',
    }
    retained_message = {
        "type": "message",
        "role": "assistant",
        "content": [{"type": "output_text", "text": "Action completed."}],
    }
    second_old_observation = {
        "role": "user",
        "content": OBSERVATION_INPUT_PREFIX + '{"game":{"round":1,"phase":"action"}}',
    }
    current_input = OBSERVATION_INPUT_PREFIX + '{"game":{"round":2}}'
    new_items = [{"role": "user", "content": current_input}]
    context_filter = _SessionContextFilter(32, current_input)

    filtered = context_filter(
        [
            orphaned_output,
            old_observation,
            retained_reasoning,
            retained_call,
            retained_output,
            retained_message,
            second_old_observation,
        ],
        new_items,
    )

    assert filtered == [
        retained_reasoning,
        retained_call,
        retained_output,
        retained_message,
        *new_items,
    ]
    manifest = context_filter.manifest()
    assert manifest["retrievedHistoryItemCount"] == 7
    assert manifest["discardedPrefixItemCount"] == 1
    assert manifest["removedObservationItemCount"] == 2
    assert manifest["removedObservationCharacters"] == (
        len(old_observation["content"]) + len(second_old_observation["content"])
    )
    assert manifest["selectedHistoryItems"] == [
        retained_reasoning,
        retained_call,
        retained_output,
        retained_message,
    ]


def test_session_context_filter_removes_large_recall_and_support_outputs() -> None:
    observation = {
        "role": "user",
        "content": OBSERVATION_INPUT_PREFIX + '{"game":{"stateId":"old"}}',
    }
    recall_call = {
        "type": "function_call",
        "call_id": "recall-1",
        "name": "recall_game_state",
        "arguments": '{"turns_ago":1}',
    }
    recall_output = {
        "type": "function_call_output",
        "call_id": "recall-1",
        "output": json.dumps({"observation": "x" * 30_000}),
    }
    oracle_call = {
        "type": "function_call",
        "call_id": "oracle-1",
        "name": "ask_rules_oracle",
        "arguments": '{"question":"How does supply work?"}',
    }
    oracle_output = {
        "type": "function_call_output",
        "call_id": "oracle-1",
        "output": "A concise answer.",
    }
    game_call = {
        "type": "function_call",
        "call_id": "game-1",
        "name": "resolve_march",
        "arguments": '{"starting_region_id":"winterfell","moves":[]}',
    }
    game_output = {
        "type": "function_call_output",
        "call_id": "game-1",
        "output": '{"ok":true}',
    }
    current_input = OBSERVATION_INPUT_PREFIX + '{"game":{"stateId":"current"}}'
    context_filter = _SessionContextFilter(32, current_input)

    filtered = context_filter(
        [
            observation,
            recall_call,
            recall_output,
            oracle_call,
            oracle_output,
            game_call,
            game_output,
        ],
        [{"role": "user", "content": current_input}],
    )

    serialized = json.dumps(filtered, separators=(",", ":"))
    assert "x" * 100 not in serialized
    assert "recall_game_state" not in serialized
    assert "ask_rules_oracle" not in serialized
    assert filtered[:2] == [game_call, game_output]
    manifest = context_filter.manifest()
    assert manifest["removedSupportToolItemCount"] == 4
    assert manifest["removedSupportToolCharacters"] > 30_000


@pytest.mark.asyncio
async def test_failed_strategy_note_is_not_replayed_on_the_next_run(
    monkeypatch, tmp_path
) -> None:
    failing_model = RememberThenFailModel()
    current_model: Model = failing_model
    monkeypatch.setattr(
        "raven_harness.models.openai_agent._response_model",
        lambda **_kwargs: current_model,
    )
    record = AgentRecord.from_create(
        AgentCreate(name="Wolf", user_id="2", auth_token="secret")
    )
    database_path = tmp_path / "failed-note.db"
    runner = OpenAIAgentRunner(
        api_key="test-key",
        base_url="https://api.openai.test/v1",
        session_database_path=database_path,
    )
    first_context = HarnessRunContext(
        client=FakeClient(), user_id="2", game_password="wolf"
    )
    tools = [
        *available_tools(first_context.current_game_context()),
        remember_strategy,
    ]
    first_arguments = turn_arguments(record, first_context)
    first_arguments["tools"] = tools
    first_arguments["max_turns"] = 3

    with pytest.raises(ModelRunError, match="provider failed after note") as raised:
        await runner.run_once(**first_arguments)

    partial = raised.value.partial_result
    assert partial.usage == {
        "requests": 1,
        "inputTokens": 20,
        "outputTokens": 5,
        "totalTokens": 25,
    }
    assert partial.raw_usage == [
        {"scope": "agent", "response_id": "remember-response"}
    ]
    assert partial.response_items[0]["type"] == "partial_model_response"
    assert partial.response_items[0]["responseId"] == "remember-response"

    with sqlite3.connect(database_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM agent_messages").fetchone() == (
            0,
        )

    successful_model = ToolCallingModel(["choose_house", "remember_strategy"])
    current_model = successful_model
    second_context = HarnessRunContext(
        client=FakeClient(), user_id="2", game_password="wolf"
    )
    second_arguments = turn_arguments(record, second_context)
    second_arguments["tools"] = tools
    result = await runner.run_once(**second_arguments)

    serialized_input = json.dumps(successful_model.inputs[0], separators=(",", ":"))
    assert "Uncommitted northern plan" not in serialized_input
    assert "remember_strategy" not in serialized_input
    assert result.context_manifest["retrievedHistoryItemCount"] == 0
    assert result.context_manifest["removedSupportToolItemCount"] == 0
    await runner.shutdown()


@pytest.mark.asyncio
async def test_runner_restores_session_to_the_pre_model_checkpoint(
    monkeypatch, tmp_path
) -> None:
    model = ToolCallingModel()
    monkeypatch.setattr(
        "raven_harness.models.openai_agent._response_model",
        lambda **_kwargs: model,
    )
    database_path = tmp_path / "checkpoint.db"
    database = Database(database_path)
    store = AgentStore(database)
    record = store.create_agent(
        AgentCreate(name="Wolf", user_id="2", auth_token="secret")
    )
    session = SQLiteSession(
        session_id=f"raven-agent-{record.id}", db_path=database_path
    )
    kept_items = [
        {"role": "assistant", "content": f"keep-{index}"}
        for index in range(40)
    ]
    await session.add_items(kept_items)
    store.set_agent_checkpoint(
        agent_id=record.id,
        state_id="leaf-1",
        observation={
            "game": {"stateId": "leaf-1"},
            "recoveryMarker": "exact saved observation",
        },
        session_item_count=len(kept_items),
        run_id="interrupted-run",
        phase="before-model",
    )
    await session.add_items(
        [{"role": "user", "content": "discard interrupted model input"}]
    )
    session.close()

    runner = OpenAIAgentRunner(
        api_key="test-key",
        base_url="https://api.openai.test/v1",
        session_database_path=database_path,
        checkpoint_store=store,
    )
    context = HarnessRunContext(
        client=FakeClient(), user_id="2", game_password="wolf"
    )
    await runner.run_once(**turn_arguments(record, context))

    with sqlite3.connect(database_path) as connection:
        persisted_items = "\n".join(
            row[0]
            for row in connection.execute(
                "SELECT message_data FROM agent_messages ORDER BY id"
            )
        )
    assert "keep-0" in persisted_items
    assert "keep-39" in persisted_items
    assert "discard interrupted model input" not in persisted_items
    assert "exact saved observation" in json.dumps(model.inputs[0])
    checkpoint = store.get_agent_checkpoint(record.id)
    assert checkpoint is not None
    assert checkpoint["phase"] == "after-action"
    assert checkpoint["sessionItemCount"] > len(kept_items)
    await runner.shutdown()
    database.close()


def test_session_context_filter_plateaus_across_one_hundred_decisions() -> None:
    history_limit = 32
    stored_history: list[dict[str, Any]] = []
    effective_sizes: list[int] = []

    for decision in range(100):
        current_input = (
            OBSERVATION_INPUT_PREFIX
            + json.dumps(
                {
                    "game": {"stateId": f"state-{decision}"},
                    "board": "x" * 30_000,
                },
                separators=(",", ":"),
            )
        )
        new_items = [{"role": "user", "content": current_input}]
        context_filter = _SessionContextFilter(history_limit, current_input)
        effective_input = context_filter(stored_history[-history_limit:], new_items)

        serialized_input = json.dumps(effective_input, separators=(",", ":"))
        effective_sizes.append(len(serialized_input))
        effective_text = "\n".join(
            content
            for item in effective_input
            if isinstance((content := item.get("content")), str)
        )
        assert effective_text.count(OBSERVATION_INPUT_PREFIX) == 1
        if decision:
            assert f'"stateId":"state-{decision - 1}"' not in effective_text

        call_id = f"call-{decision}"
        stored_history.extend(
            [
                *new_items,
                {
                    "type": "reasoning",
                    "id": f"reasoning-{decision}",
                    "summary": [],
                },
                {
                    "type": "function_call",
                    "call_id": call_id,
                    "name": "resolve_march",
                    "arguments": '{"option_id":"march-1"}',
                },
                {
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": '{"ok":true}',
                },
            ]
        )

    assert len(stored_history) == 400
    assert len(set(effective_sizes[20:])) == 1
    assert effective_sizes[-1] < 35_000
