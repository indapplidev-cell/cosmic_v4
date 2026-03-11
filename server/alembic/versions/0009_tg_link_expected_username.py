"""EN: Add expected Telegram username and explicit used flag to link tokens.
RU: Добавить ожидаемый Telegram username и явный флаг used в link-токены.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0009_tg_link_expected_username"
down_revision = "0008_refresh_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """EN: Extend telegram_link_tokens with expected username and used flag.
    RU: Расширить telegram_link_tokens ожидаемым username и флагом used.
    """

    op.add_column(
        "telegram_link_tokens",
        sa.Column("expected_tg_username", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column(
        "telegram_link_tokens",
        sa.Column("used", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_index(
        "ix_telegram_link_tokens_expected_tg_username",
        "telegram_link_tokens",
        ["expected_tg_username"],
    )
    op.create_index(
        "ix_telegram_link_tokens_used",
        "telegram_link_tokens",
        ["used"],
    )
    op.execute("UPDATE telegram_link_tokens SET used = TRUE WHERE used_at IS NOT NULL")


def downgrade() -> None:
    """EN: Roll back expected username and used flag additions.
    RU: Откатить добавление expected username и флага used.
    """

    op.drop_index("ix_telegram_link_tokens_used", table_name="telegram_link_tokens")
    op.drop_index("ix_telegram_link_tokens_expected_tg_username", table_name="telegram_link_tokens")
    op.drop_column("telegram_link_tokens", "used")
    op.drop_column("telegram_link_tokens", "expected_tg_username")

