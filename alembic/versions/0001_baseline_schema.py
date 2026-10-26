"""Baseline schema

Revision ID: 0001_baseline
Revises: 
Create Date: 2026-10-26 17:53:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = sa.inspect(bind).get_table_names()

    if "metric_definitions" not in tables:
        op.create_table(
            "metric_definitions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("key", sa.String(length=64), nullable=False, unique=True),
            sa.Column("name", sa.String(length=128), nullable=False),
            sa.Column("retention_days", sa.Integer(), nullable=False, server_default="7"),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_metric_definitions_key", "metric_definitions", ["key"])

    if "metric_samples" not in tables:
        op.create_table(
            "metric_samples",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("metric_key", sa.String(length=64), nullable=False),
            sa.Column("value", sa.Float(), nullable=False),
            sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_metric_samples_metric_key", "metric_samples", ["metric_key"])
        op.create_index("ix_metric_samples_collected_at", "metric_samples", ["collected_at"])

    if "alert_rules" not in tables:
        op.create_table(
            "alert_rules",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=128), nullable=False),
            sa.Column("metric_key", sa.String(length=64), nullable=False),
            sa.Column("operator", sa.String(length=8), nullable=False, server_default=">"),
            sa.Column("threshold", sa.Float(), nullable=False),
            sa.Column("channels", sa.JSON(), nullable=False),
            sa.Column("cooldown_seconds", sa.Integer(), nullable=False, server_default="300"),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_alert_rules_metric_key", "alert_rules", ["metric_key"])

    if "alert_cooldowns" not in tables:
        op.create_table(
            "alert_cooldowns",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("rule_id", sa.Integer(), sa.ForeignKey("alert_rules.id", ondelete="CASCADE"), nullable=False),
            sa.Column("metric_key", sa.String(length=64), nullable=False),
            sa.Column("channel", sa.String(length=32), nullable=False),
            sa.Column("last_sent_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("rule_id", "channel", name="uq_cooldown_rule_channel"),
        )

    if "smtp_settings" not in tables:
        op.create_table(
            "smtp_settings",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("host", sa.String(length=128), nullable=False, server_default=""),
            sa.Column("port", sa.Integer(), nullable=False, server_default="587"),
            sa.Column("use_tls", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("username", sa.String(length=128), nullable=False, server_default=""),
            sa.Column("password", sa.String(length=128), nullable=False, server_default=""),
            sa.Column("from_address", sa.String(length=128), nullable=False, server_default=""),
            sa.Column("to_addresses", sa.JSON(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )

    if "mail_queue" not in tables:
        op.create_table(
            "mail_queue",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("channel", sa.String(length=32), nullable=False, server_default="email"),
            sa.Column("rule_id", sa.Integer(), nullable=True),
            sa.Column("subject", sa.String(length=256), nullable=False),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("to_addresses", sa.JSON(), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
            sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("last_error", sa.Text(), nullable=True),
            sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )

    if "mail_attempts" not in tables:
        op.create_table(
            "mail_attempts",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("queue_id", sa.Integer(), sa.ForeignKey("mail_queue.id", ondelete="CASCADE"), nullable=False),
            sa.Column("attempted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("success", sa.Boolean(), nullable=False),
            sa.Column("error", sa.Text(), nullable=True),
        )


def downgrade() -> None:
    op.drop_table("mail_attempts")
    op.drop_table("mail_queue")
    op.drop_table("smtp_settings")
    op.drop_table("alert_cooldowns")
    op.drop_table("alert_rules")
    op.drop_table("metric_samples")
    op.drop_table("metric_definitions")
