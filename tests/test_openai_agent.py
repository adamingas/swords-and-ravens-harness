from collections.abc import AsyncIterator
from typing import Any

import pytest
from agents import ModelResponse, Usage
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
    async def get_response(self, *args, **kwargs) -> ModelResponse:
        tools = kwargs["tools"]
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

    result = await OpenAIAgentRunner(
        api_key="test-key", base_url="https://api.openai.test/v1"
    ).run_once(agent_record=record, observation=observation, context=context)

    assert result.response_id == "resp-1"
    assert result.usage["totalTokens"] == 25
    assert context.action_taken is not None
    assert context.action_taken.name == "choose_house"
    assert client.sent == [
        {"type": "choose-house", "house": "stark", "password": "wolf"}
    ]
