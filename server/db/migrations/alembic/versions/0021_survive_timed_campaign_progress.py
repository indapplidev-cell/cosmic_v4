"""survive timed campaign progress

Revision ID: 0021_survive_timed_progress
Revises: 0020_miniapp_session_purpose
Create Date: 2026-04-02 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0021_survive_timed_progress"
down_revision = "0020_miniapp_session_purpose"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "survive_timed_user_campaign_progress",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("last_completed_level_number", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_level_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("campaign_completed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("last_completed_level_number >= 0", name="ck_survive_timed_campaign_last_completed_nonneg"),
        sa.CheckConstraint("current_level_number >= 1", name="ck_survive_timed_campaign_current_level_min"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_survive_timed_campaign_progress_user_id"),
    )

    op.create_table(
        "survive_timed_user_level_results",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("level_number", sa.Integer(), nullable=False),
        sa.Column("best_survival_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_survival_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("attempts_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_result", sa.String(length=32), nullable=False, server_default="unknown"),
        sa.Column("first_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("level_number >= 1", name="ck_survive_timed_results_level_min"),
        sa.CheckConstraint("best_survival_ms >= 0", name="ck_survive_timed_results_best_nonneg"),
        sa.CheckConstraint("last_survival_ms >= 0", name="ck_survive_timed_results_last_nonneg"),
        sa.CheckConstraint("attempts_count >= 0", name="ck_survive_timed_results_attempts_nonneg"),
        sa.CheckConstraint("completed_count >= 0", name="ck_survive_timed_results_completed_nonneg"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_survive_timed_results_user_level",
        "survive_timed_user_level_results",
        ["user_id", "level_number"],
        unique=True,
    )
    op.create_index(
        "ix_survive_timed_results_user_id",
        "survive_timed_user_level_results",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_survive_timed_results_user_id", table_name="survive_timed_user_level_results")
    op.drop_index("ix_survive_timed_results_user_level", table_name="survive_timed_user_level_results")
    op.drop_table("survive_timed_user_level_results")
    op.drop_table("survive_timed_user_campaign_progress")
