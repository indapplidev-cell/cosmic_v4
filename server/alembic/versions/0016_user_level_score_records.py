"""user level score records

Revision ID: 0016_user_level_score_records
Revises: 0015_ads_live
Create Date: 2026-03-20 12:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0016_user_level_score_records"
down_revision = "0015_ads_live"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """EN: Create server table for per-user best score records on each level.
    RU: Создать серверную таблицу лучших результатов пользователя по очкам на каждом уровне.
    """

    op.create_table(
        "user_level_score_records",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("level_number", sa.Integer(), nullable=False),
        sa.Column("best_score", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("best_elapsed_ms", sa.Integer(), nullable=True),
        sa.Column("best_result", sa.String(length=32), nullable=True),
        sa.Column("best_attempts_used", sa.Integer(), nullable=True),
        sa.Column("best_reward_used", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("last_score", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("last_elapsed_ms", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("last_result", sa.String(length=32), server_default="unknown", nullable=False),
        sa.Column("runs_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("level_number >= 1", name="ck_user_level_score_records_level_number"),
        sa.CheckConstraint("best_score >= 0", name="ck_user_level_score_records_best_score"),
        sa.CheckConstraint("last_score >= 0", name="ck_user_level_score_records_last_score"),
        sa.CheckConstraint("runs_count >= 0", name="ck_user_level_score_records_runs_count"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_user_level_score_records_user_id_level_number",
        "user_level_score_records",
        ["user_id", "level_number"],
        unique=True,
    )
    op.execute(
        sa.text(
            """
            CREATE INDEX ix_user_level_score_records_level_score_elapsed
            ON user_level_score_records (level_number, best_score DESC, best_elapsed_ms ASC)
            """
        )
    )
    op.create_index(
        "ix_user_level_score_records_user_id",
        "user_level_score_records",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """EN: Drop per-level score records table and its indexes.
    RU: Удалить таблицу рекордов по уровням и её индексы.
    """

    op.drop_index("ix_user_level_score_records_user_id", table_name="user_level_score_records")
    op.drop_index("ix_user_level_score_records_level_score_elapsed", table_name="user_level_score_records")
    op.drop_index("ix_user_level_score_records_user_id_level_number", table_name="user_level_score_records")
    op.drop_table("user_level_score_records")
