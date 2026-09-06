from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    host: str = "127.0.0.1"
    port: int = 8787
    database_path: Path = Path("./data/harness.db")
    rules_path: Path = Path("./data/rules.json")
    openrouter_token: str = Field(default="", repr=False)
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openai_api_key: str = Field(default="", repr=False)
    openai_base_url: str = "https://api.openai.com/v1"
    model_request_timeout_seconds: float = Field(default=45, gt=0, le=600)
    model_run_timeout_seconds: float = Field(default=150, gt=0, le=1_800)
    model_api_max_retries: int = Field(default=2, ge=0, le=10)
    model_max_concurrency: int = Field(default=1, ge=1, le=32)
    model_max_output_tokens: int = Field(default=2_048, ge=256, le=65_536)
    openrouter_provider_sort: str = Field(
        default="throughput", pattern="^(price|throughput|latency)$"
    )
    openrouter_allow_fallbacks: bool = True
    openrouter_require_parameters: bool = False

    @property
    def resolved_database_path(self) -> Path:
        return self.database_path.expanduser().resolve()

    @property
    def resolved_rules_path(self) -> Path:
        return self.rules_path.expanduser().resolve()

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
