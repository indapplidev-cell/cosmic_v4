"""telegram reset flow

Revision ID: 0012_tg_reset_flow
Revises: 0011_tg_verify_ch_username
Create Date: 2026-03-11 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0012_tg_reset_flow"
down_revision = "0011_tg_verify_ch_username"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """EN: Create telegram reset request/challenge tables for bot-only password reset.
    RU: Создать таблицы telegram reset request/challenge для bot-only сброса пароля.
    """

    op.create_table(
        "telegram_reset_request",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("reset_link_code_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=True),
        sa.Column("telegram_username", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tg_reset_request_user_id", "telegram_reset_request", ["user_id"])
    op.create_index("ix_tg_reset_request_code_hash", "telegram_reset_request", ["reset_link_code_hash"])
    op.create_index("ix_tg_reset_request_expires_at", "telegram_reset_request", ["expires_at"])
    op.create_index("ix_tg_reset_request_used_at", "telegram_reset_request", ["used_at"])
    op.create_index("ix_tg_reset_request_tg_uid", "telegram_reset_request", ["telegram_user_id"])

    op.create_table(
        "telegram_reset_challenge",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("confirm_code_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("telegram_username", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tg_reset_challenge_user_id", "telegram_reset_challenge", ["user_id"])
    op.create_index("ix_tg_reset_challenge_code_hash", "telegram_reset_challenge", ["confirm_code_hash"])
    op.create_index("ix_tg_reset_challenge_expires_at", "telegram_reset_challenge", ["expires_at"])
    op.create_index("ix_tg_reset_challenge_used_at", "telegram_reset_challenge", ["used_at"])
    op.create_index("ix_tg_reset_challenge_tg_uid", "telegram_reset_challenge", ["telegram_user_id"])


def downgrade() -> None:
    """EN: Drop telegram reset flow tables and related indexes.
    RU: Удалить таблицы telegram reset flow и связанные индексы.
    """

    op.drop_index("ix_tg_reset_challenge_tg_uid", table_name="telegram_reset_challenge")
    op.drop_index("ix_tg_reset_challenge_used_at", table_name="telegram_reset_challenge")
    op.drop_index("ix_tg_reset_challenge_expires_at", table_name="telegram_reset_challenge")
    op.drop_index("ix_tg_reset_challenge_code_hash", table_name="telegram_reset_challenge")
    op.drop_index("ix_tg_reset_challenge_user_id", table_name="telegram_reset_challenge")
    op.drop_table("telegram_reset_challenge")

    op.drop_index("ix_tg_reset_request_tg_uid", table_name="telegram_reset_request")
    op.drop_index("ix_tg_reset_request_used_at", table_name="telegram_reset_request")
    op.drop_index("ix_tg_reset_request_expires_at", table_name="telegram_reset_request")
    op.drop_index("ix_tg_reset_request_code_hash", table_name="telegram_reset_request")
    op.drop_index("ix_tg_reset_request_user_id", table_name="telegram_reset_request")
    op.drop_table("telegram_reset_request")
