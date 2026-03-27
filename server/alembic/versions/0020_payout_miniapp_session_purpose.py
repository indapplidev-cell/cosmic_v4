"""telegram miniapp session purpose

Revision ID: 0020_payout_miniapp_session_purpose
Revises: 0019_payout_requests_and_reserved_balance
Create Date: 2026-03-27 00:10:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0020_payout_miniapp_session_purpose"
down_revision = "0019_payout_requests_and_reserved_balance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """EN: Add purpose column so one Mini App verification table can serve payout and telegram_link flows.
    RU: Добавить колонку purpose, чтобы одна таблица Mini App verification обслуживала payout и telegram_link.
    """

    op.add_column(
        "payout_miniapp_sessions",
        sa.Column("purpose", sa.Text(), nullable=False, server_default="payout"),
    )
    op.create_index("ix_payout_miniapp_sessions_purpose", "payout_miniapp_sessions", ["purpose"])


def downgrade() -> None:
    """EN: Drop purpose column from Mini App verification sessions.
    RU: Удалить колонку purpose из Mini App verification sessions.
    """

    op.drop_index("ix_payout_miniapp_sessions_purpose", table_name="payout_miniapp_sessions")
    op.drop_column("payout_miniapp_sessions", "purpose")
