"""Prune old metric samples per definition retention."""

from __future__ import annotations

from sqlalchemy.orm import Session

from gaugora.repositories.metrics import MetricRepository


class RetentionService:
    def __init__(self, session: Session) -> None:
        self.metrics = MetricRepository(session)

    def prune_all(self) -> int:
        total = 0
        for definition in self.metrics.list_definitions():
            total += self.metrics.prune_older_than(
                definition.key, definition.retention_days
            )
        return total
