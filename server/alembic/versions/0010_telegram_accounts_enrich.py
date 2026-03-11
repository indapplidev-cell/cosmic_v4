"""EN: Extend telegram_accounts with username/update timestamp and nullable verified_at.
RU: Расширение telegram_accounts полями username/updated_at и перевод verified_at в nullable.

Revision ID: 0010_telegram_accounts_enrich
Revises: 0009_tg_link_expected_username
Create Date: 2026-03-11 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0010_telegram_accounts_enrich"
down_revision = "0009_tg_link_expected_username"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """EN: Add telegram username and updated_at fields; allow verified_at to be null.
    RU: Добавить поля username и updated_at; разрешить nullable для verified_at.
    """

    op.add_column("telegram_accounts", sa.Column("telegram_username", sa.Text(), nullable=True))
    op.add_column(
        "telegram_accounts",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.alter_column("telegram_accounts", "verified_at", existing_type=sa.DateTime(timezone=True), nullable=True)


def downgrade() -> None:
    """EN: Revert telegram_accounts extension changes.
    RU: Откатить изменения расширения telegram_accounts.
    """

    op.alter_column("telegram_accounts", "verified_at", existing_type=sa.DateTime(timezone=True), nullable=False)
    op.drop_column("telegram_accounts", "updated_at")
    op.drop_column("telegram_accounts", "telegram_username")
