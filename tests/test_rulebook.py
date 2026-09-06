from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest
from agents import ModelResponse, Usage
from agents.models.interface import Model
from openai.types.responses import (
    ResponseFunctionToolCall,
    ResponseOutputMessage,
    ResponseOutputText,
)

from raven_harness.agent_store import AgentStore
from raven_harness.database import Database
from raven_harness.harness.actions import HarnessRunContext
from raven_harness.harness.observation import build_context
from raven_harness.harness.strategic import StrategicHarness
from raven_harness.models.openai_agent import OpenAIAgentRunner
from raven_harness.rulebook import (
    RuleSection,
    RuleSectionId,
    RuleSource,
    Rulebook,
    RulebookData,
)
from raven_harness.schemas import AgentCreate

from conftest import lobby_snapshot


def sample_rulebook() -> Rulebook:
    return Rulebook(
        RulebookData(
            generated_at="2026-01-01T00:00:00+00:00",
            sources=[
                RuleSource(
                    id="rules",
                    title="Official rules",
                    url="https://example.test/rules.pdf",
                    sha256="a" * 64,
                )
            ],
            sections=[
                RuleSection(
                    id=RuleSectionId.SUPPLY_AND_MUSTERING,
                    title="Supply and mustering",
                    summary="Supply limits and recruitment.",
                    source_id="rules",
                    pages=[8, 9],
                    text="Supply limits the number and size of armies, not total units.",
                )
            ],
        )
    )


class OracleThenActionModel(Model):
    def __init__(self) -> None:
        self.outer_calls = 0
        self.oracle_calls = 0

    async def get_response(self, *args: Any, **kwargs: Any) -> ModelResponse:
        names = {tool.name for tool in kwargs["tools"]}
        if names == {"read_rulebook_sections"}:
            self.oracle_calls += 1
            if self.oracle_calls == 1:
                output: Any = ResponseFunctionToolCall(
                    arguments='{"section_ids":["supply-and-mustering"]}',
                    call_id="read-rules",
                    name="read_rulebook_sections",
                    type="function_call",
                )
            else:
                output = ResponseOutputMessage(
                    id="oracle-answer",
                    content=[
                        ResponseOutputText(
                            annotations=[],
                            text=(
                                "Supply limits army sizes, not total units "
                                "(Supply and mustering, pages 8-9)."
                            ),
                            type="output_text",
                        )
                    ],
                    role="assistant",
                    status="completed",
                    type="message",
                )
        else:
            self.outer_calls += 1
            if self.outer_calls == 1:
                assert "ask_rules_oracle" in names
                output = ResponseFunctionToolCall(
                    arguments='{"question":"Does supply limit all of my units?"}',
                    call_id="ask-rules",
                    name="ask_rules_oracle",
                    type="function_call",
                )
            else:
                output = ResponseFunctionToolCall(
                    arguments='{"house_id":"stark"}',
                    call_id="choose-house",
                    name="choose_house",
                    type="function_call",
                )
        return ModelResponse(
            output=[output],
            usage=Usage(requests=1, input_tokens=20, output_tokens=5, total_tokens=25),
            response_id=f"response-{self.outer_calls}-{self.oracle_calls}",
        )

    async def stream_response(self, *args: Any, **kwargs: Any) -> AsyncIterator[Any]:
        if False:
            yield None


class FakeClient:
    def __init__(self) -> None:
        self.snapshot = lobby_snapshot()
        self.recent_events: list[dict[str, Any]] = []
        self.sent: list[dict[str, Any]] = []

    async def send(
        self, message: dict[str, Any], *, require_auth: bool = True
    ) -> None:
        self.sent.append(message)

    async def sync_snapshot(self, timeout: float = 10) -> dict[str, Any]:
        del timeout
        message = self.sent[-1]
        self.snapshot["childGameState"]["players"].append([message["house"], "2"])
        return self.snapshot


def test_rulebook_reads_only_named_sections() -> None:
    rulebook = sample_rulebook()

    assert rulebook.catalog()[0]["id"] == "supply-and-mustering"
    result = rulebook.read([RuleSectionId.SUPPLY_AND_MUSTERING])
    assert result[0]["pages"] == [8, 9]
    assert "not total units" in result[0]["text"]
    assert len(rulebook.cache_fingerprint) == 24


@pytest.mark.asyncio
async def test_rules_oracle_reads_a_section_then_returns_to_game_action(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    fake_model = OracleThenActionModel()
    monkeypatch.setattr(
        "raven_harness.models.openai_agent.OpenAIResponsesModel",
        lambda **_kwargs: fake_model,
    )
    database = Database(tmp_path / "oracle.db")
    store = AgentStore(database)
    record = store.create_agent(
        AgentCreate(name="Wolf", model="test-model", user_id="2", auth_token="x")
    )
    rulebook = sample_rulebook()
    harness = StrategicHarness(
        OpenAIAgentRunner(
            api_key="test-key",
            base_url="https://api.test/v1",
            rulebook=rulebook,
        ),
        store,
        rules_available=True,
    )
    client = FakeClient()
    prepared = harness.prepare_turn(
        record, build_context(client.snapshot, "2"), previous_error=None
    )
    context = HarnessRunContext(client=client, user_id="2")

    result = await harness.run_turn(record, prepared, context, "oracle-run")

    assert fake_model.outer_calls == 2
    assert fake_model.oracle_calls == 2
    assert context.action_taken is not None
    assert context.action_taken.name == "choose_house"
    oracle_trace = next(
        item for item in result.response_items if item.get("type") == "rules_oracle"
    )
    assert oracle_trace["sectionIds"] == ["supply-and-mustering"]
    assert "not total units" in oracle_trace["answer"]
    assert result.usage["totalTokens"] == 100
    database.close()
