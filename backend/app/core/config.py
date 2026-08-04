"""Application settings loaded from environment variables.

The `python-dotenv` package reads variables from a local `.env` file during
development. In production, hosts like Render provide the same values through
their dashboard instead.
"""

from functools import lru_cache

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Load values from `.env` before Pydantic reads environment variables.
load_dotenv()


class Settings(BaseSettings):
    """Typed configuration values used throughout the app."""

    app_name: str = "Chat With Your Notes"
    environment: str = "development"

    # These are already expected to exist in your local `.env` file.
    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")

    # JWT settings will be used in the auth step.
    secret_key: str = Field(default="change-this-local-dev-secret", alias="SECRET_KEY")
    access_token_expire_minutes: int = 60 * 24

    # Local frontend origins allowed to call the API in development.
    cors_origins: list[str] = [
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return one cached Settings object instead of rebuilding it repeatedly."""

    return Settings()
