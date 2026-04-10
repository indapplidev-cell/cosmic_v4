"""telegram link token context

Revision ID: 0007_tg_link_token_context
Revises: 0006_tg_verify_challenges
Create Date: 2026-03-09 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0007_tg_link_token_context"
down_revision = "0006_tg_verify_challenges"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """EN: Add telegram_user_id/attempts context fields to telegram_link_tokens.
    RU: Добавить контекстные поля telegram_user_id/attempts в таблицу telegram_link_tokens.
    """

    op.add_column("telegram_link_tokens", sa.Column("telegram_user_id", sa.BigInteger(), nullable=True))
    op.add_column(
        "telegram_link_tokens",
        sa.Column("attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.create_index(
        "ix_telegram_link_tokens_telegram_user_id",
        "telegram_link_tokens",
        ["telegram_user_id"],
    )


def downgrade() -> None:
    """EN: Remove telegram_user_id/attempts context fields from telegram_link_tokens.
    RU: Удалить контекстные поля telegram_user_id/attempts из таблицы telegram_link_tokens.
    """

    op.drop_index("ix_telegram_link_tokens_telegram_user_id", table_name="telegram_link_tokens")
    op.drop_column("telegram_link_tokens", "attempts")
    op.drop_column("telegram_link_tokens", "telegram_user_id")
