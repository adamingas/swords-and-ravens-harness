"""Construct the endpoint-specific implementation of the shared LLM agent."""

from __future__ import annotations

from ..config import Settings
from ..rulebook import Rulebook
from .openai_agent import LLMAgentRunner, OpenAIAgentRunner, OpenRouterAgentRunner


def create_llm_runner(
    settings: Settings,
    *,
    rulebook: Rulebook | None,
) -> LLMAgentRunner:
    common = {"rulebook": rulebook}
    if settings.uses_openrouter:
        return OpenRouterAgentRunner(
            api_key=settings.openrouter_token,
            base_url=settings.openrouter_base_url,
            provider_blocklist=settings.openrouter_blocked_providers,
            **common,
        )
    return OpenAIAgentRunner(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        **common,
    )
