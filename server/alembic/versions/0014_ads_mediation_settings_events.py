"""ads mediation settings and events

Revision ID: 0014_ads_mediation
Revises: 0013_payout_link_codes
Create Date: 2026-03-12 16:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0014_ads_mediation"
down_revision = "0013_payout_link_codes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """EN: Create global ads settings and ads events tables with one default mediation row.
    RU: Создать таблицы глобальных ads-настроек и ads-событий с одной дефолтной строкой медиации.
    """

    op.create_table(
        "ads_settings",
        sa.Column("id", sa.BigInteger(), autoincrement=False, nullable=False),
        sa.Column("provider", sa.String(length=32), server_default="dummy", nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("banner_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("rewarded_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("admob_app_id", sa.Text(), nullable=True),
        sa.Column("banner_topbar_world", sa.Text(), nullable=True),
        sa.Column("banner_topbar_cis", sa.Text(), nullable=True),
        sa.Column("rewarded_gameover_world", sa.Text(), nullable=True),
        sa.Column("rewarded_gameover_cis", sa.Text(), nullable=True),
        sa.Column("refresh_sec", sa.Integer(), server_default="30", nullable=False),
        sa.Column("min_banner_sec", sa.Integer(), server_default="5", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "ads_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("screen", sa.String(length=32), server_default="Unknown", nullable=False),
        sa.Column("placement", sa.String(length=64), nullable=False),
        sa.Column("event", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("flow_id", sa.String(length=32), nullable=True),
        sa.Column("ok", sa.Boolean(), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("meta", sa.JSON(), server_default=sa.text("'{}'::json"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ads_events_created_at", "ads_events", ["created_at"])
    op.create_index("ix_ads_events_user_id", "ads_events", ["user_id"])
    op.create_index("ix_ads_events_placement", "ads_events", ["placement"])
    op.create_index("ix_ads_events_event", "ads_events", ["event"])
    op.create_index("ix_ads_events_flow_id", "ads_events", ["flow_id"])

    op.execute(
        sa.text(
            """
            INSERT INTO ads_settings (
                id,
                provider,
                enabled,
                banner_enabled,
                rewarded_enabled,
                admob_app_id,
                banner_topbar_world,
                banner_topbar_cis,
                rewarded_gameover_world,
                rewarded_gameover_cis,
                refresh_sec,
                min_banner_sec
            ) VALUES (
                1,
                'admob_mediation',
                true,
                true,
                true,
                'ca-app-pub-XXXX~YYYY',
                'ca-app-pub-XXXX/BBBB',
                'ca-app-pub-XXXX/CCCC',
                'ca-app-pub-XXXX/RRRR',
                'ca-app-pub-XXXX/SSSS',
                30,
                5
            )
            """
        )
    )


def downgrade() -> None:
    """EN: Drop ads settings/events tables and their indexes.
    RU: Удалить таблицы ads-настроек/ads-событий и их индексы.
    """

    op.drop_index("ix_ads_events_flow_id", table_name="ads_events")
    op.drop_index("ix_ads_events_event", table_name="ads_events")
    op.drop_index("ix_ads_events_placement", table_name="ads_events")
    op.drop_index("ix_ads_events_user_id", table_name="ads_events")
    op.drop_index("ix_ads_events_created_at", table_name="ads_events")
    op.drop_table("ads_events")
    op.drop_table("ads_settings")
