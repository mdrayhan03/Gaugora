"""Database bootstrap: create tables and seed defaults."""

from __future__ import annotations

from gaugora import extensions
from gaugora.extensions import Base, session_scope
from gaugora.models import (  # noqa: F401 — register models on Base.metadata
    AlertCooldown,
    AlertRule,
    MailAttempt,
    MailQueueItem,
    MetricDefinition,
    MetricSample,
    SmtpSettings,
)
from gaugora.repositories.mail import MailRepository
from gaugora.repositories.metrics import MetricRepository


def init_database() -> None:
    if extensions.engine is None:
        raise RuntimeError("Engine not initialized")
    Base.metadata.create_all(bind=extensions.engine)
    with session_scope() as session:
        MetricRepository(session).ensure_defaults()
        MailRepository(session).ensure_smtp_singleton()
