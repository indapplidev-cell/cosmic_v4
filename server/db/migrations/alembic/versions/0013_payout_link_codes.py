"""payout link codes

Revision ID: 0013_payout_link_codes
Revises: 0012_tg_reset_flow
Create Date: 2026-03-11 00:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0013_payout_link_codes"
down_revision = "0012_tg_reset_flow"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """EN: Create payout_link_codes table for paybot deep-link acknowledgement.
    RU: Создать таблицу payout_link_codes для подтверждения deep-link через paybot.
    """

    op.create_table(
        "payout_link_codes",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("code_hash", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("purpose", sa.String(length=32), server_default="payout", nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code_hash", name="uq_payout_link_codes_code_hash"),
    )
    op.create_index("ix_payout_link_codes_user_id", "payout_link_codes", ["user_id"])
    op.create_index("ix_payout_link_codes_code_hash", "payout_link_codes", ["code_hash"])
    op.create_index("ix_payout_link_codes_expires_at", "payout_link_codes", ["expires_at"])
    op.create_index("ix_payout_link_codes_used_at", "payout_link_codes", ["used_at"])


def downgrade() -> None:
    """EN: Drop payout_link_codes table and indexes.
    RU: Удалить таблицу payout_link_codes и её индексы.
    """

    op.drop_index("ix_payout_link_codes_used_at", table_name="payout_link_codes")
    op.drop_index("ix_payout_link_codes_expires_at", table_name="payout_link_codes")
    op.drop_index("ix_payout_link_codes_code_hash", table_name="payout_link_codes")
    op.drop_index("ix_payout_link_codes_user_id", table_name="payout_link_codes")
    op.drop_table("payout_link_codes")
