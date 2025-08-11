"""
Application configuration management using Pydantic Settings.
"""

import secrets
from functools import lru_cache
from typing import List, Optional, Union

from pydantic import AnyHttpUrl, EmailStr, Field, PostgresDsn, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with validation and environment variable support.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore"
    )
    
    # Application Settings
    ENVIRONMENT: str = Field(default="development", description="Application environment")
    DEBUG: bool = Field(default=False, description="Debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    
    # API Settings
    API_V1_STR: str = Field(default="/api/v1", description="API v1 prefix")
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24 * 8, description="8 days")
    REFRESH_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24 * 30, description="30 days")
    
    # Security Settings
    ALLOWED_HOSTS: List[str] = Field(default=["localhost", "127.0.0.1"])
    CORS_ORIGINS: List[AnyHttpUrl] = Field(
        default=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://app.caseprep.com"
        ]
    )
    
    # Database Settings
    DATABASE_URL: PostgresDsn = Field(
        default="postgresql+asyncpg://caseprep:caseprep@localhost:5432/caseprep",
        description="PostgreSQL database URL"
    )
    DATABASE_POOL_SIZE: int = Field(default=10, description="Database connection pool size")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, description="Database max overflow connections")
    
    # Redis Settings
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis URL for caching")
    REDIS_CELERY_BROKER: str = Field(default="redis://localhost:6379/1", description="Celery broker URL")
    REDIS_CELERY_BACKEND: str = Field(default="redis://localhost:6379/2", description="Celery result backend URL")
    
    # Storage Settings
    STORAGE_BACKEND: str = Field(default="minio", description="Storage backend: minio, s3, local")
    
    # MinIO/S3 Settings
    MINIO_ENDPOINT: str = Field(default="localhost:9000", description="MinIO endpoint")
    MINIO_ACCESS_KEY: str = Field(default="minio", description="MinIO access key")
    MINIO_SECRET_KEY: str = Field(default="minio123", description="MinIO secret key")
    MINIO_SECURE: bool = Field(default=False, description="Use HTTPS for MinIO")
    MINIO_BUCKET_NAME: str = Field(default="caseprep", description="Default bucket name")
    
    # AWS S3 Settings (if using S3 instead of MinIO)
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None, description="AWS access key")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None, description="AWS secret key")
    AWS_S3_BUCKET_NAME: Optional[str] = Field(default=None, description="S3 bucket name")
    AWS_S3_REGION: str = Field(default="us-east-1", description="S3 region")
    
    # File Upload Settings
    MAX_UPLOAD_SIZE_MB: int = Field(default=500, description="Maximum file upload size in MB")
    ALLOWED_AUDIO_EXTENSIONS: List[str] = Field(
        default=["mp3", "wav", "m4a", "flac", "ogg", "aac"],
        description="Allowed audio file extensions"
    )
    ALLOWED_VIDEO_EXTENSIONS: List[str] = Field(
        default=["mp4", "avi", "mov", "wmv", "flv", "webm", "mkv"],
        description="Allowed video file extensions"
    )
    
    # AI/ML Settings
    WHISPER_MODEL_SIZE: str = Field(default="large-v3", description="Whisper model size")
    WHISPER_DEVICE: str = Field(default="cpu", description="Device for Whisper: cpu, cuda")
    WHISPER_COMPUTE_TYPE: str = Field(default="float32", description="Whisper compute type")
    ENABLE_DIARIZATION: bool = Field(default=True, description="Enable speaker diarization")
    DIARIZATION_MIN_SPEAKERS: int = Field(default=1, description="Minimum number of speakers")
    DIARIZATION_MAX_SPEAKERS: int = Field(default=10, description="Maximum number of speakers")
    
    # Background Task Settings
    CELERY_TASK_ALWAYS_EAGER: bool = Field(default=False, description="Execute tasks synchronously")
    CELERY_WORKER_CONCURRENCY: int = Field(default=2, description="Celery worker concurrency")
    CELERY_TASK_SOFT_TIME_LIMIT: int = Field(default=3600, description="Soft time limit for tasks (1 hour)")
    CELERY_TASK_TIME_LIMIT: int = Field(default=7200, description="Hard time limit for tasks (2 hours)")
    
    # Email Settings (for notifications)
    SMTP_TLS: bool = Field(default=True, description="Use TLS for SMTP")
    SMTP_PORT: Optional[int] = Field(default=587, description="SMTP port")
    SMTP_HOST: Optional[str] = Field(default=None, description="SMTP host")
    SMTP_USER: Optional[str] = Field(default=None, description="SMTP username")
    SMTP_PASSWORD: Optional[str] = Field(default=None, description="SMTP password")
    EMAILS_FROM_EMAIL: Optional[EmailStr] = Field(default=None, description="From email address")
    EMAILS_FROM_NAME: Optional[str] = Field(default="CasePrep", description="From name")
    
    # Monitoring Settings
    SENTRY_DSN: Optional[str] = Field(default=None, description="Sentry DSN for error tracking")
    ENABLE_METRICS: bool = Field(default=True, description="Enable metrics collection")
    METRICS_PORT: int = Field(default=8001, description="Metrics server port")
    
    # Legal/Compliance Settings
    DEFAULT_RETENTION_DAYS: int = Field(default=0, description="Default data retention in days (0 = no retention)")
    REQUIRE_AUDIT_LOG: bool = Field(default=True, description="Require audit logging")
    ENABLE_CHAIN_OF_CUSTODY: bool = Field(default=True, description="Enable chain of custody tracking")
    MAX_CONCURRENT_TRANSCRIPTIONS: int = Field(default=5, description="Max concurrent transcription jobs per tenant")
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable API rate limiting")
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(default=100, description="Requests per minute per IP")
    RATE_LIMIT_BURST: int = Field(default=200, description="Burst capacity for rate limiting")
    
    # Feature Flags
    ENABLE_GLOBAL_LEARNING: bool = Field(default=False, description="Enable global learning features")
    ENABLE_REAL_TIME_TRANSCRIPTION: bool = Field(default=False, description="Enable real-time transcription")
    ENABLE_MULTI_LANGUAGE: bool = Field(default=False, description="Enable multi-language support")
    
    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        allowed = ["development", "staging", "production", "testing"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of: {allowed}")
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of: {allowed}")
        return v.upper()
    
    @validator("STORAGE_BACKEND")
    def validate_storage_backend(cls, v):
        allowed = ["minio", "s3", "local"]
        if v not in allowed:
            raise ValueError(f"STORAGE_BACKEND must be one of: {allowed}")
        return v
    
    @validator("WHISPER_DEVICE")
    def validate_whisper_device(cls, v):
        allowed = ["cpu", "cuda"]
        if v not in allowed:
            raise ValueError(f"WHISPER_DEVICE must be one of: {allowed}")
        return v
    
    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @property
    def DATABASE_URL_SYNC(self) -> str:
        """Synchronous database URL for Alembic."""
        return str(self.DATABASE_URL).replace("+asyncpg", "")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"
    
    @property
    def MAX_UPLOAD_SIZE_BYTES(self) -> int:
        """Maximum upload size in bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    """
    return Settings()