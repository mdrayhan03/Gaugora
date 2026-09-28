"""Application settings loaded from environment."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    project_name: str
    secret_key: str
    database_url: str
    sample_interval_seconds: int
    mail_retry_interval_seconds: int
    mail_max_attempts: int
    host: str
    port: int


def _ensure_sqlite_parent(database_url: str) -> None:
    if not database_url.startswith("sqlite:///"):
        return
    raw = database_url.removeprefix("sqlite:///")
    # Absolute paths use sqlite:////path (four slashes → three after scheme strip starts with /)
    path = Path(raw)
    if not path.is_absolute():
        path = Path.cwd() / path
    path.parent.mkdir(parents=True, exist_ok=True)


def load_settings() -> Settings:
    database_url = os.getenv("GAUGORA_DATABASE_URL", "sqlite:///./data/gaugora.db")
    _ensure_sqlite_parent(database_url)
    return Settings(
        project_name=os.getenv("GAUGORA_PROJECT_NAME", "Gaugora").strip() or "Gaugora",
        secret_key=os.getenv("GAUGORA_SECRET_KEY", "dev-secret-change-me"),
        database_url=database_url,
        sample_interval_seconds=int(os.getenv("GAUGORA_SAMPLE_INTERVAL_SECONDS", "60")),
        mail_retry_interval_seconds=int(
            os.getenv("GAUGORA_MAIL_RETRY_INTERVAL_SECONDS", "30")
        ),
        mail_max_attempts=int(os.getenv("GAUGORA_MAIL_MAX_ATTEMPTS", "5")),
        host=os.getenv("GAUGORA_HOST", "0.0.0.0"),
        port=int(os.getenv("GAUGORA_PORT", "8080")),
    )
