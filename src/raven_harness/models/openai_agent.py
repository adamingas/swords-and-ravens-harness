from __future__ import annotations

import asyncio
import copy
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from time import monotonic
from typing import Any

from agents import (
    Agent,
    FunctionTool,
    ModelSettings,
    OpenAIResponsesModel,
    RunConfig,
    RunHooks,
    Runner,
    ToolsToFinalOutputResult,
)
from agents.memory import Session, SessionSettings, SQLiteSession
from agents.run_config import CallModelData, ModelInputData
from openai import APITimeoutError, AsyncOpenAI

from ..errors import is_permanent_provider_error, safe_error_text
from ..harness.actions import HarnessRunContext
from ..rulebook import RULES_ORACLE_TOOL_NAME, Rulebook
from ..schemas import AgentRecord


OBSERVATION_INPUT_PREFIX = (
    "This is your current player-scoped game observation. "
    "Choose exactly one available tool.\n\n"
)
CONTEXT_POLICY_NAME = "current-observation-with-recent-game-actions-v1"
TRANSIENT_SUPPORT_TOOL_NAMES = {
    "ask_rules_oracle",
    "recall_game_state",
    "remember_strategy",
}


def _stop_after_accepted_action(
    gameplay_tool_names: list[str],
):
    """Keep tool errors in the same model run and stop after an accepted action."""

    allowed = set(gameplay_tool_names)

    def behavior(context_wrapper: Any, tool_results: list[Any]) -> ToolsToFinalOutputResult:
        action = context_wrapper.context.action_taken
        if action is None or action.name not in allowed:
            return ToolsToFinalOutputResult(is_final_output=False, final_output=None)
        matching_result = next(
            (
                result
                for result in tool_results
                if result.tool.name == action.name
                or result.tool.qualified_name == action.name
            ),
            None,
        )
        return ToolsToFinalOutputResult(
            is_final_output=True,
            final_output=(
                matching_result.output
                if matching_result is not None
                else json.dumps(
                    {"ok": True, "accepted": True, "action": action.name},
                    separators=(",", ":"),
                )
            ),
        )

    return behavior


@dataclass(frozen=True)
class ModelRunResult:
    response_id: str | None
    output_text: str
    usage: dict[str, int]
    response_items: list[dict[str, Any]]
    raw_usage: list[dict[str, Any]]
    context_manifest: dict[str, Any] = field(default_factory=dict)


