from raven_harness.config import Settings
from raven_harness.models.openai_agent import OpenAIAgentRunner, OpenRouterAgentRunner
from raven_harness.models.runner import create_llm_runner


async def test_factory_builds_openrouter_runner_with_shared_blocklist():
    runner = create_llm_runner(
        Settings(
            openrouter_token="test-token",
            openrouter_provider_blocklist="together,novita",
            _env_file=None,
        ),
        rulebook=None,
    )
    try:
        assert isinstance(runner, OpenRouterAgentRunner)
        settings = runner._model_settings(
            max_tokens=100,
            prompt_cache_key="cache",
            metadata=None,
            user="agent-id",
        )
        assert settings.extra_body == {
            "session_id": "raven-agent-agent-id",
            "provider": {"ignore": ["together", "novita"]},
        }
    finally:
        await runner.shutdown()


async def test_factory_builds_direct_openai_runner_without_router_fields():
    runner = create_llm_runner(
        Settings(openai_api_key="test-key", _env_file=None),
        rulebook=None,
    )
    try:
        assert isinstance(runner, OpenAIAgentRunner)
        settings = runner._model_settings(
            max_tokens=100,
            prompt_cache_key="cache",
            metadata=None,
            user="agent-id",
        )
        assert settings.extra_body is None
    finally:
        await runner.shutdown()
