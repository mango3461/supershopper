from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(
        default="SuperShopper Backend",
        validation_alias="APP_NAME",
    )
    app_env: str = Field(default="development", validation_alias="APP_ENV")
    llm_provider: str = Field(default="mock", validation_alias="LLM_PROVIDER")
    search_provider: str = Field(default="mock", validation_alias="SEARCH_PROVIDER")
    cache_provider: str = Field(default="mock", validation_alias="CACHE_PROVIDER")
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    google_api_key: str | None = Field(default=None, validation_alias="GOOGLE_API_KEY")
    serpapi_api_key: str | None = Field(default=None, validation_alias="SERPAPI_API_KEY")
    serpapi_engine: str = Field(default="google_shopping", validation_alias="SERPAPI_ENGINE")
    serpapi_expert_engine: str = Field(default="google", validation_alias="SERPAPI_EXPERT_ENGINE")
    serpapi_base_url: str = Field(
        default="https://serpapi.com/search.json",
        validation_alias="SERPAPI_BASE_URL",
    )
    serpapi_google_domain: str = Field(
        default="google.com",
        validation_alias="SERPAPI_GOOGLE_DOMAIN",
    )
    serpapi_gl: str = Field(default="kr", validation_alias="SERPAPI_GL")
    serpapi_hl: str = Field(default="ko", validation_alias="SERPAPI_HL")
    serpapi_device: str = Field(default="desktop", validation_alias="SERPAPI_DEVICE")
    serpapi_location: str | None = Field(default=None, validation_alias="SERPAPI_LOCATION")
    serpapi_num: int = Field(default=6, validation_alias="SERPAPI_NUM")
    serpapi_timeout_seconds: float = Field(
        default=20.0,
        validation_alias="SERPAPI_TIMEOUT_SECONDS",
    )
    redis_url: str | None = Field(default=None, validation_alias="REDIS_URL")


@lru_cache
def get_settings() -> Settings:
    return Settings()
