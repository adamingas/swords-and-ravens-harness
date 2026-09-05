from collections.abc import AsyncIterator
from typing import Any

import pytest
from agents import ModelResponse, SQLiteSession, Usage
from agents.models.interface import Model
from openai.types.responses import ResponseFunctionToolCall

from raven_harness.harness.actions import HarnessRunContext
from raven_harness.harness.observation import build_context, build_observation
from raven_harness.models.openai_agent import OpenAIAgentRunner
from raven_harness.schemas import AgentCreate, AgentRecord

from conftest import lobby_snapshot


class FakeClient:
    def __init__(self) -> None:
        self.snapshot = lobby_snapshot()
        self.recent_events: list[dict[str, Any]] = []
        self.sent: list[dict[str, Any]] = []

    async def send(self, message: dict[str, Any], *, require_auth: bool = True) -> None:
        self.sent.append(message)


class ToolCallingModel(Model):
    model_settings: Any = None

    async def get_response(self, *args, **kwargs) -> ModelResponse:
        tools = kwargs["tools"]
        self.model_settings = kwargs["model_settings"]
        assert [tool.name for tool in tools] == ["choose_house"]
        return ModelResponse(
            output=[
                ResponseFunctionToolCall(
                    arguments='{"house_id":"stark"}',
                    call_id="call-1",
                    name="choose_house",
                    type="function_call",
                )
            ],
            usage=Usage(requests=1, input_tokens=20, output_tokens=5, total_tokens=25),
            response_id="resp-1",
        )

    async def stream_response(self, *args, **kwargs) -> AsyncIterator[Any]:
        if False:
            yield None


class FailingModel(Model):
    async def get_response(self, *args, **kwargs) -> ModelResponse:
        raise RuntimeError("provider failed")

    async def stream_response(self, *args, **kwargs) -> AsyncIterator[Any]:
        if False:
            yield None


@pytest.mark.asyncio
async def test_openai_runner_attaches_and_executes_agents_sdk_tools(
    monkeypatch,
) -> None:
    fake_model = ToolCallingModel()
    monkeypatch.setattr(
        "raven_harness.models.openai_agent.OpenAIResponsesModel",
        lambda **_kwargs: fake_model,
    )
    record = AgentRecord.from_create(
        AgentCreate(name="Wolf", user_id="2", auth_token="secret")
    )
    client = FakeClient()
    context = HarnessRunContext(client=client, user_id="2", game_password="wolf")
    observation = build_observation(build_context(client.snapshot, "2"))

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
    result = await runner.run_once(
        agent_record=record, observation=observation, context=context
    )

    assert result.response_id == "resp-1"
    assert result.usage["totalTokens"] == 25
    assert context.action_taken is not None
    assert context.action_taken.name == "choose_house"
    assert runner.client.max_retries == 4
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
async def test_failed_model_run_rolls_back_session_input(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        "raven_harness.models.openai_agent.OpenAIResponsesModel",
        lambda **_kwargs: FailingModel(),
    )
    record = AgentRecord.from_create(
        AgentCreate(name="Wolf", user_id="2", auth_token="secret")
    )
    client = FakeClient()
    context = HarnessRunContext(client=client, user_id="2", game_password="wolf")
    session = SQLiteSession("rollback", db_path=tmp_path / "session.db")
    original = {"role": "user", "content": "an earlier retained item"}
    await session.add_items([original])

    with pytest.raises(RuntimeError, match="provider failed"):
        await OpenAIAgentRunner(
            api_key="test-key", base_url="https://api.openai.test/v1"
        ).run_once(
            agent_record=record,
            observation=build_observation(build_context(client.snapshot, "2")),
            context=context,
            session=session,
        )

    assert await session.get_items(limit=-1) == [original]
    session.close()
