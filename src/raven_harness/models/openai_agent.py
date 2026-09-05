from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any

from agents import (
    Agent,
    FunctionTool,
    ModelSettings,
    OpenAIResponsesModel,
    RunConfig,
    Runner,
)
from openai import AsyncOpenAI

from ..harness.actions import HarnessRunContext, available_tools
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
        request_timeout_seconds: float = 90,
        max_output_tokens: int = 8_192,
    ) -> None:
        self.api_key = api_key
        self.request_timeout_seconds = request_timeout_seconds
        self.max_output_tokens = max_output_tokens
        self.client = AsyncOpenAI(
            api_key=api_key or "not-configured",
            base_url=base_url,
            timeout=request_timeout_seconds,
            max_retries=1,
        )

    async def run_once(
        self,
        *,
        agent_record: AgentRecord,
        observation: dict[str, Any],
        context: HarnessRunContext,
        tools: list[FunctionTool] | None = None,
        instructions: str | None = None,
        session: Any | None = None,
        max_turns: int = 1,
        stop_at_tool_names: list[str] | None = None,
        prompt_cache_key: str | None = None,
        trace_metadata: dict[str, str] | None = None,
    ) -> ModelRunResult:
        if not self.api_key:
            raise RuntimeError(
                "OPENROUTER_TOKEN or OPENAI_API_KEY is not configured on the harness server"
            )

        tools = tools or available_tools(context.current_game_context())
        if not tools:
            raise RuntimeError(
                "No model tool is implemented for the current game state"
            )

        model = OpenAIResponsesModel(
            model=agent_record.model, openai_client=self.client
        )
        agent = Agent[HarnessRunContext](
            name=agent_record.name,
            instructions=instructions or agent_record.system_prompt,
            model=model,
            tools=tools,
            model_settings=ModelSettings(
                tool_choice="required",
                parallel_tool_calls=False,
                max_tokens=self.max_output_tokens,
                reasoning={"effort": "low"},
                store=False,
                metadata=trace_metadata,
                preserve_raw_usage=True,
                extra_args=(
                    {
                        "prompt_cache_key": prompt_cache_key,
                        "user": agent_record.id,
                    }
                    if prompt_cache_key
                    else None
                ),
            ),
            tool_use_behavior=(
                {"stop_at_tool_names": stop_at_tool_names}
                if stop_at_tool_names
                else "stop_on_first_tool"
            ),
            reset_tool_choice=not bool(stop_at_tool_names),
        )
        try:
            async with asyncio.timeout(self.request_timeout_seconds):
                result = await Runner.run(
                    agent,
                    input=(
                        "This is your current player-scoped game observation. "
                        "Choose exactly one available tool.\n\n"
                        + json.dumps(observation, separators=(",", ":"))
                    ),
                    context=context,
                    max_turns=max_turns,
                    session=session,
                    run_config=RunConfig(
                        tracing_disabled=True,
                        workflow_name="Raven Harness action",
                        group_id=agent_record.id,
                        trace_metadata=trace_metadata,
                    ),
                )
        except TimeoutError as error:
            raise RuntimeError(
                f"Model turn exceeded {self.request_timeout_seconds:g} seconds"
            ) from error

        usage = {"requests": 0, "inputTokens": 0, "outputTokens": 0, "totalTokens": 0}
        response_items: list[dict[str, Any]] = []
        raw_usage: list[dict[str, Any]] = []
        for response in result.raw_responses:
            usage["requests"] += response.usage.requests
            usage["inputTokens"] += response.usage.input_tokens
            usage["outputTokens"] += response.usage.output_tokens
            usage["totalTokens"] += response.usage.total_tokens
            response_items.extend(_jsonable(item) for item in response.output)
            if response.raw_usage is not None:
                raw_usage.append(_jsonable(response.raw_usage))
        return ModelRunResult(
            response_id=result.last_response_id,
            output_text=str(result.final_output or ""),
            usage=usage,
            response_items=response_items,
            raw_usage=raw_usage,
        )


def _jsonable(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", exclude_none=True)
    if isinstance(value, dict):
        return value
    return {"value": str(value)}
