"""Metric repositories."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from gaugora.models.metric import MetricDefinition, MetricSample


class MetricRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_definitions(self) -> list[MetricDefinition]:
        return list(
            self.session.scalars(
                select(MetricDefinition).order_by(MetricDefinition.key)
            ).all()
        )

    def list_enabled_definitions(self) -> list[MetricDefinition]:
        return list(
            self.session.scalars(
                select(MetricDefinition)
                .where(MetricDefinition.enabled.is_(True))
                .order_by(MetricDefinition.key)
            ).all()
        )

    def get_definition(self, metric_id: int) -> MetricDefinition | None:
        return self.session.get(MetricDefinition, metric_id)

    def get_definition_by_key(self, key: str) -> MetricDefinition | None:
        return self.session.scalar(
            select(MetricDefinition).where(MetricDefinition.key == key)
        )

    def update_retention(self, metric_id: int, retention_days: int) -> MetricDefinition | None:
        definition = self.get_definition(metric_id)
        if definition is None:
            return None
        definition.retention_days = max(1, retention_days)
        self.session.flush()
        return definition

    def add_sample(self, metric_key: str, value: float, collected_at: datetime) -> MetricSample:
        sample = MetricSample(
            metric_key=metric_key, value=value, collected_at=collected_at
        )
        self.session.add(sample)
        self.session.flush()
        return sample

    def latest_sample(self, metric_key: str) -> MetricSample | None:
        return self.session.scalar(
            select(MetricSample)
            .where(MetricSample.metric_key == metric_key)
            .order_by(MetricSample.collected_at.desc())
            .limit(1)
        )

    def latest_samples_map(self) -> dict[str, MetricSample]:
        result: dict[str, MetricSample] = {}
        for definition in self.list_definitions():
            sample = self.latest_sample(definition.key)
            if sample is not None:
                result[definition.key] = sample
        return result

    def history(
        self, metric_key: str, *, since: datetime | None = None, limit: int = 500
    ) -> list[MetricSample]:
        stmt = select(MetricSample).where(MetricSample.metric_key == metric_key)
        if since is not None:
            stmt = stmt.where(MetricSample.collected_at >= since)
        stmt = stmt.order_by(MetricSample.collected_at.asc()).limit(limit)
        return list(self.session.scalars(stmt).all())

    def prune_older_than(self, metric_key: str, retention_days: int) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        result = self.session.execute(
            delete(MetricSample).where(
                MetricSample.metric_key == metric_key,
                MetricSample.collected_at < cutoff,
            )
        )
        return result.rowcount or 0

    def ensure_defaults(self) -> None:
        defaults = [
            ("cpu_percent", "CPU usage"),
            ("memory_percent", "Memory usage"),
            ("disk_percent", "Disk usage (/)"),
        ]
        for key, name in defaults:
            if self.get_definition_by_key(key) is None:
                self.session.add(
                    MetricDefinition(
                        key=key,
                        name=name,
                        retention_days=7,
                        enabled=True,
                    )
                )
        self.session.flush()
