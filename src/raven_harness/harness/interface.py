from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from agents import FunctionTool

from ..models.openai_agent import ModelRunResult
from ..schemas import AgentRecord
from .actions import HarnessRunContext
from .decision import DecisionContract
from .observation import HarnessContext


@dataclass
class PreparedTurn:
    observation: dict[str, Any]
    tools: list[FunctionTool]
    instructions: str
    prompt_cache_key: str
    history_id: int | None = None
    decision: DecisionContract | None = None


@runtime_checkable
class PlayerHarness(Protocol):
    """Canonical interface between game state, model execution, and persistence."""

    def preview_observation(
        self, record: AgentRecord, context: HarnessContext
    ) -> dict[str, Any]: ...

    def preview_tools(self, context: HarnessContext) -> list[FunctionTool]: ...

    def prepare_turn(
        self,
        record: AgentRecord,
        context: HarnessContext,
        previous_error: str | None,
    ) -> PreparedTurn: ...

    async def run_turn(
        self,
        record: AgentRecord,
        prepared: PreparedTurn,
        context: HarnessRunContext,
        run_id: str,
    ) -> ModelRunResult: ...

    async def shutdown(self) -> None: ...
