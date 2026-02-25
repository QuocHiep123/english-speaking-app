# =============================================================================
# Application Configuration
# =============================================================================

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "VietSpeak AI"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/vietspeak"
    REDIS_URL: str = "redis://localhost:6379/0"

    # AI Models
    WHISPER_MODEL: str = "base"  # tiny, base, small, medium, large
    PRONUNCIATION_MODEL_PATH: str = "models/pronunciation_scorer"
    USE_GPU: bool = True

    # Audio Processing
    AUDIO_SAMPLE_RATE: int = 16000
    AUDIO_MAX_DURATION: int = 30  # seconds

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # MCP Server
    MCP_ENABLED: bool = True
    MCP_SERVER_NAME: str = "vietspeak-pronunciation"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
