"""One gameplay pipeline; only the injected execution loop varies."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from agents import Agent, FunctionTool, ModelSettings, RunConfig

from ..agent_store import AgentStore
from ..errors import is_permanent_provider_error, safe_error_text
from ..game.client import GameConnectionLost
from ..models.providers import ResponseProvider
from ..models.results import (
    ModelRunCancelled,
    ModelRunError,
    ModelRunResult,
    PermanentModelError,
    TransientProviderCapacityError,
    _caused_by_connection_loss,
)
from ..models.tracing import RunTrace
from ..rulebook import RULES_ORACLE_TOOL_NAME, Rulebook
from ..schemas import AgentRecord
from .actions import HarnessRunContext
from .execution import Harness, Turn
from .interface import PreparedTurn
from .memory import PersistentGameMemory, _automatic_notes
from .observation import HarnessContext
from .preparation import DecisionPreparation


@dataclass
class GameHarness:
    store: AgentStore
    provider: ResponseProvider
    execution_factory: Callable[
        [Callable[[], Agent[HarnessRunContext]]], Harness[HarnessRunContext]
    ]
    completion_instructions: str
    rulebook: Rulebook | None = None
    max_output_tokens: int | None = None
    preparation: DecisionPreparation = field(init=False)

    def __post_init__(self) -> None:
        self.preparation = DecisionPreparation(self.store, self.rulebook is not None)

    def preview_tools(self, context: HarnessContext) -> list[FunctionTool]:
        return self.preparation.preview_tools(context)

    def preview_observation(
        self, record: AgentRecord, context: HarnessContext
    ) -> dict[str, Any]:
        return self.preparation.preview_observation(record, context)

    def prepare_turn(
        self, record: AgentRecord, context: HarnessContext, previous_error: str | None
    ) -> PreparedTurn:
        return self.preparation.prepare_turn(record, context, previous_error)

    async def run_turn(
        self,
        record: AgentRecord,
        prepared: PreparedTurn,
        context: HarnessRunContext,
        run_id: str,
    ) -> ModelRunResult:
        if prepared.decision is None:
            raise ValueError("A game turn requires a decision")
        context.memory = PersistentGameMemory(self.store, record.id)
        context.decision = prepared.decision
        observation = dict(prepared.observation)
        briefing = observation.pop("decisionBriefing")
        current_input = (
            "Read the current board state, then follow the decision instructions below."
            "\n\nCurrent observation:\n"
            + json.dumps(observation, separators=(",", ":"))
            + "\n\nCurrent decision:\n"
            + briefing
            + "\n\nHow to complete this decision:\n"
            + self.completion_instructions
        )
        trace = RunTrace(current_input, prepared.decision.output_schema.json_schema())
        metadata = {"agent_id": record.id, "game_id": record.game_id, "run_id": run_id}
        config = RunConfig(
            tracing_disabled=True,
            workflow_name="Raven Harness action",
            group_id=record.id,
            trace_metadata=metadata,
            call_model_input_filter=trace.input_recorder,
        )
        try:
            if not self.provider.configured:
                raise RuntimeError(
                    "OPENROUTER_TOKEN or OPENAI_API_KEY is not configured"
                )
            model = trace.model(record.model, self.provider.client)
            settings = self.model_settings(
                max_tokens=self.max_output_tokens,
                prompt_cache_key=prepared.prompt_cache_key,
                metadata=metadata,
                user=record.id,
            )
            tools = [
                self.rulebook.build_oracle_tool(
                    model=trace.model(
                        record.model, self.provider.client, scope="rules-oracle"
                    ),
                    model_settings=self.model_settings(
                        max_tokens=900,
                        prompt_cache_key=f"raven-rules-{record.model}-{self.rulebook.cache_fingerprint}",
                        metadata=metadata,
                        user=record.id,
                    ),
                    interaction_sink=trace.oracle_interactions,
                    run_config=config,
                    hooks=trace.hooks,
                )
                if tool.name == RULES_ORACLE_TOOL_NAME and self.rulebook
                else tool
                for tool in prepared.tools
            ]

            def create_agent() -> Agent[HarnessRunContext]:
                return trace.bind(
                    Agent(
                        name=record.name,
                        model=model,
                        instructions=prepared.instructions,
                        model_settings=settings,
                    )
                )

            answer = await self.execution_factory(create_agent).run(
                Turn(
                    messages=current_input,
                    context=context,
                    tools=tools,
                    output_type=prepared.decision.output_schema,
                    run_config=config,
                    hooks=trace.hooks,
                    on_result=trace.results.append,
                )
            )
            await prepared.decision.execute(context, answer)
            context.memory.set_notes(
                _automatic_notes(record, prepared, context, context.memory.get_notes())
            )
            return trace.complete()
        except asyncio.CancelledError as error:
            raise ModelRunCancelled(trace.partial()) from error
        except GameConnectionLost:
            raise
        except Exception as error:
            connection_error = _caused_by_connection_loss(error)
            if connection_error is not None:
                raise connection_error from error
            if is_permanent_provider_error(error):
                error_type = PermanentModelError
            elif getattr(error, "status_code", None) in {429, 503}:
                error_type = TransientProviderCapacityError
            else:
                error_type = ModelRunError
            message = safe_error_text(error)
            if context.last_tool_error:
                message += "; last tool error: " + safe_error_text(
                    context.last_tool_error
                )
            raise error_type(message, trace.partial()) from None

    def model_settings(
        self,
        *,
        max_tokens: int | None,
        prompt_cache_key: str,
        metadata: dict[str, str],
        user: str | None = None,
    ) -> ModelSettings:
        return ModelSettings(
            tool_choice="auto",
            parallel_tool_calls=False,
            max_tokens=max_tokens,
            reasoning={"effort": "high"},
            store=False,
            metadata=metadata,
            preserve_raw_usage=True,
            extra_body=self.provider.request_extra_body(user=user) or None,
            extra_args={
                "prompt_cache_key": prompt_cache_key,
                **({"user": user} if user else {}),
            }
            if prompt_cache_key
            else None,
        )

    async def shutdown(self) -> None:
        await self.provider.client.close()
