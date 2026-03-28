"""payout requests and reserved balance

Revision ID: 0019_payout_requests_and_reserved_balance
Revises: 0018_payout_miniapp_sessions
Create Date: 2026-03-27 00:00:01
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0019_payout_requests_and_reserved_balance"
down_revision = "0018_payout_miniapp_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """EN: Add reserved balance to profile_games and create internal payout_requests table.
    RU: Добавить reserved balance в profile_games и создать таблицу внутренних payout_requests.
    """

    op.add_column(
        "profile_games",
        sa.Column("reserved_balance", sa.Numeric(12, 3), nullable=True, server_default=sa.text("0")),
    )

    op.create_table(
        "payout_requests",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("wallet_address", sa.Text(), nullable=False),
        sa.Column("asset_code", sa.Text(), nullable=False, server_default="USDT"),
        sa.Column("amount", sa.Numeric(12, 3), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="reserved"),
        sa.Column(
            "miniapp_session_id",
            sa.BigInteger(),
            sa.ForeignKey("payout_miniapp_sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("fail_reason", sa.Text(), nullable=True),
    )
    op.create_index("ix_payout_requests_user_id", "payout_requests", ["user_id"])
    op.create_index("ix_payout_requests_telegram_user_id", "payout_requests", ["telegram_user_id"])
    op.create_index("ix_payout_requests_status", "payout_requests", ["status"])
    op.create_index("ix_payout_requests_miniapp_session_id", "payout_requests", ["miniapp_session_id"])


def downgrade() -> None:
    """EN: Drop payout_requests table and reserved balance column.
    RU: Удалить таблицу payout_requests и колонку reserved balance.
    """

    op.drop_index("ix_payout_requests_miniapp_session_id", table_name="payout_requests")
    op.drop_index("ix_payout_requests_status", table_name="payout_requests")
    op.drop_index("ix_payout_requests_telegram_user_id", table_name="payout_requests")
    op.drop_index("ix_payout_requests_user_id", table_name="payout_requests")
    op.drop_table("payout_requests")
    op.drop_column("profile_games", "reserved_balance")
