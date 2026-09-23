"""Compose the gameplay adapter from independently selected execution and provider."""

from functools import partial

from openai import AsyncOpenAI

from ..agent_store import AgentStore
from ..config import Settings
from ..models.providers import OpenAIProvider, OpenRouterProvider
from ..rulebook import Rulebook
from .execution import StructuredOutputHarness, TwoStageHarness
from .gameplay import GameHarness
from .prompts import EXPLORATION_INSTRUCTIONS, FINALIZE_PROMPT, STRUCTURED_INSTRUCTIONS


def create_game_harness(
    settings: Settings, store: AgentStore, *, rulebook: Rulebook | None = None
) -> GameHarness:
    client = AsyncOpenAI(
        api_key=settings.model_api_key or "not-configured",
        base_url=settings.model_base_url,
        timeout=None,
        max_retries=0,
    )
    if settings.uses_openrouter:
        provider = OpenRouterProvider(
            client,
            tuple(settings.openrouter_blocked_providers),
            bool(settings.model_api_key),
        )
    else:
        provider = OpenAIProvider(client, bool(settings.model_api_key))
    if settings.harness_mode == "two-stage":
        execution = partial(
            TwoStageHarness,
            finalize_prompt=FINALIZE_PROMPT,
            max_turns=settings.harness_max_turns,
        )
        instructions = EXPLORATION_INSTRUCTIONS
    else:
        execution = partial(
            StructuredOutputHarness, max_turns=settings.harness_max_turns
        )
        instructions = STRUCTURED_INSTRUCTIONS
    return GameHarness(
        store,
        provider,
        execution,
        instructions,
        rulebook,
        settings.model_max_output_tokens,
    )
