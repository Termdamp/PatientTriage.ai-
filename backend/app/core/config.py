from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    DATABASE_URL: str = "postgresql+psycopg://triage:triage@localhost:5432/patienttriage"
    CORS_ORIGINS: str = "http://localhost:3000"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    APP_VERSION: str = "0.1.0"
    APP_NAME: str = "PatientTriage.ai"
    HF_API_TOKEN: str = "hf_placeholder"
    HF_MODEL_ID: str = "Qwen/Qwen2.5-1.5B-Instruct"

    # Waiting breach thresholds in minutes
    WAITING_BREACH_CRITICAL_MINUTES: int = 15
    WAITING_BREACH_HIGH_MINUTES: int = 30
    WAITING_BREACH_MODERATE_MINUTES: int = 60
    WAITING_BREACH_LOW_MINUTES: int = 120

    # Capacity warning threshold
    CAPACITY_WARNING_THRESHOLD: float = 0.85
    CRITICAL_CAPACITY_WARNING_THRESHOLD: float = 0.90

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

settings = Settings()

# Hosting providers (Render, Railway, Heroku, etc.) commonly hand back a
# "postgresql://" or "postgres://" connection string. SQLAlchemy needs the
# psycopg3 driver to be named explicitly, so normalize it here rather than
# requiring every deployment target to set the URL just right.
if settings.DATABASE_URL.startswith("postgres://"):
    settings.DATABASE_URL = settings.DATABASE_URL.replace(
        "postgres://", "postgresql+psycopg://", 1
    )
elif settings.DATABASE_URL.startswith("postgresql://"):
    settings.DATABASE_URL = settings.DATABASE_URL.replace(
        "postgresql://", "postgresql+psycopg://", 1
    )
