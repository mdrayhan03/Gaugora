"""Add consecutive spikes guard and retention logs table

Revision ID: 0002_spikes_and_retention
Revises: 0001_baseline
Create Date: 2026-10-26 17:54:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0002_spikes_and_retention"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add consecutive spike guard columns to alert_rules
    op.add_column(
        "alert_rules",
        sa.Column("consecutive_breaches", sa.Integer(), nullable=False, server_default="3"),
    )
    op.add_column(
        "alert_rules",
        sa.Column("current_breach_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "alert_rules",
        sa.Column("is_firing", sa.Boolean(), nullable=False, server_default="0"),
    )
    op.add_column(
        "alert_rules",
        sa.Column("last_breached_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 2. Create retention_logs audit table
    op.create_table(
        "retention_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("total_deleted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="success"),
        sa.Column("error", sa.Text(), nullable=True),
    )
    op.create_index("ix_retention_logs_started_at", "retention_logs", ["started_at"])


def downgrade() -> None:
    op.drop_index("ix_retention_logs_started_at", table_name="retention_logs")
    op.drop_table("retention_logs")

    with op.batch_alter_table("alert_rules") as batch_op:
        batch_op.drop_column("last_breached_at")
        batch_op.drop_column("is_firing")
        batch_op.drop_column("current_breach_count")
        batch_op.drop_column("consecutive_breaches")
