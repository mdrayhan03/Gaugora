"""Retention log repository."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaugora.models.retention import RetentionLog


class RetentionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def record_run(
        self,
        *,
        started_at: datetime,
        completed_at: datetime,
        duration_ms: float,
        total_deleted: int,
        details: dict,
        status: str = "success",
        error: str | None = None,
    ) -> RetentionLog:
        log = RetentionLog(
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
            total_deleted=total_deleted,
            details=details,
            status=status,
            error=error,
        )
        self.session.add(log)
        self.session.flush()
        return log

    def latest_log(self) -> RetentionLog | None:
        return self.session.scalar(
            select(RetentionLog).order_by(RetentionLog.started_at.desc()).limit(1)
        )

    def list_recent(self, *, limit: int = 20) -> list[RetentionLog]:
        return list(
            self.session.scalars(
                select(RetentionLog).order_by(RetentionLog.started_at.desc()).limit(limit)
            ).all()
        )
