"""Collect host metrics via psutil."""

from __future__ import annotations

from datetime import datetime, timezone

import psutil
from sqlalchemy.orm import Session

from gaugora.repositories.metrics import MetricRepository


class CollectorService:
    def __init__(self, session: Session) -> None:
        self.metrics = MetricRepository(session)

    def collect_once(self) -> dict[str, float]:
        now = datetime.now(timezone.utc)
        readings: dict[str, float] = {}
        for definition in self.metrics.list_enabled_definitions():
            value = self._read(definition.key)
            if value is None:
                continue
            readings[definition.key] = value
            self.metrics.add_sample(definition.key, value, now)
        return readings

    def _read(self, metric_key: str) -> float | None:
        if metric_key == "cpu_percent":
            return float(psutil.cpu_percent(interval=0.1))
        if metric_key == "memory_percent":
            return float(psutil.virtual_memory().percent)
        if metric_key == "disk_percent":
            return float(psutil.disk_usage("/").percent)
        return None
