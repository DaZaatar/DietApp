from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "DietApp"
    env: str = "dev"
    api_v1_prefix: str = "/api/v1"
    database_url: str

    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o-mini"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    media_backend: str = "local"
    media_local_root: str = "uploads"

    jwt_secret: str = "dev-only-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60 * 24 * 7
    # When True, X-User-Id is accepted without a Bearer token (local dev / tests).
    allow_dev_user_header: bool = True
    # When True and no JWT/header user, default to user id 1 (integration tests).
    allow_default_user: bool = True

    # If set (e.g. /app/static), serve built SPA from this directory (Docker / Railway).
    static_root: str = ""
    # Set True on HTTPS (Railway) so auth cookies are marked Secure.
    cookie_secure: bool = False

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_postgres_url(cls, v: object) -> object:
        """Railway/Heroku use postgres://; SQLAlchemy 2 + psycopg3 expect postgresql+psycopg://."""
        if not isinstance(v, str) or v.startswith("sqlite"):
            return v
        if v.startswith("postgresql+psycopg"):
            return v
        if v.startswith("postgres://"):
            return "postgresql+psycopg://" + v[len("postgres://") :]
        if v.startswith("postgresql://"):
            return "postgresql+psycopg://" + v[len("postgresql://") :]
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
