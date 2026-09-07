import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_ID = "z-ai/glm-5.3-flash"
DEFAULT_MODEL_MAX_OUTPUT_TOKENS = 16_384


def _source_checkout_root() -> Path | None:
    """Return the repository root when running from the source checkout."""

    package_root = Path(__file__).resolve().parent
    repository_root = package_root.parents[1]
    if (repository_root / "pyproject.toml").is_file() and (
        repository_root / "src" / "raven_harness" / "__init__.py"
    ).is_file():
        return repository_root
    return None


def _installed_data_root() -> Path:
    if os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support"
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return root / "raven-harness"


SOURCE_CHECKOUT_ROOT = _source_checkout_root()
RUNTIME_DATA_ROOT = (
    SOURCE_CHECKOUT_ROOT / "data"
    if SOURCE_CHECKOUT_ROOT is not None
    else _installed_data_root()
)


def _resolve_runtime_path(path: Path) -> Path:
    expanded = path.expanduser()
    if expanded.is_absolute():
        return expanded.resolve()
    base = SOURCE_CHECKOUT_ROOT or RUNTIME_DATA_ROOT
    return (base / expanded).resolve()


def _default_data_file(filename: str) -> Path:
    return Path(filename) if SOURCE_CHECKOUT_ROOT is None else Path("data") / filename


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    host: str = "127.0.0.1"
    port: int = 8787
    database_path: Path | None = None
    rules_path: Path | None = None
    model_id: str = Field(default=DEFAULT_MODEL_ID, min_length=1, max_length=100)
    openrouter_token: str = Field(default="", repr=False)
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openai_api_key: str = Field(default="", repr=False)
    openai_base_url: str = "https://api.openai.com/v1"
    model_request_timeout_seconds: float = Field(default=45, gt=0, le=300)
    model_run_timeout_seconds: float = Field(default=300, gt=0, le=1_800)
    model_max_output_tokens: int = Field(
        default=DEFAULT_MODEL_MAX_OUTPUT_TOKENS, ge=256, le=65_536
    )
    model_session_history_items: int = Field(default=32, ge=4, le=1_000)
    autoplay_max_consecutive_failures: int = Field(default=2, ge=1, le=20)
    autoplay_retry_base_seconds: float = Field(default=2, gt=0, le=60)
    openrouter_provider_order: str = (
        "reka,cloudflare,coreweave,fireworks,deepinfra,together"
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
        path = self.database_path or _default_data_file("harness.db")
        return _resolve_runtime_path(path)

    @property
    def resolved_rules_path(self) -> Path:
        path = self.rules_path or _default_data_file("rules.json")
        return _resolve_runtime_path(path)

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
        return urlsplit(self.model_base_url).hostname or "configured-model-endpoint"

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
