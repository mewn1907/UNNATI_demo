"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import List

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central, typed application settings.

    All secrets are read from the environment (or a local .env file) and are
    never hard-coded anywhere in the codebase.
    """

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_ENV: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str = "sqlite:///./Unnati.db"

    # LLM configuration (OpenAI-compatible providers such as OpenRouter).
    LLM_ENABLED: bool = True
    LLM_PROVIDER: str = "openrouter"
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_MODEL: str = "openrouter/auto"
    LLM_TEMPERATURE: float = 0.2
    LLM_TIMEOUT_SECONDS: int = 30

    # Weather enrichment (optional).
    WEATHER_ENABLED: bool = False
    WEATHER_API_KEY: str = ""

    CORS_ORIGINS: str = "http://localhost:5173"

    DEMO_MODE: bool = True

    # Matching constraints.
    MAX_POOL_RADIUS_KM: float = 40.0
    MAX_HARVEST_TIME_DIFF_HOURS: float = 24.0
    MIN_LISTING_QUANTITY_KG: float = 50.0

    # Transport model constants (INR).
    TRANSPORT_FIXED_COST: float = 500.0
    TRANSPORT_COST_PER_KM: float = 18.0
    RETURN_TRIP_DISCOUNT: float = 0.35

    # Legacy alias kept for compatibility with existing local .env files.
    OPENROUTER_API_KEY: str = ""

    @model_validator(mode="after")
    def _accept_legacy_key_names(self) -> "Settings":
        if not self.LLM_API_KEY and self.OPENROUTER_API_KEY:
            self.LLM_API_KEY = self.OPENROUTER_API_KEY
        return self

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
