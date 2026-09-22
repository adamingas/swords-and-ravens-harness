from __future__ import annotations

import asyncio
import hashlib
import json
from collections import Counter
from dataclasses import dataclass, field
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
from agents.models.openai_responses import _mark_request_completed_without_usage
from agents.run_config import CallModelData, ModelInputData
from openai import AsyncOpenAI

from ..errors import is_permanent_provider_error, safe_error_text
from ..game.client import GameConnectionLost
from ..harness.actions import HarnessRunContext
from ..harness.decision import SUBMIT_ACTION_TOOL_NAME
from ..rulebook import RULES_ORACLE_TOOL_NAME, Rulebook
from ..schemas import AgentRecord


SUBMISSION_REMINDER = (
    "You stopped without submitting a gameplay action. Continue this same decision. "
    "Use exploration tools if more information would help, then call submit_action. "
    "Only an accepted submit_action call finishes the decision."
)
CONTEXT_POLICY_NAME = "current-decision-with-continuation"


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


def _stop_after_submission(
    context_wrapper: Any, tool_results: list[Any]
) -> ToolsToFinalOutputResult:
    """Continue exploration until submit_action has executed an accepted action."""

    if context_wrapper.context.action_taken is None:
        return ToolsToFinalOutputResult(is_final_output=False, final_output=None)
    matching_result = next(
        (
            result
            for result in tool_results
            if result.tool.name == SUBMIT_ACTION_TOOL_NAME
            or result.tool.qualified_name == SUBMIT_ACTION_TOOL_NAME
        ),
        None,
    )
    if matching_result is None:
        return ToolsToFinalOutputResult(is_final_output=False, final_output=None)
    return ToolsToFinalOutputResult(
        is_final_output=True,
        final_output=matching_result.output,
    )


@dataclass(frozen=True)
class ModelRunResult:
    response_id: str | None
    output_text: str
    usage: dict[str, int]
    response_items: list[dict[str, Any]]
    raw_usage: list[dict[str, Any]]
    context_manifest: dict[str, Any] = field(default_factory=dict)


