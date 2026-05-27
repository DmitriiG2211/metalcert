from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyUrl, field_validator
from typing import List
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Metal Certificates Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/certificates_db"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/certificates_db"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_async_url(cls, v: str) -> str:
        if v.startswith("postgres://"):
            return "postgresql+asyncpg://" + v[len("postgres://"):]
        if v.startswith("postgresql://") and "+" not in v:
            return "postgresql+asyncpg://" + v[len("postgresql://"):]
        return v

    @field_validator("DATABASE_URL_SYNC", mode="before")
    @classmethod
    def fix_sync_url(cls, v: str) -> str:
        if v.startswith("postgres://"):
            return "postgresql+psycopg2://" + v[len("postgres://"):]
        if v.startswith("postgresql://") and "+" not in v:
            return "postgresql+psycopg2://" + v[len("postgresql://"):]
        return v

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "change-me-in-production-use-32-chars-minimum-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # File Upload
    UPLOAD_DIR: str = "uploads"
    PREVIEW_DIR: str = "uploads/previews"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50 MB
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "jpg", "jpeg", "png", "webp", "tiff", "tif"]
    ALLOWED_MIME_TYPES: List[str] = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/tiff",
    ]

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: List[str] = ["json"]
    CELERY_TIMEZONE: str = "Europe/Moscow"

    # OCR
    TESSERACT_CMD: str = "tesseract"
    OCR_CONFIDENCE_THRESHOLD: float = 0.7
    TESSERACT_LANG: str = "rus+eng"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
    ]

    @field_validator("UPLOAD_DIR", "PREVIEW_DIR", mode="before")
    @classmethod
    def create_dirs(cls, v: str) -> str:
        os.makedirs(v, exist_ok=True)
        return v


settings = Settings()
