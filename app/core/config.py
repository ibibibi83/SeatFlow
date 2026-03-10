"""
Application configuration.

All settings are loaded from environment variables or the .env file.
Defaults are suitable for local development only – change SECRET_KEY in production.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # ── General ───────────────────────────────────────────────────────────────
    APP_NAME: str = "SeatFlow API"
    APP_VERSION: str = "1.0.0"

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./seatflow.db"

    # ── JWT auth ──────────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production-must-be-at-least-32-characters"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── Seat management ───────────────────────────────────────────────────────
    TOTAL_SEATS: int = 230          # physical seats in the venue
    RESERVABLE_SEATS: int = 50      # maximum seats that can be reserved at once
    RESERVATION_DURATION_MINUTES: int = 15  # how long a reservation stays active


settings = Settings()