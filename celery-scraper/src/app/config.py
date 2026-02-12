"""
Configuration via Pydantic Settings.

All values are loaded from environment variables (or .env file).
This is the single source of truth for all configuration across
both the Celery workers and the FastAPI server.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Redis / Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # Hacker News API
    hn_api_base_url: str = "https://hacker-news.firebaseio.com/v0"

    # Beat schedule
    beat_pipeline_interval_seconds: int = 300  # 5 minutes

    # Storage
    storage_dir: str = "./data"


settings = Settings()
