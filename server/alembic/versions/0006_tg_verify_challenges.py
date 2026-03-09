"""telegram verify challenges

Revision ID: 0006_tg_verify_challenges
Revises: 0005_telegram_reset_support
Create Date: 2026-03-09 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0006_tg_verify_challenges"
down_revision = "0005_telegram_reset_support"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """EN: Create telegram_verify_challenges table for bot-based verification flow.
    RU: Создать таблицу telegram_verify_challenges для потока верификации через бота.
    """

    op.create_table(
        "telegram_verify_challenges",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("request_id", sa.Text(), nullable=False),
        sa.Column("code_hash", sa.Text(), nullable=True),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("request_id", name="uq_tg_verify_challenges_request_id"),
    )
    op.create_index("ix_tg_verify_challenges_user_id", "telegram_verify_challenges", ["user_id"])
    op.create_index("ix_tg_verify_challenges_code_hash", "telegram_verify_challenges", ["code_hash"])
    op.create_index("ix_tg_verify_challenges_expires_at", "telegram_verify_challenges", ["expires_at"])
    op.create_index("ix_tg_verify_challenges_telegram_user_id", "telegram_verify_challenges", ["telegram_user_id"])
    op.create_index("ix_tg_verify_challenges_used_at", "telegram_verify_challenges", ["used_at"])


def downgrade() -> None:
    """EN: Drop telegram_verify_challenges table and related indexes.
    RU: Удалить таблицу telegram_verify_challenges и связанные индексы.
    """

    op.drop_index("ix_tg_verify_challenges_code_hash", table_name="telegram_verify_challenges")
    op.drop_index("ix_tg_verify_challenges_used_at", table_name="telegram_verify_challenges")
    op.drop_index("ix_tg_verify_challenges_telegram_user_id", table_name="telegram_verify_challenges")
    op.drop_index("ix_tg_verify_challenges_expires_at", table_name="telegram_verify_challenges")
    op.drop_index("ix_tg_verify_challenges_user_id", table_name="telegram_verify_challenges")
    op.drop_table("telegram_verify_challenges")
