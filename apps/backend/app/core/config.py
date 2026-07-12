from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Type-validated app config, sourced from environment variables.
    Missing/invalid required values fail at startup, not mid-request.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_name: str = "Orin"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False

    secret_key: str = "dev-only-change-me"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    postgres_user: str = "orin"
    postgres_password: str = "orin"
    postgres_db: str = "orin"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    chroma_host: str = "localhost"
    chroma_port: int = 8000

    ai_provider: str = "gemini"
    ai_api_key: str | None = None
    ai_model: str = "models/gemini-embedding-001"
    ai_embedding_dimensions: int = 3072

    # Chat completion settings
    ai_chat_model: str = "gemini-2.5-flash"
    ai_chat_temperature: float = 0.2
    chat_retrieval_top_k: int = 6

    # Document storage settings
    upload_dir: str = "uploads"
    max_file_size_mb: int = 10
    allowed_mime_types: list[str] = [
        "application/pdf",
        "text/plain",
        "text/markdown",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]

    # Embedding settings
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # CORS settings
    cors_origins_str: str = "http://localhost:3000"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_str.split(",")]

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    """Cached, injectable via FastAPI Depends(get_settings)."""
    return Settings()
