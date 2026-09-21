"""Load settings from the environment or project-root .env; PostgreSQL is required at startup."""

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    database_url: str = ""
    aws_region: str = ""
    s3_bucket_name: str = ""
    storage_backend: Literal["local", "s3"] = "local"

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
