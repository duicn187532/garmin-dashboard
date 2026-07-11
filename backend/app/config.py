from dataclasses import dataclass
from functools import lru_cache
import os
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")


def _truthy(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _backend_path(value: str | None, default: str) -> str:
    path = Path(value or default)
    if not path.is_absolute():
        path = BACKEND_DIR / path
    return str(path)


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Garmin Insight")
    environment: str = os.getenv("ENVIRONMENT", "development")
    database_backend: str = os.getenv("DATABASE_BACKEND", "sqlite").strip().lower()
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./garmin_insight.db")
    mongodb_uri: str | None = os.getenv("MONGODB_URI")
    mongodb_database: str = os.getenv("MONGODB_DATABASE", "garmin_insight")
    cors_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8081",
        ).split(",")
        if origin.strip()
    )

    demo_mode: bool = _truthy(os.getenv("DEMO_MODE"), True)
    app_access_token: str | None = os.getenv("APP_ACCESS_TOKEN")
    sync_token: str | None = os.getenv("SYNC_TOKEN")

    garmin_email: str | None = os.getenv("GARMIN_EMAIL")
    garmin_password: str | None = os.getenv("GARMIN_PASSWORD")
    garmin_mfa_code: str | None = os.getenv("GARMIN_MFA_CODE")
    garmin_tokenstore: str = _backend_path(os.getenv("GARMIN_TOKENSTORE"), ".garmin_tokens")

    ai_provider: str = os.getenv("AI_PROVIDER", "gemini").strip().lower()
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", os.getenv("AI_MODEL", "gpt-4.1-mini"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
