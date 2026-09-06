from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _project_path(path: Path) -> Path:
    expanded = path.expanduser()
    if expanded.is_absolute():
        return expanded.resolve()
    return (PROJECT_ROOT / expanded).resolve()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    host: str = "127.0.0.1"
    port: int = 8787
    database_path: Path = Path("./data/harness.db")
    rules_path: Path = Path("./data/rules.json")
    model_id: str = Field(default="z-ai/glm-5.3-flash", min_length=1, max_length=100)
    openrouter_token: str = Field(default="", repr=False)
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openai_api_key: str = Field(default="", repr=False)
    openai_base_url: str = "https://api.openai.com/v1"
    model_request_timeout_seconds: float = Field(default=45, gt=0, le=600)
    model_run_timeout_seconds: float = Field(default=300, gt=0, le=1_800)
    model_api_max_retries: int = Field(default=2, ge=0, le=10)
    model_max_concurrency: int = Field(default=1, ge=1, le=32)
    model_max_output_tokens: int = Field(default=16_384, ge=256, le=65_536)
    model_session_history_items: int = Field(default=32, ge=4, le=1_000)
    autoplay_max_consecutive_failures: int = Field(default=5, ge=1, le=20)
    autoplay_retry_base_seconds: float = Field(default=2, gt=0, le=60)
    openrouter_provider_order: str = (
        "cloudflare,reka,deepinfra,io-net,together,wafer"
    )
    openrouter_allow_unlisted_providers: bool = False
    openrouter_provider_sort: str = Field(
        default="throughput", pattern="^(price|throughput|latency)$"
    )
    openrouter_allow_fallbacks: bool = True
    openrouter_require_parameters: bool = False
    otel_exporter_otlp_traces_endpoint: str = ""
    otel_service_name: str = "raven-harness"

    @property
    def resolved_database_path(self) -> Path:
        return _project_path(self.database_path)

    @property
    def resolved_rules_path(self) -> Path:
        return _project_path(self.rules_path)

    @property
    def model_api_key(self) -> str:
        return self.openrouter_token or self.openai_api_key

    @property
    def model_base_url(self) -> str:
        return (
            self.openrouter_base_url if self.openrouter_token else self.openai_base_url
        )

    @property
    def model_provider(self) -> str:
        return "OpenRouter" if self.openrouter_token else "OpenAI"

    @property
    def openrouter_provider_routing(self) -> dict[str, Any]:
        order = _comma_separated(self.openrouter_provider_order)
        routing: dict[str, Any] = {
            "allow_fallbacks": self.openrouter_allow_fallbacks,
            "require_parameters": self.openrouter_require_parameters,
        }
        if order:
            routing["order"] = order
            if not self.openrouter_allow_unlisted_providers:
                routing["only"] = order
        else:
            routing["sort"] = self.openrouter_provider_sort
        return routing


def _comma_separated(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]
