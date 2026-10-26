"""APScheduler job registration."""

from __future__ import annotations

from datetime import datetime, timezone
import logging

from flask import Flask

from gaugora.config import Settings
from gaugora.extensions import scheduler, session_scope
from gaugora.repositories.retention import RetentionRepository
from gaugora.services.alerter import AlerterService
from gaugora.services.collector import CollectorService
from gaugora.services.evaluator import EvaluatorService
from gaugora.services.mailer import MailerService
from gaugora.services.retention import RetentionService

logger = logging.getLogger(__name__)


def _sample_job(settings: Settings) -> None:
    try:
        with session_scope() as session:
            CollectorService(session).collect_once()
            breaches = EvaluatorService(session).find_breaches()
            if breaches:
                AlerterService(session, settings).handle_breaches(breaches)
    except Exception:
        logger.exception("Sample job failed")


def _mail_retry_job(settings: Settings) -> None:
    try:
        with session_scope() as session:
            MailerService(session, settings).retry_due()
    except Exception:
        logger.exception("Mail retry job failed")


def _retention_job() -> None:
    started_at = datetime.now(timezone.utc)
    try:
        with session_scope() as session:
            log = RetentionService(session).prune_all()
            if log.total_deleted:
                logger.info(
                    "Retention pruned %s samples in %.2fms",
                    log.total_deleted,
                    log.duration_ms,
                )
    except Exception as e:
        logger.exception("Retention job failed")
        try:
            with session_scope() as session:
                completed_at = datetime.now(timezone.utc)
                duration_ms = max(
                    0.0, (completed_at - started_at).total_seconds() * 1000.0
                )
                RetentionRepository(session).record_run(
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_ms=round(duration_ms, 2),
                    total_deleted=0,
                    details={},
                    status="failed",
                    error=str(e),
                )
        except Exception:
            logger.exception("Failed to record retention error log")


def start_scheduler(app: Flask, settings: Settings) -> None:
    if scheduler.running:
        return

    scheduler.add_job(
        _sample_job,
        "interval",
        seconds=settings.sample_interval_seconds,
        args=[settings],
        id="sample",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.add_job(
        _mail_retry_job,
        "interval",
        seconds=settings.mail_retry_interval_seconds,
        args=[settings],
        id="mail_retry",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.add_job(
        _retention_job,
        "interval",
        hours=1,
        id="retention",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()
    app.logger.info(
        "Scheduler started (sample=%ss, mail_retry=%ss)",
        settings.sample_interval_seconds,
        settings.mail_retry_interval_seconds,
    )


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
