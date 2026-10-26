from datetime import datetime, timezone

from sqlalchemy.orm import Session

from gaugora.models.retention import RetentionLog
from gaugora.repositories.metrics import MetricRepository
from gaugora.repositories.retention import RetentionRepository


class RetentionService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.metrics = MetricRepository(session)
        self.retention_repo = RetentionRepository(session)

    def prune_all(self) -> RetentionLog:
        started_at = datetime.now(timezone.utc)
        details: dict[str, int] = {}
        total = 0
        for definition in self.metrics.list_definitions():
            count = self.metrics.prune_older_than(
                definition.key, definition.retention_days
            )
            details[definition.key] = count
            total += count

        completed_at = datetime.now(timezone.utc)
        duration_ms = max(0.0, (completed_at - started_at).total_seconds() * 1000.0)

        log = self.retention_repo.record_run(
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=round(duration_ms, 2),
            total_deleted=total,
            details=details,
            status="success",
        )
        return log
