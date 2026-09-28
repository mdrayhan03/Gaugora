"""Mail send and retry helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from gaugora.channels.base import ChannelMessage, ChannelResult
from gaugora.channels.email import EmailChannel
from gaugora.config import Settings
from gaugora.models.mail import MailQueueItem
from gaugora.repositories.mail import MailRepository


def backoff_seconds(attempt_number: int) -> int:
    """Exponential backoff starting at 30s, capped at 30 minutes."""
    return min(30 * (2 ** max(attempt_number - 1, 0)), 1800)


class MailerService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.mail = MailRepository(session)
        self.settings = settings

    def send_queue_item(self, item: MailQueueItem) -> ChannelResult:
        smtp = self.mail.get_smtp()
        if item.channel != "email":
            result = ChannelResult(success=False, error=f"Unsupported channel: {item.channel}")
            self._record(item, result)
            return result

        channel = EmailChannel(smtp)
        message = ChannelMessage(
            subject=item.subject,
            body=item.body,
            to_addresses=list(item.to_addresses or []),
        )
        result = channel.send(message)
        self._record(item, result)
        return result

    def retry_due(self) -> int:
        items = self.mail.items_ready_for_retry(max_attempts=self.settings.mail_max_attempts)
        count = 0
        for item in items:
            # Skip items that just failed and were already attempted in this same flow
            # if status was updated — items_ready_for_retry already filters.
            self.send_queue_item(item)
            count += 1
        return count

    def _record(self, item: MailQueueItem, result: ChannelResult) -> None:
        next_retry: datetime | None = None
        if not result.success:
            delay = backoff_seconds(item.attempts + 1)
            next_retry = datetime.now(timezone.utc) + timedelta(seconds=delay)
        self.mail.record_attempt(
            item,
            success=result.success,
            error=result.error,
            next_retry_at=next_retry,
            max_attempts=self.settings.mail_max_attempts,
        )
