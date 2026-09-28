"""Alert rule and cooldown models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from gaugora.extensions import Base


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    metric_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    operator: Mapped[str] = mapped_column(String(8), nullable=False, default=">")
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    channels: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    cooldown_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=300)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class AlertCooldown(Base):
    __tablename__ = "alert_cooldowns"
    __table_args__ = (
        UniqueConstraint("rule_id", "channel", name="uq_cooldown_rule_channel"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("alert_rules.id", ondelete="CASCADE"), nullable=False
    )
    metric_key: Mapped[str] = mapped_column(String(64), nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    last_sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
