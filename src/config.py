"""
Module: src/config.py
Purpose: Centralized runtime configuration for ScrapeSignal
Author: ScrapeSignal Team
Created: 2026-05-10

Dependencies:
    - pydantic-settings (environment-driven settings)

Used by:
    - src.logger (logging configuration)
    - src.db (database connection)
    - src.main (orchestrator)
    - src.scrapers.* (external API configuration)
    - src.email.* (delivery configuration)
"""

# Standard library
from functools import lru_cache
from typing import Literal

# Third-party
from pydantic import EmailStr, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigError(RuntimeError):
    """Raised when required production configuration is missing or invalid."""


class Settings(BaseSettings):
    """Environment-driven settings for ScrapeSignal.

    Settings are loaded from environment variables and an optional local `.env`
    file. Secret values are represented as `SecretStr` so accidental string
    conversion does not expose their contents in logs.

    Raises:
        ConfigError: When `validate_for_production` finds missing required
            settings for a live run.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    ENVIRONMENT: Literal["development", "test", "staging", "production"] = "development"
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_FORMAT: Literal["text", "json"] = "text"
    DRY_RUN: bool = True

    DATABASE_URL: str = "postgresql+psycopg://user:password@localhost:5432/scrapesignal"
    DATABASE_POOL_SIZE: int = Field(default=5, ge=1, le=20)
    DATABASE_MAX_OVERFLOW: int = Field(default=10, ge=0, le=50)
    DATABASE_POOL_RECYCLE_SECONDS: int = Field(default=3600, ge=300)

    RECIPIENT_EMAIL: EmailStr = "sunil.lalwani@quidelortho.com"
    SENDER_EMAIL: EmailStr = "scrapesignal@example.com"
    SENDER_NAME: str = "ScrapeSignal"
    EMAIL_SUBJECT_PREFIX: str = "ScrapeSignal Daily Brief"
    ARTICLES_PER_EMAIL: int = Field(default=20, ge=1, le=50)

    DELIVERY_TIME_IST: str = "07:00"
    DELIVERY_TIME_UTC: str = "01:30"
    CRON_SCHEDULE: str = "30 1 * * *"
    TIMEZONE: str = "Asia/Kolkata"

    MIN_RELEVANCE_SCORE: float = Field(default=70.0, ge=0.0, le=100.0)
    DEDUPLICATION_WINDOW_DAYS: int = Field(default=30, ge=1, le=365)
    KEEP_ARTICLES_DAYS: int = Field(default=90, ge=1, le=3650)
    MAX_EXECUTION_MINUTES: int = Field(default=10, ge=1, le=60)

    SCRAPE_TIMEOUT_SECONDS: float = Field(default=30.0, ge=1.0, le=120.0)
    SCRAPE_CONNECT_TIMEOUT_SECONDS: float = Field(default=5.0, ge=1.0, le=30.0)
    SCRAPE_CONCURRENCY: int = Field(default=14, ge=1, le=50)
    PDF_TIMEOUT_SECONDS: float = Field(default=30.0, ge=1.0, le=120.0)
    MAX_ARTICLES_PER_SOURCE: int = Field(default=150, ge=1, le=1000)
    USER_AGENT: str = "ScrapeSignal/0.1 (+https://github.com/scrapesignal)"

    FIRECRAWL_API_KEY: SecretStr = SecretStr("")
    JINA_API_KEY: SecretStr = SecretStr("")
    APIFY_API_TOKEN: SecretStr = SecretStr("")
    ANTHROPIC_API_KEY: SecretStr = SecretStr("")
    CLAUDE_MODEL: str = "claude-3-5-sonnet-20241022"
    CLAUDE_MAX_TOKENS: int = Field(default=1200, ge=100, le=8192)
    CLAUDE_REQUESTS_PER_MINUTE: int = Field(default=20, ge=1, le=1000)
    USE_BATCH_API: bool = False
    BATCH_MIN_ARTICLES: int = Field(default=50, ge=1, le=1000)
    SENDGRID_API_KEY: SecretStr = SecretStr("")

    SLACK_WEBHOOK_URL: SecretStr = SecretStr("")
    SLACK_ALERT_SEVERITY_THRESHOLD: Literal["info", "warning", "error", "critical"] = (
        "error"
    )

    LOG_FILE_PATH: str = "scrapesignal.log"
    LOG_FILE_MAX_BYTES: int = Field(default=10_485_760, ge=1024)
    LOG_FILE_BACKUP_COUNT: int = Field(default=5, ge=1, le=20)

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        """Validate that the database URL uses async SQLAlchemy driver syntax.

        Args:
            value: Database URL from environment.

        Returns:
            Validated database URL.

        Raises:
            ValueError: If the URL is empty or not async-driver compatible.
        """
        if not value:
            raise ValueError("DATABASE_URL is required")
        valid_prefixes = (
            "postgresql://",
            "postgresql+psycopg://",
            "postgresql+asyncpg://",
        )
        if not value.startswith(valid_prefixes):
            raise ValueError(
                "DATABASE_URL must start with postgresql://, "
                "postgresql+psycopg://, or postgresql+asyncpg://"
            )
        return value

    @field_validator("DELIVERY_TIME_IST")
    @classmethod
    def validate_delivery_time(cls, value: str) -> str:
        """Validate HH:MM delivery time format.

        Args:
            value: Delivery time string.

        Returns:
            Validated delivery time.

        Raises:
            ValueError: If the delivery time is not exactly 07:00.
        """
        if value != "07:00":
            raise ValueError("DELIVERY_TIME_IST must be 07:00")
        return value

    @field_validator("CRON_SCHEDULE")
    @classmethod
    def validate_cron_schedule(cls, value: str) -> str:
        """Validate the required GitHub Actions UTC cron schedule.

        Args:
            value: Cron expression.

        Returns:
            Validated cron expression.

        Raises:
            ValueError: If the expression is not the required 01:30 UTC schedule.
        """
        if value != "30 1 * * *":
            raise ValueError("CRON_SCHEDULE must be 30 1 * * * for 7:00 AM IST")
        return value

    @model_validator(mode="after")
    def validate_core_contract(self) -> "Settings":
        """Validate non-negotiable ScrapeSignal constants.

        Returns:
            Validated settings instance.

        Raises:
            ValueError: If core delivery or scoring constants drift from spec.
        """
        if self.RECIPIENT_EMAIL != "sunil.lalwani@quidelortho.com":
            raise ValueError("RECIPIENT_EMAIL must be sunil.lalwani@quidelortho.com")
        if self.ARTICLES_PER_EMAIL != 20:
            raise ValueError("ARTICLES_PER_EMAIL must be 20")
        if self.MIN_RELEVANCE_SCORE != 70.0:
            raise ValueError("MIN_RELEVANCE_SCORE must be 70.0")
        return self

    def secret_is_set(self, value: SecretStr) -> bool:
        """Return whether a secret value is configured.

        Args:
            value: SecretStr setting.

        Returns:
            True when the secret contains a non-empty value.
        """
        return bool(value.get_secret_value().strip())

    def validate_for_production(self) -> None:
        """Validate settings required for a live production pipeline run.

        Raises:
            ConfigError: If any required production secret or sender setting is
                missing.
        """
        missing: list[str] = []
        required_secrets: dict[str, SecretStr] = {
            "FIRECRAWL_API_KEY": self.FIRECRAWL_API_KEY,
            "ANTHROPIC_API_KEY": self.ANTHROPIC_API_KEY,
            "SENDGRID_API_KEY": self.SENDGRID_API_KEY,
        }

        for name, secret in required_secrets.items():
            if not self.secret_is_set(secret):
                missing.append(name)

        if self.SENDER_EMAIL == "scrapesignal@example.com":
            missing.append("SENDER_EMAIL")

        if missing:
            joined = ", ".join(sorted(missing))
            raise ConfigError(f"Missing production configuration: {joined}")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load settings once per process.

    Returns:
        Cached Settings instance.
    """
    return Settings()


settings: Settings = get_settings()