@dataclass
class _ContextManifest:
    current_input: str
    model_request_inputs: list[dict[str, Any]] = field(default_factory=list)
    action_output_schema: dict[str, Any] | None = None

    def manifest(self) -> dict[str, Any]:
        current_input_bytes = self.current_input.encode("utf-8")
        manifest = {
            "policy": CONTEXT_POLICY_NAME,
            "currentInputItemCount": 1,
            "currentInputCharacters": len(self.current_input),
            "currentInputSha256": hashlib.sha256(current_input_bytes).hexdigest(),
            "modelRequestInputs": list(self.model_request_inputs),
        }
        if self.action_output_schema is not None:
            manifest["actionOutputSchema"] = self.action_output_schema
            manifest["actionOutputSchemaSha256"] = hashlib.sha256(
                _canonical_json(self.action_output_schema).encode()
            ).hexdigest()
        return manifest


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
    """Publish a body-free lifecycle stream for every model call in one turn."""

    def __init__(self) -> None:
        self.parent_agent: Agent[HarnessRunContext] | None = None
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
        scope = self._scope(agent)
        if scope is None:
            return
        self.request_count += 1
        request_index = self.request_count
        self.request_starts[request_index] = monotonic()
        context.context.report_activity(
            "model-request-started",
            {
                "requestIndex": request_index,
                "scope": scope,
                "inputItemCount": len(input_items),
            },
        )

    async def on_llm_end(
        self,
        context: Any,
        agent: Agent[HarnessRunContext],
        response: Any,
    ) -> None:
        scope = self._scope(agent)
        if scope is None:
            return
        if scope == "agent":
            self.responses.append(response)
        request_index = self.request_count
        started_at = self.request_starts.pop(request_index, None)
        context.context.report_activity(
            "model-request-completed",
            {
                "requestIndex": request_index,
                "scope": scope,
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

    def _scope(self, agent: Agent[HarnessRunContext]) -> str | None:
        if agent is self.parent_agent:
            return "agent"
        if agent.name == "Rules oracle":
            return "rules-oracle"
        return None

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


class _UsageCapturingResponsesModel(OpenAIResponsesModel):
    """Retain each raw response before SDK processing."""

    def __init__(
        self,
        *,
        response_sink: list[tuple[str, Any]] | None = None,
        response_scope: str = "agent",
        response_provider: str | None = None,
        response_attribution_sink: dict[str, dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.response_sink = response_sink
        self.response_scope = response_scope
        self.response_provider = response_provider
        self.response_attribution_sink = response_attribution_sink

    async def _fetch_response(self, *args: Any, **kwargs: Any) -> Any:
        if kwargs.get("stream", False):
            return await super()._fetch_response(*args, **kwargs)

        create_kwargs = self._build_response_create_kwargs(*args, **kwargs)
        response = await self._get_client().responses.create(**create_kwargs)
        if self.response_attribution_sink is not None:
            response_id = str(getattr(response, "id", ""))
            if response_id:
                self.response_attribution_sink[response_id] = _response_attribution(
                    response, response_provider=self.response_provider
                )
        if getattr(response, "usage", None) is None:
            _mark_request_completed_without_usage(response)
        if self.response_sink is not None:
            self.response_sink.append((self.response_scope, response))
        status = getattr(response, "status", None)
        if status in {"failed", "incomplete"}:
            detail = getattr(response, "incomplete_details", None)
            suffix = f"; incomplete_details={detail}" if detail is not None else ""
            provider_error = getattr(response, "error", None)
            if provider_error is not None:
                suffix += "; error=" + safe_error_text(
                    _canonical_json(_jsonable(provider_error))
                )
            raise RuntimeError(
                f"Responses API returned terminal status {status}{suffix}"
            )
        return response


def _response_model(
    *,
    model: str,
    openai_client: AsyncOpenAI,
    response_sink: list[tuple[str, Any]] | None = None,
    response_scope: str = "agent",
    response_provider: str | None = None,
    response_attribution_sink: dict[str, dict[str, Any]] | None = None,
) -> OpenAIResponsesModel:
    return _UsageCapturingResponsesModel(
        model=model,
        openai_client=openai_client,
        response_sink=response_sink,
        response_scope=response_scope,
        response_provider=response_provider,
        response_attribution_sink=response_attribution_sink,
    )


def _response_attribution(
    response: Any, *, response_provider: str | None = None
) -> dict[str, Any]:
    """Keep portable attribution fields returned with the model response."""

    values = {
        "response_model": getattr(response, "model", None),
        "response_provider": getattr(response, "provider", None) or response_provider,
        "service_tier": getattr(response, "service_tier", None),
        "request_id": getattr(response, "_request_id", None),
    }
    return {key: value for key, value in values.items() if value is not None}


def _merge_response_attribution(
    usage: dict[str, Any],
    response_id: str | None,
    attribution: dict[str, dict[str, Any]],
) -> None:
    if response_id is not None:
        usage.update(attribution.get(response_id, {}))


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


class TransientProviderCapacityError(ModelRunError):
    """A provider rejected a request because temporary capacity was unavailable."""


class ModelRunCancelled(asyncio.CancelledError):
    """A cancelled parent run that still produced traceable nested model work."""

    def __init__(self, partial_result: ModelRunResult) -> None:
        super().__init__("Model run cancelled")
        self.partial_result = partial_result


class LLMAgentRunner:
    """Shared Responses API agent loop for concrete LLM endpoint adapters."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        rulebook: Rulebook | None = None,
        max_output_tokens: int | None = None,
    ) -> None:
        if max_output_tokens is not None and max_output_tokens <= 0:
            raise ValueError("max_output_tokens must be positive when specified")
        self.api_key = api_key
        self.rulebook = rulebook
        self.max_output_tokens = max_output_tokens
        self.client = AsyncOpenAI(
            api_key=api_key or "not-configured",
            base_url=base_url,
            timeout=None,
            max_retries=0,
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
        prompt_cache_key: str,
        trace_metadata: dict[str, str],
    ) -> ModelRunResult:
        if context.decision is None:
            raise ValueError("A model turn requires a gameplay decision")
        visible_observation = dict(observation)
        briefing = visible_observation.pop("decisionBriefing")
        current_input = (
            "Read the current board state, then follow the decision instructions below."
            "\n\nCurrent observation:\n"
            + json.dumps(visible_observation, separators=(",", ":"))
            + "\n\nCurrent decision:\n"
            + briefing
            + "\n\nHow to complete this decision:\n"
            "You MUST call submit_action to submit your gameplay action. A text response "
            "does not submit anything. Use the exact fields and enum values in the current "
            "submit_action schema. Explore liberally with the other tools whenever they can "
            "test a route, target, threat, rule, memory, or assumption. Inspect the results, "
            "then call submit_action. Exploration tools do not submit an action."
        )
        run_manifest = _ContextManifest(
            current_input=current_input,
            action_output_schema=context.decision.output_schema.json_schema(),
        )
        model_input_recorder = _ModelInputRecorder(run_manifest.model_request_inputs)
        if not self.api_key:
            message = "OPENROUTER_TOKEN or OPENAI_API_KEY is not configured on the harness server"
            raise ModelRunError(message, _partial_result([], run_manifest.manifest()))

        oracle_interactions: list[dict[str, Any]] = []
        provider_responses: list[tuple[str, Any]] = []
        response_attribution: dict[str, dict[str, Any]] = {}
        try:
            model = _response_model(
                model=agent_record.model,
                openai_client=self.client,
                response_sink=provider_responses,
                response_attribution_sink=response_attribution,
            )
            run_config = RunConfig(
                tracing_disabled=True,
                workflow_name="Raven Harness action",
                group_id=agent_record.id,
                trace_metadata=trace_metadata,
                call_model_input_filter=model_input_recorder,
            )
            activity_hooks = _ModelActivityHooks()
            tools = [
                (
                    self.rulebook.build_oracle_tool(
                        model=_response_model(
                            model=agent_record.model,
                            openai_client=self.client,
                            response_sink=provider_responses,
                            response_scope="rules-oracle",
                            response_attribution_sink=response_attribution,
                        ),
                        model_settings=self._model_settings(
                            max_tokens=900,
                            prompt_cache_key=(
                                f"raven-rules-{agent_record.model}-"
                                f"{self.rulebook.cache_fingerprint}"
                            ),
                            metadata=trace_metadata,
                            user=agent_record.id,
                        ),
                        interaction_sink=oracle_interactions,
                        run_config=run_config,
                        hooks=activity_hooks,
                    )
                    if tool.name == RULES_ORACLE_TOOL_NAME and self.rulebook is not None
                    else tool
                )
                for tool in tools
            ]
            tools.append(context.decision.submission_tool())
            agent = Agent[HarnessRunContext](
                name=agent_record.name,
                instructions=instructions,
                model=model,
                tools=tools,
                output_type=None,
                model_settings=self._model_settings(
                    max_tokens=self.max_output_tokens,
                    prompt_cache_key=prompt_cache_key,
                    metadata=trace_metadata,
                    user=agent_record.id,
                    tool_choice="required",
                ),
                tool_use_behavior=_stop_after_submission,
                reset_tool_choice=False,
            )
            model_input_recorder.parent_agent = agent
            activity_hooks.parent_agent = agent
        except Exception as error:
            raise ModelRunError(
                safe_error_text(error),
                _partial_result(oracle_interactions, run_manifest.manifest()),
            ) from None

        def partial_result() -> ModelRunResult:
            return _partial_result(
                oracle_interactions,
                run_manifest.manifest(),
                parent_responses=activity_hooks.responses,
                provider_responses=provider_responses,
                response_attribution=response_attribution,
            )

        try:
            results = []
            run_input: str | list[dict[str, Any]] = current_input
            while context.action_taken is None:
                result = await Runner.run(
                    agent,
                    input=run_input,
                    context=context,
                    max_turns=None,
                    run_config=run_config,
                    hooks=activity_hooks,
                )
                results.append(result)
                if context.action_taken is None:
                    run_input = result.to_input_list()
                    run_input.append({"role": "user", "content": SUBMISSION_REMINDER})
        except asyncio.CancelledError as error:
            raise ModelRunCancelled(partial_result()) from error
        except GameConnectionLost:
            raise
        except Exception as error:
            connection_error = _caused_by_connection_loss(error)
            if connection_error is not None:
                raise connection_error from error
            error_type = (
                PermanentModelError
                if is_permanent_provider_error(error)
                else (
                    TransientProviderCapacityError
                    if getattr(error, "status_code", None) in {429, 503}
                    else ModelRunError
                )
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
                results,
                oracle_interactions,
                run_manifest.manifest(),
                provider_responses=provider_responses,
                response_attribution=response_attribution,
            )
        except Exception as error:
            raise ModelRunError(
                safe_error_text(error),
                partial_result(),
            ) from None
        return completed

    async def shutdown(self) -> None:
        await self.client.close()

    def _model_settings(
        self,
        *,
        max_tokens: int | None,
        prompt_cache_key: str | None,
        metadata: dict[str, str] | None,
        user: str | None = None,
        tool_choice: str = "auto",
    ) -> ModelSettings:
        extra_body = self._request_extra_body(user=user)
        return ModelSettings(
            tool_choice=tool_choice,
            parallel_tool_calls=False,
            max_tokens=max_tokens,
            reasoning={"effort": "high"},
            store=False,
            metadata=metadata,
            preserve_raw_usage=True,
            extra_body=extra_body or None,
            extra_args=(
                {
                    "prompt_cache_key": prompt_cache_key,
                    **({"user": user} if user else {}),
                }
                if prompt_cache_key
                else None
            ),
        )

    def _request_extra_body(self, *, user: str | None) -> dict[str, Any]:
        del user
        return {}


class OpenAIAgentRunner(LLMAgentRunner):
    """Agent runner for OpenAI's Responses API."""


class OpenRouterAgentRunner(LLMAgentRunner):
    """Agent runner for OpenRouter with shared endpoint exclusions."""

    def __init__(
        self,
        *,
        provider_blocklist: list[str] | tuple[str, ...],
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.provider_blocklist = tuple(
            dict.fromkeys(
                provider.strip().lower()
                for provider in provider_blocklist
                if provider.strip()
            )
        )

    def _request_extra_body(self, *, user: str | None) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if user:
            body["session_id"] = f"raven-agent-{user}"
        if self.provider_blocklist:
            body["provider"] = {"ignore": list(self.provider_blocklist)}
        return body


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _completed_result(
    results: list[Any],
    oracle_interactions: list[dict[str, Any]],
    context_manifest: dict[str, Any],
    *,
    provider_responses: list[tuple[str, Any]] | None = None,
    response_attribution: dict[str, dict[str, Any]] | None = None,
) -> ModelRunResult:
    response_attribution = response_attribution or {}
    usage = {
        "requests": 0,
        "inputTokens": 0,
        "outputTokens": 0,
        "totalTokens": 0,
    }
    response_items = [
        _jsonable(item.to_input_item())
        for result in results
        for item in result.new_items
    ]
    raw_usage: list[dict[str, Any]] = []
    parent_responses = []
    for result in results:
        total_usage = result.context_wrapper.usage
        usage["requests"] += total_usage.requests
        usage["inputTokens"] += total_usage.input_tokens
        usage["outputTokens"] += total_usage.output_tokens
        usage["totalTokens"] += total_usage.total_tokens
        parent_responses.extend(result.raw_responses)
        for response in result.raw_responses:
            native_usage = (
                _jsonable(response.raw_usage) if response.raw_usage is not None else {}
            )
            native_usage["scope"] = "agent"
            native_usage["response_id"] = response.response_id
            _merge_response_attribution(
                native_usage, response.response_id, response_attribution
            )
            raw_usage.append(native_usage)
    _append_oracle_traces(
        response_items,
        raw_usage,
        oracle_interactions,
        response_attribution=response_attribution,
    )
    unrepresented_responses = _unrepresented_provider_responses(
        provider_responses or [],
        parent_responses=parent_responses,
        oracle_interactions=oracle_interactions,
    )
    _append_provider_response_traces(
        response_items,
        raw_usage,
        unrepresented_responses,
        usage=usage,
        count_usage=False,
        response_attribution=response_attribution,
    )
    final = results[-1]
    return ModelRunResult(
        response_id=final.last_response_id,
        output_text=(
            json.dumps(final.final_output, ensure_ascii=False)
            if isinstance(final.final_output, dict)
            else str(final.final_output or "")
        ),
        usage=usage,
        response_items=response_items,
        raw_usage=raw_usage,
        context_manifest=context_manifest,
    )


def _append_oracle_traces(
    response_items: list[dict[str, Any]],
    raw_usage: list[dict[str, Any]],
    interactions: list[dict[str, Any]],
    *,
    response_attribution: dict[str, dict[str, Any]] | None = None,
) -> None:
    response_attribution = response_attribution or {}
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
        for usage in interaction["rawUsage"]:
            _merge_response_attribution(
                usage, usage.get("response_id"), response_attribution
            )
            raw_usage.append(usage)


def _append_provider_response_traces(
    response_items: list[dict[str, Any]],
    raw_usage: list[dict[str, Any]],
    provider_responses: list[tuple[str, Any]],
    *,
    usage: dict[str, int],
    count_usage: bool = True,
    response_attribution: dict[str, dict[str, Any]],
) -> None:
    for scope, response in provider_responses:
        response_usage = getattr(response, "usage", None)
        if count_usage:
            usage["requests"] += 1
            if response_usage is not None:
                usage["inputTokens"] += int(response_usage.input_tokens)
                usage["outputTokens"] += int(response_usage.output_tokens)
                usage["totalTokens"] += int(response_usage.total_tokens)
        native_usage = _jsonable(response_usage) if response_usage is not None else {}
        response_id = getattr(response, "id", None)
        native_usage["scope"] = scope
        native_usage["response_id"] = response_id
        _merge_response_attribution(native_usage, response_id, response_attribution)
        raw_usage.append(native_usage)
        response_items.append(
            {
                "type": "partial_model_response",
                "scope": scope,
                "status": getattr(response, "status", "failed"),
                "responseId": response_id,
                "incompleteDetails": _jsonable(
                    getattr(response, "incomplete_details", None)
                ),
                "providerError": (
                    _jsonable(response.error)
                    if getattr(response, "error", None) is not None
                    else None
                ),
                "output": [_jsonable(item) for item in getattr(response, "output", [])],
            }
        )


def _unrepresented_provider_responses(
    provider_responses: list[tuple[str, Any]],
    *,
    parent_responses: list[Any],
    oracle_interactions: list[dict[str, Any]],
) -> list[tuple[str, Any]]:
    represented = Counter(
        ("agent", getattr(response, "response_id", None))
        for response in parent_responses
    )
    represented.update(
        ("rules-oracle", usage.get("response_id"))
        for interaction in oracle_interactions
        for usage in interaction["rawUsage"]
    )
    missing: list[tuple[str, Any]] = []
    for scope, response in provider_responses:
        key = (scope, getattr(response, "id", None))
        if represented[key] > 0:
            represented[key] -= 1
        else:
            missing.append((scope, response))
    return missing


def _partial_result(
    interactions: list[dict[str, Any]],
    context_manifest: dict[str, Any],
    *,
    parent_responses: list[Any] | None = None,
    provider_responses: list[tuple[str, Any]] | None = None,
    response_attribution: dict[str, dict[str, Any]] | None = None,
) -> ModelRunResult:
    response_attribution = response_attribution or {}
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
        _merge_response_attribution(
            native_usage, response.response_id, response_attribution
        )
        raw_usage.append(native_usage)
        response_items.append(
            {
                "type": "partial_model_response",
                "status": "completed",
                "responseId": response.response_id,
                "output": [_jsonable(item) for item in response.output],
            }
        )
    unrepresented_responses = _unrepresented_provider_responses(
        provider_responses or [],
        parent_responses=parent_responses or [],
        oracle_interactions=interactions,
    )
    _append_provider_response_traces(
        response_items,
        raw_usage,
        unrepresented_responses,
        usage=usage,
        response_attribution=response_attribution,
    )
    _append_oracle_traces(
        response_items,
        raw_usage,
        interactions,
        response_attribution=response_attribution,
    )
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