@dataclass
class _SessionContextFilter:
    session_history_limit: int
    current_input: str
    retrieved_history_item_count: int = 0
    discarded_prefix_item_count: int = 0
    removed_observation_item_count: int = 0
    removed_observation_characters: int = 0
    removed_support_tool_item_count: int = 0
    removed_support_tool_characters: int = 0
    selected_history_items: list[dict[str, Any]] = field(default_factory=list)
    model_request_inputs: list[dict[str, Any]] = field(default_factory=list)

    def __call__(
        self,
        history_items: list[dict[str, Any]],
        new_items: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        self.retrieved_history_item_count = len(history_items)
        first_observation_index = next(
            (
                index
                for index, item in enumerate(history_items)
                if _observation_input_text(item) is not None
            ),
            len(history_items),
        )
        self.discarded_prefix_item_count = first_observation_index

        candidate_items = history_items[first_observation_index:]
        transient_call_ids = {
            str(item.get("call_id"))
            for item in candidate_items
            if item.get("type") == "function_call"
            and item.get("name") in TRANSIENT_SUPPORT_TOOL_NAMES
            and item.get("call_id") is not None
        }
        selected: list[dict[str, Any]] = []
        removed_observation_characters = 0
        removed_observation_count = 0
        removed_support_characters = 0
        removed_support_count = 0
        for item in candidate_items:
            observation_text = _observation_input_text(item)
            if observation_text is not None:
                removed_observation_count += 1
                removed_observation_characters += len(observation_text)
                continue
            if _is_transient_support_item(item, transient_call_ids):
                removed_support_count += 1
                removed_support_characters += len(_canonical_json(item))
                continue
            selected.append(item)

        self.removed_observation_item_count = removed_observation_count
        self.removed_observation_characters = removed_observation_characters
        self.removed_support_tool_item_count = removed_support_count
        self.removed_support_tool_characters = removed_support_characters
        self.selected_history_items = copy.deepcopy(selected)
        return [*selected, *new_items]

    def manifest(self) -> dict[str, Any]:
        current_input_bytes = self.current_input.encode("utf-8")
        return {
            "policy": CONTEXT_POLICY_NAME,
            "sessionHistoryLimit": self.session_history_limit,
            "retrievedHistoryItemCount": self.retrieved_history_item_count,
            "discardedPrefixItemCount": self.discarded_prefix_item_count,
            "removedObservationItemCount": self.removed_observation_item_count,
            "removedObservationCharacters": self.removed_observation_characters,
            "removedSupportToolItemCount": self.removed_support_tool_item_count,
            "removedSupportToolCharacters": self.removed_support_tool_characters,
            "selectedHistoryItems": copy.deepcopy(self.selected_history_items),
            "currentInputItemCount": 1,
            "currentInputCharacters": len(self.current_input),
            "currentInputSha256": hashlib.sha256(current_input_bytes).hexdigest(),
            "modelRequestInputs": copy.deepcopy(self.model_request_inputs),
        }


@dataclass
class _ModelInputRecorder:
    request_inputs: list[dict[str, Any]]
    parent_agent: Any = None

    def __call__(self, data: CallModelData[Any]) -> ModelInputData:
        if data.agent is not self.parent_agent:
            return data.model_data
        input_json = _canonical_json(data.model_data.input)
        instructions = data.model_data.instructions or ""
        self.request_inputs.append(
            {
                "requestIndex": len(self.request_inputs) + 1,
                "inputItemCount": len(data.model_data.input),
                "inputCharacters": len(input_json),
                "inputSha256": hashlib.sha256(input_json.encode("utf-8")).hexdigest(),
                "instructionsCharacters": len(instructions),
                "instructionsSha256": hashlib.sha256(
                    instructions.encode("utf-8")
                ).hexdigest(),
            }
        )
        return data.model_data


class _ModelActivityHooks(RunHooks[HarnessRunContext]):
    """Publish a body-free lifecycle stream for the parent model run."""

    def __init__(self, parent_agent: Agent[HarnessRunContext]) -> None:
        self.parent_agent = parent_agent
        self.request_count = 0
        self.tool_count = 0
        self.request_starts: dict[int, float] = {}
        self.tool_starts: dict[str, tuple[int, float]] = {}

    async def on_llm_start(
        self,
        context: Any,
        agent: Agent[HarnessRunContext],
        system_prompt: str | None,
        input_items: list[Any],
    ) -> None:
        del system_prompt
        if agent is not self.parent_agent:
            return
        self.request_count += 1
        request_index = self.request_count
        self.request_starts[request_index] = monotonic()
        context.context.report_activity(
            "model-request-started",
            {
                "requestIndex": request_index,
                "inputItemCount": len(input_items),
            },
        )

    async def on_llm_end(
        self,
        context: Any,
        agent: Agent[HarnessRunContext],
        response: Any,
    ) -> None:
        if agent is not self.parent_agent:
            return
        request_index = self.request_count
        started_at = self.request_starts.pop(request_index, None)
        context.context.report_activity(
            "model-request-completed",
            {
                "requestIndex": request_index,
                "responseId": response.response_id,
                "outputItemCount": len(response.output),
                "usage": {
                    "requests": response.usage.requests,
                    "inputTokens": response.usage.input_tokens,
                    "outputTokens": response.usage.output_tokens,
                    "totalTokens": response.usage.total_tokens,
                },
                "durationMs": _elapsed_milliseconds(started_at),
            },
        )

    async def on_tool_start(
        self,
        context: Any,
        agent: Agent[HarnessRunContext],
        tool: Any,
    ) -> None:
        if agent is not self.parent_agent:
            return
        self.tool_count += 1
        sequence = self.tool_count
        key = _tool_activity_key(context, tool.name, sequence)
        self.tool_starts[key] = (sequence, monotonic())
        context.context.report_activity(
            "model-tool-started",
            {"tool": tool.name, "sequence": sequence},
        )

    async def on_tool_end(
        self,
        context: Any,
        agent: Agent[HarnessRunContext],
        tool: Any,
        result: object,
    ) -> None:
        del result
        if agent is not self.parent_agent:
            return
        key = _tool_activity_key(context, tool.name, self.tool_count)
        started = self.tool_starts.pop(key, None)
        if started is None:
            matching_key = next(
                (
                    candidate
                    for candidate in self.tool_starts
                    if candidate.startswith(f"{tool.name}:")
                ),
                None,
            )
            started = self.tool_starts.pop(matching_key, None) if matching_key else None
        sequence, started_at = started or (self.tool_count, None)
        context.context.report_activity(
            "model-tool-completed",
            {
                "tool": tool.name,
                "sequence": sequence,
                "durationMs": _elapsed_milliseconds(started_at),
            },
        )


def _tool_activity_key(context: Any, tool_name: str, fallback: int) -> str:
    call_id = getattr(context, "tool_call_id", None)
    return f"{tool_name}:{call_id or fallback}"


def _elapsed_milliseconds(started_at: float | None) -> int | None:
    if started_at is None:
        return None
    return max(0, int((monotonic() - started_at) * 1_000))


class ModelRunError(RuntimeError):
    """A failed parent run that still produced traceable nested model work."""

    def __init__(self, message: str, partial_result: ModelRunResult) -> None:
        super().__init__(message)
        self.partial_result = partial_result


class PermanentModelError(ModelRunError):
    """A provider account or authentication failure that retries cannot repair."""


class ModelRunCancelled(asyncio.CancelledError):
    """A cancelled parent run that still produced traceable nested model work."""

    def __init__(self, partial_result: ModelRunResult) -> None:
        super().__init__("Model run cancelled")
        self.partial_result = partial_result


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
        max_output_tokens: int = 16_384,
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

    @property
    def rules_oracle_available(self) -> bool:
        return self.rulebook is not None

    async def run_once(
        self,
        *,
        agent_record: AgentRecord,
        observation: dict[str, Any],
        context: HarnessRunContext,
        tools: list[FunctionTool],
        instructions: str,
        max_turns: int,
        stop_at_tool_names: list[str],
        prompt_cache_key: str,
        trace_metadata: dict[str, str],
    ) -> ModelRunResult:
        current_input = OBSERVATION_INPUT_PREFIX + json.dumps(
            observation, separators=(",", ":")
        )
        context_filter = _SessionContextFilter(
            session_history_limit=self.session_history_items,
            current_input=current_input,
        )
        model_input_recorder = _ModelInputRecorder(context_filter.model_request_inputs)
        if not self.api_key:
            message = (
                "OPENROUTER_TOKEN or OPENAI_API_KEY is not configured on the harness server"
            )
            raise ModelRunError(message, _partial_result([], context_filter.manifest()))

        if not tools:
            message = "No model tool is implemented for the current game state"
            raise ModelRunError(
                message, _partial_result([], context_filter.manifest())
            )
        if not stop_at_tool_names:
            message = "No gameplay tool is implemented for the current game state"
            raise ModelRunError(
                message, _partial_result([], context_filter.manifest())
            )

        oracle_interactions: list[dict[str, Any]] = []
        try:
            model = OpenAIResponsesModel(
                model=agent_record.model, openai_client=self.client
            )
            run_config = RunConfig(
                tracing_disabled=True,
                workflow_name="Raven Harness action",
                group_id=agent_record.id,
                trace_metadata=trace_metadata,
                session_input_callback=context_filter,
                call_model_input_filter=model_input_recorder,
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
                    if tool.name == RULES_ORACLE_TOOL_NAME
                    and self.rulebook is not None
                    else tool
                )
                for tool in tools
            ]
            agent = Agent[HarnessRunContext](
                name=agent_record.name,
                instructions=instructions,
                model=model,
                tools=tools,
                model_settings=self._model_settings(
                    max_tokens=self.max_output_tokens,
                    prompt_cache_key=prompt_cache_key,
                    metadata=trace_metadata,
                    user=agent_record.id,
                ),
                tool_use_behavior=_stop_after_accepted_action(stop_at_tool_names),
                reset_tool_choice=False,
            )
            model_input_recorder.parent_agent = agent
            activity_hooks = _ModelActivityHooks(agent)
        except Exception as error:
            raise ModelRunError(
                safe_error_text(error),
                _partial_result(oracle_interactions, context_filter.manifest()),
            ) from None
        try:
            async with self._run_slots:
                async with asyncio.timeout(self.run_timeout_seconds):
                    result = await Runner.run(
                        agent,
                        input=current_input,
                        context=context,
                        max_turns=max_turns,
                        run_config=run_config,
                        session=self._session(agent_record.id),
                        hooks=activity_hooks,
                    )
        except asyncio.CancelledError as error:
            raise ModelRunCancelled(
                _partial_result(oracle_interactions, context_filter.manifest())
            ) from error
        except TimeoutError:
            message = (
                f"Model run exceeded {self.run_timeout_seconds:g} seconds total"
            )
            raise ModelRunError(
                message,
                _partial_result(oracle_interactions, context_filter.manifest()),
            ) from None
        except APITimeoutError:
            message = (
                "Model API timed out after "
                f"{self.request_timeout_seconds:g} seconds per attempt and "
                f"{self.max_retries} retries"
            )
            raise ModelRunError(
                message,
                _partial_result(oracle_interactions, context_filter.manifest()),
            ) from None
        except Exception as error:
            error_type = (
                PermanentModelError
                if is_permanent_provider_error(error)
                else ModelRunError
            )
            raise error_type(
                safe_error_text(error),
                _partial_result(oracle_interactions, context_filter.manifest()),
            ) from None

        try:
            return _completed_result(
                result,
                oracle_interactions,
                context_filter.manifest(),
            )
        except Exception as error:
            raise ModelRunError(
                safe_error_text(error),
                _partial_result(oracle_interactions, context_filter.manifest()),
            ) from None

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


