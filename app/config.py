"""Environment configuration and validation.

All configuration is read from environment variables (see `.env.example`
for the full list). Nothing here silently falls back to a placeholder
secret in production: `Settings.validate_for_production()` raises if a
required production-only value is missing, so the app fails fast at
startup instead of running with a leaked "change-me" default.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Core ---------------------------------------------------------------------
    APP_ENV: Literal["development", "staging", "production"] = "development"
    APP_SECRET_KEY: str = "insecure-dev-secret-change-me"
    APP_TIMEZONE: str = "Asia/Tashkent"
    LOG_LEVEL: str = "INFO"

    # --- Telegram -------------------------------------------------------------------
    BOT_TOKEN: str = ""
    BOT_USERNAME: str = "YourMovieBot"
    BOT_WEBHOOK_URL: str = ""
    BOT_WEBHOOK_SECRET: str = "change-me"
    BOOTSTRAP_SUPERADMIN_IDS: str = ""

    # --- Database ---------------------------------------------------------------
    DATABASE_URL: str = "postgresql+asyncpg://movie_bot:change-me@localhost:5432/movie_bot"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://movie_bot:change-me@localhost:5432/movie_bot"

    # --- Redis --------------------------------------------------------------------
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- Web ------------------------------------------------------------------------
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    PUBLIC_BASE_URL: str = "http://localhost:8000"

    ADMIN_SESSION_COOKIE_NAME: str = "movie_bot_admin_session"
    ADMIN_SESSION_TTL_SECONDS: int = 43200

    DEFAULT_MANDATORY_CHANNELS: str = ""

    # --- Payments ---------------------------------------------------------------
    PAYMENTS_STARS_ENABLED: bool = False

    PAYMENTS_STRIPE_ENABLED: bool = False
    STRIPE_MODE: Literal["sandbox", "live"] = "sandbox"
    STRIPE_API_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_DEFAULT_CURRENCY: str = "usd"

    PAYMENTS_CLICK_ENABLED: bool = False
    CLICK_MODE: Literal["sandbox", "live"] = "sandbox"
    CLICK_MERCHANT_ID: str = ""
    CLICK_SERVICE_ID: str = ""
    CLICK_MERCHANT_USER_ID: str = ""
    CLICK_SECRET_KEY: str = ""
    CLICK_DEFAULT_CURRENCY: str = "UZS"

    STOREFRONT_ENABLED: bool = False

    BROADCAST_RATE_LIMIT_PER_SECOND: int = 20

    BACKUP_DIR: str = "/var/backups/movie_bot"
    BACKUP_RETENTION_DAYS: int = 14

    @field_validator("BOOTSTRAP_SUPERADMIN_IDS")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()

    @property
    def bootstrap_superadmin_ids(self) -> list[int]:
        return [int(x) for x in self.BOOTSTRAP_SUPERADMIN_IDS.split(",") if x.strip()]

    @property
    def default_mandatory_channels(self) -> list[str]:
        return [x.strip() for x in self.DEFAULT_MANDATORY_CHANNELS.split(",") if x.strip()]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    def validate_for_production(self) -> None:
        """Fail fast instead of silently running with insecure defaults."""
        if not self.is_production:
            return
        problems: list[str] = []
        if not self.BOT_TOKEN:
            problems.append("BOT_TOKEN is required")
        if self.APP_SECRET_KEY in ("", "insecure-dev-secret-change-me", "change-me"):
            problems.append("APP_SECRET_KEY must be set to a real random secret")
        if self.BOT_WEBHOOK_SECRET in ("", "change-me"):
            problems.append("BOT_WEBHOOK_SECRET must be set to a real random secret")
        if self.PAYMENTS_STRIPE_ENABLED and self.STRIPE_MODE == "live":
            if not (self.STRIPE_API_KEY and self.STRIPE_WEBHOOK_SECRET):
                problems.append(
                    "Stripe live mode requires STRIPE_API_KEY and STRIPE_WEBHOOK_SECRET"
                )
        if self.PAYMENTS_CLICK_ENABLED and self.CLICK_MODE == "live":
            if not (self.CLICK_MERCHANT_ID and self.CLICK_SECRET_KEY):
                problems.append("Click live mode requires CLICK_MERCHANT_ID and CLICK_SECRET_KEY")
        if problems:
            raise RuntimeError("Invalid production configuration:\n- " + "\n- ".join(problems))


@lru_cache
def get_settings() -> Settings:
    return Settings()
