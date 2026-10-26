"""Database bootstrap: run Alembic migrations and seed defaults."""

from __future__ import annotations

import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

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

    if not alembic_dir.exists():
        cwd_alembic = Path.cwd() / "alembic"
        if cwd_alembic.exists():
            alembic_dir = cwd_alembic
            alembic_ini_path = Path.cwd() / "alembic.ini"
        else:
            logger.error(
                "Alembic directory not found at %s or %s. Skipping auto-migrations.",
                alembic_dir,
                cwd_alembic,
            )
            return

    alembic_cfg = Config(str(alembic_ini_path) if alembic_ini_path.exists() else "")
    alembic_cfg.set_main_option("script_location", str(alembic_dir))

    with extensions.engine.begin() as connection:
        alembic_cfg.attributes["connection"] = connection
        inspector = inspect(connection)
        tables = inspector.get_table_names()

        current_rev = None
        if "alembic_version" in tables:
            current_rev = connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar()

        has_existing_tables = any(
            t in tables
            for t in (
                "metric_definitions",
                "metric_samples",
                "alert_rules",
                "smtp_settings",
            )
        )

        # If legacy database has tables but no revision stamped, stamp baseline first
        if not current_rev and has_existing_tables:
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
