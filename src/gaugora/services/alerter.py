"""Alert handling: cooldown, enqueue, immediate send."""

from __future__ import annotations

from sqlalchemy.orm import Session

from gaugora.config import Settings
from gaugora.repositories.alerts import AlertRepository
from gaugora.repositories.mail import MailRepository
from gaugora.services.diagnostics import format_diagnostics_for_email
from gaugora.services.evaluator import Breach
from gaugora.services.mailer import MailerService


class AlerterService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.alerts = AlertRepository(session)
        self.mail = MailRepository(session)
        self.mailer = MailerService(session, settings)
        self.settings = settings

    def handle_breaches(self, breaches: list[Breach]) -> int:
        sent_or_queued = 0
        smtp = self.mail.get_smtp()
        for breach in breaches:
            channels = list(breach.rule.channels or [])
            if not channels:
                channels = ["email"]
            for channel in channels:
                if channel != "email":
                    # v1: only email is implemented
                    continue
                if self.alerts.is_in_cooldown(breach.rule, channel):
                    continue
                recipients = list(smtp.to_addresses or [])
                project = self.settings.project_name
                subject = f"[Gaugora] {project} — {breach.rule.name}"
                try:
                    diagnostics = format_diagnostics_for_email(breach.rule.metric_key)
                except Exception:  # noqa: BLE001 — never block alerting on diagnostics
                    diagnostics = (
                        "\n(Host/process diagnostics unavailable on this sample.)\n"
                    )
                body = (
                    f"Project: {project}\n"
                    f"Alert: {breach.rule.name}\n"
                    f"Metric: {breach.rule.metric_key}\n"
                    f"Condition: {breach.rule.metric_key} {breach.rule.operator} "
                    f"{breach.rule.threshold}\n"
                    f"Current value: {breach.value:.2f}\n"
                    f"{diagnostics}"
                )
                item = self.mail.enqueue(
                    channel=channel,
                    rule_id=breach.rule.id,
                    subject=subject,
                    body=body,
                    to_addresses=recipients,
                )
                # Cooldown starts at enqueue so a sustained breach does not flood the queue.
                self.alerts.touch_cooldown(breach.rule, channel)
                self.mailer.send_queue_item(item)
                sent_or_queued += 1
        return sent_or_queued
