from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agents import (
    Agent,
    FunctionTool,
    ModelSettings,
    OpenAIResponsesModel,
    RunConfig,
    Runner,
)
from agents.memory import Session, SessionSettings, SQLiteSession
from openai import APITimeoutError, AsyncOpenAI

from ..harness.actions import HarnessRunContext, available_tools
from ..rulebook import RULES_ORACLE_TOOL_NAME, Rulebook
from ..schemas import AgentRecord


@dataclass(frozen=True)
class ModelRunResult:
    response_id: str | None
    output_text: str
    usage: dict[str, int]
    response_items: list[dict[str, Any]]
    raw_usage: list[dict[str, Any]]


class OpenAIAgentRunner:
    """Runs one Agents SDK turn with the currently legal game tools attached."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        request_timeout_seconds: float = 45,
        run_timeout_seconds: float = 300,
        max_retries: int = 2,
        max_concurrency: int = 1,
        max_output_tokens: int = 8_192,
        session_database_path: Path | None = None,
        session_history_items: int = 32,
        provider_routing: dict[str, Any] | None = None,
        rulebook: Rulebook | None = None,
    ) -> None:
        self.api_key = api_key
        self.request_timeout_seconds = request_timeout_seconds
        self.run_timeout_seconds = run_timeout_seconds
        self.max_retries = max_retries
        self._run_slots = asyncio.Semaphore(max_concurrency)
        self.max_output_tokens = max_output_tokens
        self.session_database_path = session_database_path
        self.session_history_items = session_history_items
        self._sessions: dict[str, SQLiteSession] = {}
        self.provider_routing = provider_routing
        self.rulebook = rulebook
        self.client = AsyncOpenAI(
            api_key=api_key or "not-configured",
            base_url=base_url,
            timeout=request_timeout_seconds,
            max_retries=max_retries,
        )

    async def run_once(
        self,
        *,
        agent_record: AgentRecord,
        observation: dict[str, Any],
        context: HarnessRunContext,
        tools: list[FunctionTool] | None = None,
        instructions: str | None = None,
        max_turns: int = 1,
        stop_at_tool_names: list[str] | None = None,
        prompt_cache_key: str | None = None,
        trace_metadata: dict[str, str] | None = None,
    ) -> ModelRunResult:
        if not self.api_key:
            raise RuntimeError(
                "OPENROUTER_TOKEN or OPENAI_API_KEY is not configured on the harness server"
            )

        if tools is None:
            tools = available_tools(context.current_game_context())
        if not tools:
            raise RuntimeError(
                "No model tool is implemented for the current game state"
            )

        model = OpenAIResponsesModel(model=agent_record.model, openai_client=self.client)
        oracle_interactions: list[dict[str, Any]] = []
        run_config = RunConfig(
            tracing_disabled=True,
            workflow_name="Raven Harness action",
            group_id=agent_record.id,
            trace_metadata=trace_metadata,
        )
        tools = [
            (
                self.rulebook.build_oracle_tool(
                    model=OpenAIResponsesModel(
                        model=agent_record.model, openai_client=self.client
                    ),
                    model_settings=self._model_settings(
                        max_tokens=900,
                        prompt_cache_key=(
                            f"raven-rules-{agent_record.model}-"
                            f"{self.rulebook.cache_fingerprint}"
                        ),
                        metadata=trace_metadata,
                    ),
                    interaction_sink=oracle_interactions,
                    run_config=run_config,
                )
                if tool.name == RULES_ORACLE_TOOL_NAME and self.rulebook is not None
                else tool
            )
            for tool in tools
        ]
        agent = Agent[HarnessRunContext](
            name=agent_record.name,
            instructions=instructions or agent_record.system_prompt,
            model=model,
            tools=tools,
            model_settings=self._model_settings(
                max_tokens=self.max_output_tokens,
                prompt_cache_key=prompt_cache_key,
                metadata=trace_metadata,
                user=agent_record.id,
            ),
            tool_use_behavior=(
                {"stop_at_tool_names": stop_at_tool_names}
                if stop_at_tool_names
                else "stop_on_first_tool"
            ),
            reset_tool_choice=not bool(stop_at_tool_names),
        )
        try:
            async with self._run_slots:
                async with asyncio.timeout(self.run_timeout_seconds):
                    result = await Runner.run(
                        agent,
                        input=(
                            "This is your current player-scoped game observation. "
                            "Choose exactly one available tool.\n\n"
                            + json.dumps(observation, separators=(",", ":"))
                        ),
                        context=context,
                        max_turns=max_turns,
                        run_config=run_config,
                        session=self._session(agent_record.id),
                    )
        except TimeoutError as error:
            raise RuntimeError(
                f"Model run exceeded {self.run_timeout_seconds:g} seconds total"
            ) from error
        except APITimeoutError as error:
            raise RuntimeError(
                "Model API timed out after "
                f"{self.request_timeout_seconds:g} seconds per attempt and "
                f"{self.max_retries} retries"
            ) from error

        total_usage = result.context_wrapper.usage
        usage = {
            "requests": total_usage.requests,
            "inputTokens": total_usage.input_tokens,
            "outputTokens": total_usage.output_tokens,
            "totalTokens": total_usage.total_tokens,
        }
        response_items = [_jsonable(item.to_input_item()) for item in result.new_items]
        raw_usage: list[dict[str, Any]] = []
        for response in result.raw_responses:
            if response.raw_usage is not None:
                raw_usage.append(_jsonable(response.raw_usage))
        for interaction in oracle_interactions:
            response_items.append(
                {
                    "type": "rules_oracle",
                    "question": interaction["question"],
                    "answer": interaction["answer"],
                    "sectionIds": interaction["sectionIds"],
                    "responseItems": interaction["responseItems"],
                }
            )
            raw_usage.extend(interaction["rawUsage"])
        return ModelRunResult(
            response_id=result.last_response_id,
            output_text=str(result.final_output or ""),
            usage=usage,
            response_items=response_items,
            raw_usage=raw_usage,
        )

    def _session(self, agent_id: str) -> Session | None:
        if self.session_database_path is None:
            return None
        session = self._sessions.get(agent_id)
        if session is None:
            session = SQLiteSession(
                session_id=f"raven-agent-{agent_id}",
                db_path=self.session_database_path,
                session_settings=SessionSettings(limit=self.session_history_items),
            )
            self._sessions[agent_id] = session
        return session

    async def shutdown(self) -> None:
        for session in self._sessions.values():
            session.close()
        self._sessions.clear()
        await self.client.close()

    async def clear_session(self, agent_id: str) -> None:
        if self.session_database_path is None:
            return
        session = self._sessions.pop(agent_id, None)
        if session is None:
            session = SQLiteSession(
                session_id=f"raven-agent-{agent_id}",
                db_path=self.session_database_path,
            )
        try:
            await session.clear_session()
        finally:
            session.close()

    def _model_settings(
        self,
        *,
        max_tokens: int,
        prompt_cache_key: str | None,
        metadata: dict[str, str] | None,
        user: str | None = None,
    ) -> ModelSettings:
        return ModelSettings(
            tool_choice="required",
            parallel_tool_calls=False,
            max_tokens=max_tokens,
            reasoning={"effort": "low"},
            store=False,
            metadata=metadata,
            preserve_raw_usage=True,
            extra_body=(
                {"provider": self.provider_routing}
                if self.provider_routing
                else None
            ),
            extra_args=(
                {
                    "prompt_cache_key": prompt_cache_key,
                    **({"user": user} if user else {}),
                }
                if prompt_cache_key
                else None
            ),
        )


def _jsonable(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", exclude_none=True)
    if isinstance(value, dict):
        return value
    return {"value": str(value)}
