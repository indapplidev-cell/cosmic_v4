"""telegram verify challenge username

Revision ID: 0011_tg_verify_ch_username
Revises: 0010_telegram_accounts_enrich
Create Date: 2026-03-11 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0011_tg_verify_ch_username"
down_revision = "0010_telegram_accounts_enrich"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """EN: Add telegram_username column to verify challenges for server-trusted username sync.
    RU: Добавить колонку telegram_username в verify challenges для серверной синхронизации доверенного username.
    """

    op.add_column(
        "telegram_verify_challenges",
        sa.Column("telegram_username", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_tg_verify_challenges_telegram_username",
        "telegram_verify_challenges",
        ["telegram_username"],
    )


def downgrade() -> None:
    """EN: Drop telegram_username column and related index from verify challenges.
    RU: Удалить колонку telegram_username и связанный индекс из verify challenges.
    """

    op.drop_index("ix_tg_verify_challenges_telegram_username", table_name="telegram_verify_challenges")
    op.drop_column("telegram_verify_challenges", "telegram_username")
