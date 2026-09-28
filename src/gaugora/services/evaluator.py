"""Evaluate alert rules against latest metric samples."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from gaugora.models.alert import AlertRule
from gaugora.repositories.alerts import AlertRepository
from gaugora.repositories.metrics import MetricRepository


@dataclass
class Breach:
    rule: AlertRule
    value: float


class EvaluatorService:
    def __init__(self, session: Session) -> None:
        self.alerts = AlertRepository(session)
        self.metrics = MetricRepository(session)

    def find_breaches(self) -> list[Breach]:
        latest = self.metrics.latest_samples_map()
        breaches: list[Breach] = []
        for rule in self.alerts.list_enabled_rules():
            sample = latest.get(rule.metric_key)
            if sample is None:
                continue
            if rule.operator == ">" and sample.value > rule.threshold:
                breaches.append(Breach(rule=rule, value=sample.value))
        return breaches