def _observation_input_text(item: dict[str, Any]) -> str | None:
    if item.get("role") != "user":
        return None
    content = item.get("content")
    if isinstance(content, str) and content.startswith(OBSERVATION_INPUT_PREFIX):
        return content
    return None


def _is_transient_support_item(
    item: dict[str, Any], transient_call_ids: set[str]
) -> bool:
    if (
        item.get("type") == "function_call"
        and item.get("name") in TRANSIENT_SUPPORT_TOOL_NAMES
    ):
        return True
    return (
        item.get("type") == "function_call_output"
        and str(item.get("call_id")) in transient_call_ids
    )


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _completed_result(
    result: Any,
    oracle_interactions: list[dict[str, Any]],
    context_manifest: dict[str, Any],
) -> ModelRunResult:
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
        native_usage = (
            _jsonable(response.raw_usage) if response.raw_usage is not None else {}
        )
        native_usage["scope"] = "agent"
        native_usage["response_id"] = response.response_id
        raw_usage.append(native_usage)
    _append_oracle_traces(response_items, raw_usage, oracle_interactions)
    return ModelRunResult(
        response_id=result.last_response_id,
        output_text=str(result.final_output or ""),
        usage=usage,
        response_items=response_items,
        raw_usage=raw_usage,
        context_manifest=context_manifest,
    )


def _append_oracle_traces(
    response_items: list[dict[str, Any]],
    raw_usage: list[dict[str, Any]],
    interactions: list[dict[str, Any]],
) -> None:
    for interaction in interactions:
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


def _partial_result(
    interactions: list[dict[str, Any]], context_manifest: dict[str, Any]
) -> ModelRunResult:
    response_items: list[dict[str, Any]] = []
    raw_usage: list[dict[str, Any]] = []
    usage = {
        "requests": 0,
        "inputTokens": 0,
        "outputTokens": 0,
        "totalTokens": 0,
    }
    _append_oracle_traces(response_items, raw_usage, interactions)
    for interaction in interactions:
        interaction_usage = interaction["usage"]
        for key in usage:
            usage[key] += int(interaction_usage[key])
    return ModelRunResult(
        response_id=None,
        output_text="",
        usage=usage,
        response_items=response_items,
        raw_usage=raw_usage,
        context_manifest=context_manifest,
    )


def _jsonable(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", exclude_none=True)
    if isinstance(value, dict):
        return value
    return {"value": str(value)}
