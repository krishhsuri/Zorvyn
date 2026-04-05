"""
Application configuration loaded from environment variables.

Uses pydantic-settings to validate and parse .env values into typed Python
attributes.  Every other module imports `settings` from here — single
source of truth for configuration (DRY).
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Typed, validated application settings."""

    # ── Database ──────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://zorvyn:zorvyn_pass@db:5432/zorvyn_finance"

    # ── JWT ───────────────────────────────────────────────
    SECRET_KEY: str = "change-me-to-a-random-64-char-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # ── Admin Seed ────────────────────────────────────────
    ADMIN_EMAIL: str = "admin@zorvyn.com"
    ADMIN_PASSWORD: str = "admin123"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
