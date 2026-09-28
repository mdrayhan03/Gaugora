"""Alert rule and cooldown repositories."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaugora.models.alert import AlertCooldown, AlertRule


class AlertRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_rules(self) -> list[AlertRule]:
        return list(
            self.session.scalars(select(AlertRule).order_by(AlertRule.id.desc())).all()
        )

    def list_enabled_rules(self) -> list[AlertRule]:
        return list(
            self.session.scalars(
                select(AlertRule).where(AlertRule.enabled.is_(True)).order_by(AlertRule.id)
            ).all()
        )

    def get_rule(self, rule_id: int) -> AlertRule | None:
        return self.session.get(AlertRule, rule_id)

    def create_rule(
        self,
        *,
        name: str,
        metric_key: str,
        threshold: float,
        channels: list[str],
        cooldown_seconds: int = 300,
        enabled: bool = True,
        operator: str = ">",
    ) -> AlertRule:
        rule = AlertRule(
            name=name,
            metric_key=metric_key,
            operator=operator,
            threshold=threshold,
            channels=channels,
            cooldown_seconds=cooldown_seconds,
            enabled=enabled,
        )
        self.session.add(rule)
        self.session.flush()
        return rule

    def update_rule(
        self,
        rule: AlertRule,
        *,
        name: str,
        metric_key: str,
        threshold: float,
        channels: list[str],
        cooldown_seconds: int,
        enabled: bool,
    ) -> AlertRule:
        rule.name = name
        rule.metric_key = metric_key
        rule.threshold = threshold
        rule.channels = channels
        rule.cooldown_seconds = cooldown_seconds
        rule.enabled = enabled
        self.session.flush()
        return rule

    def delete_rule(self, rule: AlertRule) -> None:
        # Remove cooldown rows first (SQLite may not enforce ON DELETE CASCADE
        # depending on pragma timing).
        for cooldown in self.session.scalars(
            select(AlertCooldown).where(AlertCooldown.rule_id == rule.id)
        ).all():
            self.session.delete(cooldown)
        self.session.delete(rule)
        self.session.flush()

    def get_cooldown(self, rule_id: int, channel: str) -> AlertCooldown | None:
        return self.session.scalar(
            select(AlertCooldown).where(
                AlertCooldown.rule_id == rule_id,
                AlertCooldown.channel == channel,
            )
        )

    def is_in_cooldown(self, rule: AlertRule, channel: str) -> bool:
        cooldown = self.get_cooldown(rule.id, channel)
        if cooldown is None:
            return False
        last = cooldown.last_sent_at
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        elapsed = (datetime.now(timezone.utc) - last).total_seconds()
        return elapsed < rule.cooldown_seconds

    def touch_cooldown(self, rule: AlertRule, channel: str) -> AlertCooldown:
        cooldown = self.get_cooldown(rule.id, channel)
        now = datetime.now(timezone.utc)
        if cooldown is None:
            cooldown = AlertCooldown(
                rule_id=rule.id,
                metric_key=rule.metric_key,
                channel=channel,
                last_sent_at=now,
            )
            self.session.add(cooldown)
        else:
            cooldown.last_sent_at = now
            cooldown.metric_key = rule.metric_key
        self.session.flush()
        return cooldown
