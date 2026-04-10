"""payout miniapp verification sessions

Revision ID: 0018_payout_miniapp_sessions
Revises: 0017_profile_user_null_cleanup
Create Date: 2026-03-27 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0018_payout_miniapp_sessions"
down_revision = "0017_profile_user_null_cleanup"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """EN: Create payout_miniapp_sessions table for Telegram Mini App identity verification.
    RU: Создать таблицу payout_miniapp_sessions для Telegram Mini App identity verification.
    """

    op.create_table(
        "payout_miniapp_sessions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_token_hash", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="issued"),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=True),
        sa.Column("telegram_username", sa.Text(), nullable=True),
        sa.Column("init_data_hash", sa.Text(), nullable=True),
        sa.Column("tg_auth_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fail_reason", sa.Text(), nullable=True),
        sa.UniqueConstraint("session_token_hash", name="uq_payout_miniapp_sessions_token_hash"),
    )
    op.create_index("ix_payout_miniapp_sessions_user_id", "payout_miniapp_sessions", ["user_id"])
    op.create_index("ix_payout_miniapp_sessions_status", "payout_miniapp_sessions", ["status"])
    op.create_index("ix_payout_miniapp_sessions_telegram_user_id", "payout_miniapp_sessions", ["telegram_user_id"])
    op.create_index("ix_payout_miniapp_sessions_expires_at", "payout_miniapp_sessions", ["expires_at"])


def downgrade() -> None:
    """EN: Drop payout_miniapp_sessions table and its indexes.
    RU: Удалить таблицу payout_miniapp_sessions и её индексы.
    """

    op.drop_index("ix_payout_miniapp_sessions_expires_at", table_name="payout_miniapp_sessions")
    op.drop_index("ix_payout_miniapp_sessions_telegram_user_id", table_name="payout_miniapp_sessions")
    op.drop_index("ix_payout_miniapp_sessions_status", table_name="payout_miniapp_sessions")
    op.drop_index("ix_payout_miniapp_sessions_user_id", table_name="payout_miniapp_sessions")
    op.drop_table("payout_miniapp_sessions")
