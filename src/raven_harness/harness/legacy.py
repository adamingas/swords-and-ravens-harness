from __future__ import annotations

from typing import Protocol

from agents import FunctionTool

from ..models.openai_agent import ModelRunResult
from ..schemas import AgentRecord
from .actions import HarnessRunContext, available_tools
from .interface import HarnessInfo, PreparedTurn
from .observation import HarnessContext, build_observation


class LegacyModelRunner(Protocol):
    async def run_once(
        self,
        *,
        agent_record: AgentRecord,
        observation: dict,
        context: HarnessRunContext,
        tools: list[FunctionTool] | None = None,
        **options: object,
    ) -> ModelRunResult: ...


class LegacyHarness:
    """The original stateless, one-model-call-per-action harness."""

    info = HarnessInfo(
        id="legacy",
        name="Legacy stateless",
        description="One fresh model call per action with current state only.",
    )

    def __init__(self, runner: LegacyModelRunner) -> None:
        self.runner = runner

    def preview_observation(self, record: AgentRecord, context: HarnessContext) -> dict:
        del record
        return build_observation(context)

    def prepare_turn(
        self,
        record: AgentRecord,
        context: HarnessContext,
        previous_error: str | None,
    ) -> PreparedTurn:
        observation = self.preview_observation(record, context)
        if previous_error:
            observation["previousAttemptError"] = previous_error
        return PreparedTurn(
            observation=observation,
            tools=self.preview_tools(record, context),
            instructions=record.system_prompt,
        )

    def preview_tools(
        self, record: AgentRecord, context: HarnessContext
    ) -> list[FunctionTool]:
        del record
        return available_tools(context)

    async def run_turn(
        self,
        record: AgentRecord,
        prepared: PreparedTurn,
        context: HarnessRunContext,
        run_id: str,
    ) -> ModelRunResult:
        del run_id
        return await self.runner.run_once(
            agent_record=record,
            observation=prepared.observation,
            context=context,
            tools=prepared.tools,
            instructions=prepared.instructions,
        )

    async def shutdown(self) -> None:
        return None
