"""Application settings loaded from environment variables and the repo-root .env file."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to this file so it is found no matter where the app is started from.
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    # .env also holds variables for docker compose (POSTGRES_*), so ignore unknown keys.
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    # No defaults: a missing value fails fast at startup.
    database_url: str
    redis_url: str
    jwt_secret: str


settings = Settings()
