"""Endpoint configuration composed with either execution harness."""

from dataclasses import dataclass
from typing import Any, Protocol

from openai import AsyncOpenAI


class ResponseProvider(Protocol):
    client: AsyncOpenAI
    configured: bool

    def request_extra_body(self, *, user: str | None) -> dict[str, Any]: ...


@dataclass
class OpenAIProvider:
    client: AsyncOpenAI
    configured: bool = True

    def request_extra_body(self, *, user: str | None) -> dict[str, Any]:
        return {}


@dataclass
class OpenRouterProvider:
    client: AsyncOpenAI
    blocked_providers: tuple[str, ...]
    configured: bool = True

    def request_extra_body(self, *, user: str | None) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if user:
            body["session_id"] = f"raven-agent-{user}"
        blocked = list(
            dict.fromkeys(
                provider.strip().lower()
                for provider in self.blocked_providers
                if provider.strip()
            )
        )
        if blocked:
            body["provider"] = {"ignore": blocked}
        return body
