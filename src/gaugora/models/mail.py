"""Mail queue, attempts, and SMTP settings models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from gaugora.extensions import Base


class SmtpSettings(Base):
    __tablename__ = "smtp_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    host: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    port: Mapped[int] = mapped_column(Integer, nullable=False, default=587)
    use_tls: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    username: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    password: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    from_address: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    to_addresses: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class MailQueueItem(Base):
    __tablename__ = "mail_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel: Mapped[str] = mapped_column(String(32), nullable=False, default="email")
    rule_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("alert_rules.id", ondelete="SET NULL"), nullable=True
    )
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    to_addresses: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending", index=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_retry_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MailAttempt(Base):
    __tablename__ = "mail_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    queue_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("mail_queue.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
