"""Database bootstrap: run Alembic migrations and seed defaults."""

from __future__ import annotations

import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from gaugora import extensions
from gaugora.config import Settings, load_settings
from gaugora.extensions import session_scope
from gaugora.repositories.mail import MailRepository
from gaugora.repositories.metrics import MetricRepository

logger = logging.getLogger(__name__)


def run_migrations() -> None:
    """Run Alembic migrations up to head automatically."""
    if extensions.engine is None:
        raise RuntimeError("Engine not initialized")

    project_root = Path(__file__).resolve().parent.parent.parent
    alembic_ini_path = project_root / "alembic.ini"
    alembic_dir = project_root / "alembic"

    alembic_cfg = Config(str(alembic_ini_path))
    alembic_cfg.set_main_option("script_location", str(alembic_dir))

    with extensions.engine.begin() as connection:
        alembic_cfg.attributes["connection"] = connection
        inspector = inspect(connection)
        tables = inspector.get_table_names()
        # If legacy database exists without alembic_version, stamp baseline first
        if "alembic_version" not in tables and "alert_rules" in tables:
            logger.info("Stamping existing database as 0001_baseline")
            command.stamp(alembic_cfg, "0001_baseline")

        command.upgrade(alembic_cfg, "head")


def init_database(settings: Settings | None = None) -> None:
    if extensions.engine is None:
        raise RuntimeError("Engine not initialized")

    if settings is None:
        settings = load_settings()

    if settings.auto_migrate:
        logger.info("Auto-migrating database schema to head")
        run_migrations()
    else:
        logger.info("Auto-migration disabled (GAUGORA_AUTO_MIGRATE=false)")

    with session_scope() as session:
        MetricRepository(session).ensure_defaults()
        MailRepository(session).ensure_smtp_singleton()
