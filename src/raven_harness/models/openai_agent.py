from __future__ import annotations

import asyncio
import copy
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from time import monotonic
from typing import TYPE_CHECKING, Any

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

from ..config import DEFAULT_MODEL_MAX_OUTPUT_TOKENS
from ..errors import is_permanent_provider_error, safe_error_text
from ..game.client import GameConnectionLost
from ..harness.actions import HarnessRunContext
from ..rulebook import RULES_ORACLE_TOOL_NAME, Rulebook
from ..schemas import AgentRecord

if TYPE_CHECKING:
    from ..agent_store import AgentStore


OBSERVATION_INPUT_PREFIX = (
    "A new decision starts with this current player-scoped game observation. "
    "Earlier tool results are history; you have not acted on this observation. "
    "Choose exactly one available tool for the current decision.\n\n"
)
CONTEXT_POLICY_NAME = "current-observation-with-isolated-retries-v2"
TRANSIENT_SUPPORT_TOOL_NAMES = {
    "ask_rules_oracle",
    "recall_game_state",
    "remember_strategy",
}


def _caused_by_connection_loss(error: BaseException) -> GameConnectionLost | None:
    """Recover a connection fence wrapped by the Agents SDK tool runner."""

    seen: set[int] = set()
    current: BaseException | None = error
    while current is not None and id(current) not in seen:
        if isinstance(current, GameConnectionLost):
            return current
        seen.add(id(current))
        current = current.__cause__ or current.__context__
    return None


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
    include_history: bool = True
    retrieved_history_item_count: int = 0
    discarded_prefix_item_count: int = 0
    removed_observation_item_count: int = 0
    removed_observation_characters: int = 0
    removed_support_tool_item_count: int = 0
    removed_support_tool_characters: int = 0
    removed_retry_history_item_count: int = 0
    removed_retry_history_characters: int = 0
    selected_history_items: list[dict[str, Any]] = field(default_factory=list)
    model_request_inputs: list[dict[str, Any]] = field(default_factory=list)

    def __call__(
        self,
        history_items: list[dict[str, Any]],
        new_items: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        self.retrieved_history_item_count = len(history_items)
        if not self.include_history:
            self.removed_retry_history_item_count = len(history_items)
            self.removed_retry_history_characters = sum(
                len(_canonical_json(item)) for item in history_items
            )
            self.selected_history_items = []
            return list(new_items)

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
            "historyMode": (
                "recent-accepted-actions"
                if self.include_history
                else "current-observation-only-retry"
            ),
            "sessionHistoryLimit": self.session_history_limit,
            "retrievedHistoryItemCount": self.retrieved_history_item_count,
            "discardedPrefixItemCount": self.discarded_prefix_item_count,
            "removedObservationItemCount": self.removed_observation_item_count,
            "removedObservationCharacters": self.removed_observation_characters,
            "removedSupportToolItemCount": self.removed_support_tool_item_count,
            "removedSupportToolCharacters": self.removed_support_tool_characters,
            "removedRetryHistoryItemCount": self.removed_retry_history_item_count,
            "removedRetryHistoryCharacters": self.removed_retry_history_characters,
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
        self.responses: list[Any] = []

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
        self.responses.append(response)
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


def _capture_terminal_responses(model: Any, sink: list[Any]) -> None:
    """Retain failed Responses API terminal payloads before the SDK raises."""

    iterate = getattr(model, "_iter_websocket_response_events", None)
    if not callable(iterate):
        return

    async def tracked(create_kwargs: dict[str, Any]):
        async for event in iterate(create_kwargs):
            if getattr(event, "type", None) in {
                "response.failed",
                "response.incomplete",
            }:
                response = getattr(event, "response", None)
                if response is not None:
                    sink.append(response)
            yield event

    model._iter_websocket_response_events = tracked


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
        max_output_tokens: int = DEFAULT_MODEL_MAX_OUTPUT_TOKENS,
        session_database_path: Path | None = None,
        session_history_items: int = 32,
        checkpoint_store: AgentStore | None = None,
        provider_routing: dict[str, Any] | None = None,
        rulebook: Rulebook | None = None,
    ) -> None:
        self.api_key = api_key
        self.request_timeout_seconds = request_timeout_seconds
        self.run_timeout_seconds = run_timeout_seconds
        self.max_retries = max_retries
        self.max_output_tokens = max_output_tokens
        self.session_database_path = session_database_path
        self.session_history_items = session_history_items
        self.checkpoint_store = checkpoint_store
        self._sessions: dict[str, SQLiteSession] = {}
        self._restored_session_ids: set[str] = set()
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
        session = self._session(agent_record.id)
        recovered = await self._restore_agent_session(agent_record.id, session)
        current_state_id = str(observation.get("game", {}).get("stateId") or "unknown")
        if (
            recovered is not None
            and recovered["phase"] == "before-model"
            and recovered["stateId"] == current_state_id
        ):
            observation = copy.deepcopy(recovered["observation"])
        current_input = OBSERVATION_INPUT_PREFIX + json.dumps(
            observation, separators=(",", ":")
        )
        is_retry = bool(observation.get("previousAttemptError"))
        context_filter = _SessionContextFilter(
            session_history_limit=self.session_history_items,
            current_input=current_input,
            include_history=not is_retry,
        )
        model_input_recorder = _ModelInputRecorder(context_filter.model_request_inputs)
        if not self.api_key:
            message = (
                "OPENROUTER_TOKEN or OPENAI_API_KEY is not configured on the harness server"
            )
            raise ModelRunError(message, _partial_result([], context_filter.manifest()))

        session_item_count = await _session_item_count(session)

        oracle_interactions: list[dict[str, Any]] = []
        terminal_responses: list[Any] = []
        try:
            model = OpenAIResponsesModel(
                model=agent_record.model, openai_client=self.client
            )
            _capture_terminal_responses(model, terminal_responses)
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
                    tool_choice="required",
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

        def partial_result() -> ModelRunResult:
            return _partial_result(
                oracle_interactions,
                context_filter.manifest(),
                parent_responses=activity_hooks.responses,
                terminal_responses=terminal_responses,
            )

        try:
            async with asyncio.timeout(self.run_timeout_seconds):
                self._save_agent_checkpoint(
                    agent_record=agent_record,
                    observation=observation,
                    session_item_count=session_item_count,
                    run_id=trace_metadata["run_id"],
                    phase="before-model",
                )
                result = await Runner.run(
                    agent,
                    input=current_input,
                    context=context,
                    max_turns=max_turns,
                    run_config=run_config,
                    session=session,
                    hooks=activity_hooks,
                )
        except asyncio.CancelledError as error:
            await _rollback_unaccepted_session(
                session, session_item_count, context=context
            )
            raise ModelRunCancelled(
                partial_result()
            ) from error
        except TimeoutError:
            await _rollback_unaccepted_session(
                session, session_item_count, context=context
            )
            message = (
                f"Model run exceeded {self.run_timeout_seconds:g} seconds total"
            )
            raise ModelRunError(
                message,
                partial_result(),
            ) from None
        except APITimeoutError:
            await _rollback_unaccepted_session(
                session, session_item_count, context=context
            )
            message = (
                "Model API timed out after "
                f"{self.request_timeout_seconds:g} seconds per attempt and "
                f"{self.max_retries} retries"
            )
            raise ModelRunError(
                message,
                partial_result(),
            ) from None
        except GameConnectionLost:
            await _rollback_unaccepted_session(
                session, session_item_count, context=context
            )
            raise
        except Exception as error:
            await _rollback_unaccepted_session(
                session, session_item_count, context=context
            )
            connection_error = _caused_by_connection_loss(error)
            if connection_error is not None:
                raise connection_error from error
            error_type = (
                PermanentModelError
                if is_permanent_provider_error(error)
                else ModelRunError
            )
            error_text = safe_error_text(error)
            if context.last_tool_error:
                error_text = (
                    f"{error_text}; last tool error: "
                    f"{safe_error_text(context.last_tool_error)}"
                )
            raise error_type(
                error_text,
                partial_result(),
            ) from None

        try:
            completed = _completed_result(
                result,
                oracle_interactions,
                context_filter.manifest(),
            )
        except Exception as error:
            await _rollback_unaccepted_session(
                session, session_item_count, context=context
            )
            raise ModelRunError(
                safe_error_text(error),
                partial_result(),
            ) from None
        await _rollback_unaccepted_session(
            session, session_item_count, context=context
        )
        if context.action_taken is not None:
            self._save_agent_checkpoint(
                agent_record=agent_record,
                observation=observation,
                session_item_count=await _session_item_count(session),
                run_id=trace_metadata["run_id"],
                phase="after-action",
            )
        return completed

    async def _restore_agent_session(
        self, agent_id: str, session: Session | None
    ) -> dict[str, Any] | None:
        """Discard an interrupted turn back to its last durable boundary."""

        if (
            session is None
            or self.checkpoint_store is None
            or agent_id in self._restored_session_ids
        ):
            return None
        checkpoint = self.checkpoint_store.get_agent_checkpoint(agent_id)
        if checkpoint is not None:
            expected_count = int(checkpoint["sessionItemCount"])
            current_count = await _session_item_count(session)
            if current_count < expected_count:
                raise RuntimeError(
                    f"Agent session {agent_id} has {current_count} items but its "
                    f"checkpoint requires {expected_count}"
                )
            for _ in range(current_count - expected_count):
                if await session.pop_item() is None:
                    raise RuntimeError(
                        f"Agent session {agent_id} could not be restored to its "
                        "checkpoint"
                    )
        self._restored_session_ids.add(agent_id)
        return checkpoint

    def _save_agent_checkpoint(
        self,
        *,
        agent_record: AgentRecord,
        observation: dict[str, Any],
        session_item_count: int,
        run_id: str,
        phase: str,
    ) -> None:
        if self.checkpoint_store is None:
            return
        state_id = str(observation.get("game", {}).get("stateId") or "unknown")
        self.checkpoint_store.set_agent_checkpoint(
            agent_id=agent_record.id,
            state_id=state_id,
            observation=observation,
            session_item_count=session_item_count,
            run_id=run_id,
            phase=phase,
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
            self._restored_session_ids.discard(agent_id)

    def _model_settings(
        self,
        *,
        max_tokens: int,
        prompt_cache_key: str | None,
        metadata: dict[str, str] | None,
        user: str | None = None,
        tool_choice: str = "auto",
    ) -> ModelSettings:
        return ModelSettings(
            tool_choice=tool_choice,
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


async def _rollback_unaccepted_session(
    session: Session | None,
    original_item_count: int,
    *,
    context: HarnessRunContext,
) -> None:
    """Remove only the current failed decision from persistent model history."""

    if session is None or context.action_taken is not None:
        return
    try:
        current_item_count = await _session_item_count(session)
        for _ in range(max(0, current_item_count - original_item_count)):
            if await session.pop_item() is None:
                break
    except Exception:
        # A stale failed transcript is worse than losing optional conversation
        # history. Authoritative observations and durable strategy remain stored.
        try:
            await session.clear_session()
        except Exception:
            pass


async def _session_item_count(session: Session | None) -> int:
    if session is None:
        return 0
    # SQLiteSession uses -1 as an explicit unlimited query. Calling get_items()
    # would apply the model-context history limit and is not a durable row count.
    return len(await session.get_items(limit=-1))


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
    interactions: list[dict[str, Any]],
    context_manifest: dict[str, Any],
    *,
    parent_responses: list[Any] | None = None,
    terminal_responses: list[Any] | None = None,
) -> ModelRunResult:
    response_items: list[dict[str, Any]] = []
    raw_usage: list[dict[str, Any]] = []
    usage = {
        "requests": 0,
        "inputTokens": 0,
        "outputTokens": 0,
        "totalTokens": 0,
    }
    for response in parent_responses or []:
        response_usage = response.usage
        usage["requests"] += int(response_usage.requests)
        usage["inputTokens"] += int(response_usage.input_tokens)
        usage["outputTokens"] += int(response_usage.output_tokens)
        usage["totalTokens"] += int(response_usage.total_tokens)
        native_usage = (
            _jsonable(response.raw_usage) if response.raw_usage is not None else {}
        )
        native_usage["scope"] = "agent"
        native_usage["response_id"] = response.response_id
        raw_usage.append(native_usage)
        response_items.append(
            {
                "type": "partial_model_response",
                "status": "completed",
                "responseId": response.response_id,
                "output": [_jsonable(item) for item in response.output],
            }
        )
    for response in terminal_responses or []:
        response_usage = getattr(response, "usage", None)
        usage["requests"] += 1
        if response_usage is not None:
            usage["inputTokens"] += int(response_usage.input_tokens)
            usage["outputTokens"] += int(response_usage.output_tokens)
            usage["totalTokens"] += int(response_usage.total_tokens)
        native_usage = _jsonable(response_usage) if response_usage is not None else {}
        native_usage["scope"] = "agent"
        native_usage["response_id"] = getattr(response, "id", None)
        raw_usage.append(native_usage)
        response_items.append(
            {
                "type": "partial_model_response",
                "status": getattr(response, "status", "failed"),
                "responseId": getattr(response, "id", None),
                "incompleteDetails": _jsonable(
                    getattr(response, "incomplete_details", None)
                ),
                "output": [
                    _jsonable(item) for item in getattr(response, "output", [])
                ],
            }
        )
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
