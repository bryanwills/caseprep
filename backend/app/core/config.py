"""
Configuration settings for CasePrep backend.
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""

    # Application
    APP_NAME: str = "CasePrep"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")

    # Security
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")

    # Storage
    STORAGE_BACKEND: str = Field(default="local", env="STORAGE_BACKEND")  # local, s3, minio
    STORAGE_PATH: str = Field(default="/tmp/caseprep", env="STORAGE_PATH")

    # S3/MinIO Configuration
    S3_ENDPOINT: Optional[str] = Field(default=None, env="S3_ENDPOINT")
    S3_ACCESS_KEY: Optional[str] = Field(default=None, env="S3_ACCESS_KEY")
    S3_SECRET_KEY: Optional[str] = Field(default=None, env="S3_SECRET_KEY")
    S3_BUCKET: Optional[str] = Field(default=None, env="S3_BUCKET")
    S3_REGION: Optional[str] = Field(default=None, env="S3_REGION")
    S3_USE_SSL: bool = Field(default=True, env="S3_USE_SSL")

    # File Upload
    MAX_UPLOAD_SIZE: int = Field(default=2 * 1024 * 1024 * 1024, env="MAX_UPLOAD_SIZE")  # 2GB
    ALLOWED_EXTENSIONS: List[str] = Field(
        default=["mp4", "mov", "avi", "wmv", "flv", "webm", "mp3", "wav", "m4a", "flac", "ogg", "aac"],
        env="ALLOWED_EXTENSIONS"
    )

    # Transcription Settings
    WHISPER_MODEL_SIZE: str = Field(default="large-v3", env="WHISPER_MODEL_SIZE")
    WHISPER_DEVICE: str = Field(default="cuda" if os.environ.get("CUDA_VISIBLE_DEVICES") else "cpu", env="WHISPER_DEVICE")
    WHISPER_COMPUTE_TYPE: str = Field(default="float16", env="WHISPER_COMPUTE_TYPE")
    WHISPER_MODEL_CACHE_DIR: str = Field(default="/tmp/whisper_models", env="WHISPER_MODEL_CACHE_DIR")

    # Speaker Diarization
    ENABLE_DIARIZATION: bool = Field(default=True, env="ENABLE_DIARIZATION")
    PYANNOTE_AUTH_TOKEN: Optional[str] = Field(default=None, env="PYANNOTE_AUTH_TOKEN")
    PYANNOTE_MODEL: str = Field(default="pyannote/speaker-diarization-3.1", env="PYANNOTE_MODEL")

    # Processing
    MAX_CONCURRENT_JOBS: int = Field(default=4, env="MAX_CONCURRENT_JOBS")
    JOB_TIMEOUT_SECONDS: int = Field(default=3600, env="JOB_TIMEOUT_SECONDS")  # 1 hour

    # Retention
    DEFAULT_RETENTION_DAYS: int = Field(default=0, env="DEFAULT_RETENTION_DAYS")
    MAX_RETENTION_DAYS: int = Field(default=365, env="MAX_RETENTION_DAYS")

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        env="CORS_ORIGINS"
    )

    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")

    # Monitoring
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    METRICS_PORT: int = Field(default=9090, env="METRICS_PORT")

    # Email (for notifications)
    SMTP_HOST: Optional[str] = Field(default=None, env="SMTP_HOST")
    SMTP_PORT: Optional[int] = Field(default=None, env="SMTP_PORT")
    SMTP_USERNAME: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    SMTP_USE_TLS: bool = Field(default=True, env="SMTP_USE_TLS")

    # Feature Flags
    ENABLE_ANONYMOUS_LEARNING: bool = Field(default=False, env="ENABLE_ANONYMOUS_LEARNING")
    ENABLE_CLIENT_SIDE_ENCRYPTION: bool = Field(default=False, env="ENABLE_CLIENT_SIDE_ENCRYPTION")
    ENABLE_REAL_TIME_PROCESSING: bool = Field(default=False, env="ENABLE_REAL_TIME_PROCESSING")

    # Performance
    WORKER_PROCESSES: int = Field(default=1, env="WORKER_PROCESSES")
    WORKER_THREADS: int = Field(default=4, env="WORKER_THREADS")

    # Cache
    CACHE_TTL: int = Field(default=300, env="CACHE_TTL")  # 5 minutes
    CACHE_MAX_SIZE: int = Field(default=1000, env="CACHE_MAX_SIZE")

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_WINDOW: int = Field(default=60, env="RATE_LIMIT_WINDOW")  # 1 minute

    # Backup
    BACKUP_ENABLED: bool = Field(default=False, env="BACKUP_ENABLED")
    BACKUP_SCHEDULE: str = Field(default="0 2 * * *", env="BACKUP_SCHEDULE")  # Daily at 2 AM
    BACKUP_RETENTION_DAYS: int = Field(default=30, env="BACKUP_RETENTION_DAYS")

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings