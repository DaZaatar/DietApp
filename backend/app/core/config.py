import os
from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _normalize_postgres_url(url: str) -> str:
    """Railway/Heroku use postgres://; SQLAlchemy 2 + psycopg3 expect postgresql+psycopg://."""
    if url.startswith("sqlite"):
        return url
    if url.startswith("postgresql+psycopg"):
        return url
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "DietApp"
    env: str = "dev"
    api_v1_prefix: str = "/api/v1"
    # From env DATABASE_URL (or resolved in model_validator).
    database_url: str = ""

    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o-mini"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    media_backend: str = "local"
    media_local_root: str = "uploads"

    jwt_secret: str = "dev-only-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60 * 24 * 7
    allow_dev_user_header: bool = True
    allow_default_user: bool = True

    static_root: str = ""
    cookie_secure: bool = False

    @model_validator(mode="after")
    def resolve_database_url(self) -> Self:
        url = (self.database_url or "").strip()
        if not url:
            url = (
                os.environ.get("DATABASE_URL", "").strip()
                or os.environ.get("POSTGRES_URL", "").strip()
            )
        if not url:
            if os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("RAILWAY"):
                raise ValueError(
                    "DATABASE_URL is missing. On Railway: add a PostgreSQL database, open this service → "
                    "Variables → New variable → Variable Reference → choose DATABASE_URL from the Postgres service."
                )
            url = "sqlite:///./dietapp_dev.db"
        object.__setattr__(self, "database_url", _normalize_postgres_url(url))
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
