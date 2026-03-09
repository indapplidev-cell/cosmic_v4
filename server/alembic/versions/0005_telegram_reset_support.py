"""telegram reset support

Revision ID: 0005_telegram_reset_support
Revises: 0004_pwd_reset_tokens
Create Date: 2026-03-09 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0005_telegram_reset_support"
down_revision = "0004_pwd_reset_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """EN: Create telegram link/account/outbox tables for bot-based reset flow.
    RU: Создать таблицы telegram link/account/outbox для reset-потока через бота.
    """

    op.create_table(
        "telegram_accounts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", name="uq_telegram_accounts_user_id"),
        sa.UniqueConstraint("telegram_user_id", name="uq_telegram_accounts_tg_user_id"),
    )
    op.create_index("ix_telegram_accounts_user_id", "telegram_accounts", ["user_id"])
    op.create_index("ix_telegram_accounts_telegram_user_id", "telegram_accounts", ["telegram_user_id"])

    op.create_table(
        "telegram_link_tokens",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("code_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_telegram_link_tokens_user_id", "telegram_link_tokens", ["user_id"])
    op.create_index("ix_telegram_link_tokens_code_hash", "telegram_link_tokens", ["code_hash"])
    op.create_index("ix_telegram_link_tokens_expires_at", "telegram_link_tokens", ["expires_at"])
    op.create_index("ix_telegram_link_tokens_used_at", "telegram_link_tokens", ["used_at"])

    op.create_table(
        "telegram_outbox",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_telegram_outbox_telegram_user_id", "telegram_outbox", ["telegram_user_id"])
    op.create_index("ix_telegram_outbox_status", "telegram_outbox", ["status"])
    op.create_index("ix_telegram_outbox_next_attempt_at", "telegram_outbox", ["next_attempt_at"])


def downgrade() -> None:
    """EN: Drop telegram support tables and indexes.
    RU: Удалить таблицы и индексы поддержки Telegram.
    """

    op.drop_index("ix_telegram_outbox_next_attempt_at", table_name="telegram_outbox")
    op.drop_index("ix_telegram_outbox_status", table_name="telegram_outbox")
    op.drop_index("ix_telegram_outbox_telegram_user_id", table_name="telegram_outbox")
    op.drop_table("telegram_outbox")

    op.drop_index("ix_telegram_link_tokens_used_at", table_name="telegram_link_tokens")
    op.drop_index("ix_telegram_link_tokens_expires_at", table_name="telegram_link_tokens")
    op.drop_index("ix_telegram_link_tokens_code_hash", table_name="telegram_link_tokens")
    op.drop_index("ix_telegram_link_tokens_user_id", table_name="telegram_link_tokens")
    op.drop_table("telegram_link_tokens")

    op.drop_index("ix_telegram_accounts_telegram_user_id", table_name="telegram_accounts")
    op.drop_index("ix_telegram_accounts_user_id", table_name="telegram_accounts")
    op.drop_table("telegram_accounts")

