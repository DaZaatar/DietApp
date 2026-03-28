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

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
