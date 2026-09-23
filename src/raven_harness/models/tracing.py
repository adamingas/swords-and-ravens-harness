"""Canonical context accounting, lifecycle events and provider response capture."""

from __future__ import annotations
import hashlib
from dataclasses import dataclass, field
from time import monotonic
from typing import Any
from agents import Agent, OpenAIResponsesModel, RunHooks, RunResult
from agents.models.openai_responses import _mark_request_completed_without_usage
from agents.run_config import CallModelData, ModelInputData
from openai import AsyncOpenAI
from ..errors import safe_error_text
from ..harness.actions import HarnessRunContext
from .results import (
    ModelRunResult,
    _canonical_json,
    _jsonable,
    _completed_result,
    _partial_result,
)

CONTEXT_POLICY_NAME = "current-decision-with-continuation"


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


def _tool_activity_key(context: Any, tool_name: str, fallback: int) -> str:
    call_id = getattr(context, "tool_call_id", None)
    return f"{tool_name}:{call_id or fallback}"


def _elapsed_milliseconds(started_at: float | None) -> int | None:
    if started_at is None:
        return None
    return max(0, int((monotonic() - started_at) * 1_000))


class RunTrace:
    """One decision's shared accounting, used by either execution loop."""

    def __init__(self, current_input: str, output_schema: dict[str, Any]) -> None:
        self.manifest = _ContextManifest(
            current_input, action_output_schema=output_schema
        )
        self.input_recorder = _ModelInputRecorder(self.manifest.model_request_inputs)
        self.hooks = _ModelActivityHooks()
        self.provider_responses: list[tuple[str, Any]] = []
        self.response_attribution: dict[str, dict[str, Any]] = {}
        self.oracle_interactions: list[dict[str, Any]] = []
        self.results: list[RunResult] = []

    def model(
        self, model: str, client: AsyncOpenAI, *, scope: str = "agent"
    ) -> OpenAIResponsesModel:
        return _response_model(
            model=model,
            openai_client=client,
            response_sink=self.provider_responses,
            response_scope=scope,
            response_attribution_sink=self.response_attribution,
        )

    def bind(self, agent: Agent[HarnessRunContext]) -> Agent[HarnessRunContext]:
        self.input_recorder.parent_agent = agent
        self.hooks.parent_agent = agent
        return agent

    def partial(self) -> ModelRunResult:
        return _partial_result(
            self.oracle_interactions,
            self.manifest.manifest(),
            parent_responses=self.hooks.responses,
            provider_responses=self.provider_responses,
            response_attribution=self.response_attribution,
        )

    def complete(self) -> ModelRunResult:
        return _completed_result(
            self.results,
            self.oracle_interactions,
            self.manifest.manifest(),
            provider_responses=self.provider_responses,
            response_attribution=self.response_attribution,
        )
