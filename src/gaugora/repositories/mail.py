"""Mail queue and SMTP repositories."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaugora.models.mail import MailAttempt, MailQueueItem, SmtpSettings


class MailRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def ensure_smtp_singleton(self) -> SmtpSettings:
        settings = self.session.get(SmtpSettings, 1)
        if settings is None:
            settings = SmtpSettings(id=1)
            self.session.add(settings)
            self.session.flush()
        return settings

    def get_smtp(self) -> SmtpSettings:
        return self.ensure_smtp_singleton()

    def update_smtp(
        self,
        *,
        host: str,
        port: int,
        use_tls: bool,
        username: str,
        password: str,
        from_address: str,
        to_addresses: list[str],
    ) -> SmtpSettings:
        settings = self.ensure_smtp_singleton()
        settings.host = host
        settings.port = port
        settings.use_tls = use_tls
        settings.username = username
        if password:
            settings.password = password
        settings.from_address = from_address
        settings.to_addresses = to_addresses
        self.session.flush()
        return settings

    def enqueue(
        self,
        *,
        channel: str,
        rule_id: int | None,
        subject: str,
        body: str,
        to_addresses: list[str],
    ) -> MailQueueItem:
        item = MailQueueItem(
            channel=channel,
            rule_id=rule_id,
            subject=subject,
            body=body,
            to_addresses=to_addresses,
            status="pending",
            attempts=0,
            # Set only after a failed attempt so the retry job does not race the
            # immediate send.
            next_retry_at=None,
        )
        self.session.add(item)
        self.session.flush()
        return item

    def get_item(self, item_id: int) -> MailQueueItem | None:
        return self.session.get(MailQueueItem, item_id)

    def list_queue(self, *, limit: int = 100) -> list[MailQueueItem]:
        return list(
            self.session.scalars(
                select(MailQueueItem)
                .order_by(MailQueueItem.created_at.desc())
                .limit(limit)
            ).all()
        )

    def list_attempts(self, queue_id: int) -> list[MailAttempt]:
        return list(
            self.session.scalars(
                select(MailAttempt)
                .where(MailAttempt.queue_id == queue_id)
                .order_by(MailAttempt.attempted_at.desc())
            ).all()
        )

    def list_recent_attempts(self, *, limit: int = 50) -> list[MailAttempt]:
        return list(
            self.session.scalars(
                select(MailAttempt)
                .order_by(MailAttempt.attempted_at.desc())
                .limit(limit)
            ).all()
        )

    def items_ready_for_retry(self, *, max_attempts: int) -> list[MailQueueItem]:
        now = datetime.now(timezone.utc)
        return list(
            self.session.scalars(
                select(MailQueueItem).where(
                    MailQueueItem.status.in_(("pending", "failed")),
                    MailQueueItem.attempts < max_attempts,
                    MailQueueItem.next_retry_at.is_not(None),
                    MailQueueItem.next_retry_at <= now,
                )
            ).all()
        )

    def record_attempt(
        self,
        item: MailQueueItem,
        *,
        success: bool,
        error: str | None,
        next_retry_at: datetime | None,
        max_attempts: int,
    ) -> MailAttempt:
        attempt = MailAttempt(
            queue_id=item.id,
            attempted_at=datetime.now(timezone.utc),
            success=success,
            error=error,
        )
        self.session.add(attempt)
        item.attempts += 1
        item.last_error = error
        if success:
            item.status = "sent"
            item.sent_at = datetime.now(timezone.utc)
            item.next_retry_at = None
        else:
            if item.attempts >= max_attempts:
                item.status = "failed"
                item.next_retry_at = None
            else:
                item.status = "pending"
                item.next_retry_at = next_retry_at
        self.session.flush()
        return attempt
