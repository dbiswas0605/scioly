"""Application configuration, loaded from environment variables / .env file."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the scioly backend."""

    database_url: str = Field(
        default="postgresql+psycopg://scioly:scioly_dev_password@localhost:5432/scioly",
        validation_alias="DATABASE_URL",
    )
    cors_origins_raw: str = Field(
        default="http://localhost:3000",
        validation_alias="CORS_ORIGINS",
    )
    env: str = Field(default="development", validation_alias="ENV")

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        """Parse the comma-separated CORS_ORIGINS env var into a list."""
        return [
            origin.strip()
            for origin in self.cors_origins_raw.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
