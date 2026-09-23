"""Shared run results, error types and lossless usage/response reconciliation."""

from __future__ import annotations
import asyncio
import json
from collections import Counter
from dataclasses import dataclass, field
from typing import Any
from ..game.client import GameConnectionLost


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


@dataclass(frozen=True)
class ModelRunResult:
    response_id: str | None
    output_text: str
    usage: dict[str, int]
    response_items: list[dict[str, Any]]
    raw_usage: list[dict[str, Any]]
    context_manifest: dict[str, Any] = field(default_factory=dict)


def _merge_response_attribution(
    usage: dict[str, Any],
    response_id: str | None,
    attribution: dict[str, dict[str, Any]],
) -> None:
    if response_id is not None:
        usage.update(attribution.get(response_id, {}))


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
