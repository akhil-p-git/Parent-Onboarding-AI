"""
Application Configuration.

Uses Pydantic BaseSettings for environment variable management.
"""

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Zapier Triggers API"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = Field(default="development", description="Environment: development, staging, production")
    DEBUG: bool = Field(default=True, description="Enable debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # Server
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # Database - either use DATABASE_URL directly or construct from components
    DATABASE_URL: str | None = Field(
        default=None,
        description="PostgreSQL connection string (takes precedence if set)",
    )
    # Individual database components (used when DATABASE_URL is not provided)
    DB_HOST: str | None = Field(default=None, description="Database host")
    DB_PORT: str | None = Field(default="5432", description="Database port")
    DB_NAME: str | None = Field(default=None, description="Database name")
    DB_USER: str | None = Field(default=None, description="Database user")
    DB_PASSWORD: str | None = Field(default=None, description="Database password")

    DATABASE_POOL_SIZE: int = Field(default=20, description="Database connection pool size")
    DATABASE_MAX_OVERFLOW: int = Field(default=10, description="Max overflow connections")

    @model_validator(mode="after")
    def construct_database_url(self) -> "Settings":
        """Construct DATABASE_URL from components if not provided directly."""
        if self.DATABASE_URL is None:
            if all([self.DB_HOST, self.DB_USER, self.DB_PASSWORD, self.DB_NAME]):
                self.DATABASE_URL = (
                    f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
                    f"@{self.DB_HOST}:{self.DB_PORT or '5432'}/{self.DB_NAME}"
                )
            else:
                # Fallback to local development default
                self.DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/triggers_db"
        return self

    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection string",
    )
    CACHE_TTL: int = Field(default=3600, description="Default cache TTL in seconds")

    # AWS
    AWS_REGION: str = Field(default="us-east-1", description="AWS region")
    AWS_ACCESS_KEY_ID: str | None = Field(default=None, description="AWS access key")
    AWS_SECRET_ACCESS_KEY: str | None = Field(default=None, description="AWS secret key")

    # SQS Queues
    SQS_EVENTS_QUEUE_URL: str | None = Field(default=None, description="Events queue URL")
    SQS_DELIVERY_QUEUE_URL: str | None = Field(default=None, description="Delivery queue URL")
    SQS_DLQ_URL: str | None = Field(default=None, description="Dead letter queue URL")

    # Security
    API_KEY_SECRET: str = Field(
        default="development-secret-change-in-production",
        description="Secret for hashing API keys",
    )
    WEBHOOK_SIGNING_SECRET: str = Field(
        default="webhook-secret-change-in-production",
        description="Secret for signing webhooks",
    )

    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(default=1000, description="Rate limit per minute")
    RATE_LIMIT_BURST: int = Field(default=100, description="Rate limit burst allowance")

    # Feature Flags
    ENABLE_WEBHOOK_DELIVERY: bool = Field(default=True, description="Enable webhook delivery")
    ENABLE_EVENT_REPLAY: bool = Field(default=False, description="Enable event replay")
    ENABLE_SCHEMA_VALIDATION: bool = Field(default=False, description="Enable schema validation")

    # Tracing / OpenTelemetry
    ENABLE_TRACING: bool = Field(default=False, description="Enable OpenTelemetry tracing")
    TRACING_EXPORTER: str = Field(
        default="otlp",
        description="Tracing exporter: otlp, xray, console, none",
    )
    TRACING_SAMPLE_RATE: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Trace sampling rate (0.0-1.0)",
    )
    OTLP_ENDPOINT: str = Field(
        default="http://localhost:4317",
        description="OTLP collector endpoint",
    )

    # Metrics
    ENABLE_METRICS: bool = Field(default=True, description="Enable Prometheus metrics")
    METRICS_PREFIX: str = Field(default="zapier_triggers", description="Metrics prefix")

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.APP_ENV == "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
