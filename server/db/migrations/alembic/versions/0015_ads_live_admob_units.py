"""ads live admob ids

Revision ID: 0015_ads_live
Revises: 0014_ads_mediation
Create Date: 2026-03-12 20:45:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0015_ads_live"
down_revision = "0014_ads_mediation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """EN: Update singleton ads settings row with the current live AdMob identifiers.
    RU: Обновить singleton-строку ads settings актуальными идентификаторами live AdMob.
    """

    op.execute(
        sa.text(
            """
            UPDATE ads_settings
            SET
                provider = 'admob_mediation',
                enabled = true,
                banner_enabled = true,
                rewarded_enabled = true,
                admob_app_id = 'ca-app-pub-3827702693493328~6458359144',
                banner_topbar_world = 'ca-app-pub-3827702693493328/8892950794',
                banner_topbar_cis = 'ca-app-pub-3827702693493328/8892950794',
                rewarded_gameover_world = 'ca-app-pub-3827702693493328/3640624112',
                rewarded_gameover_cis = 'ca-app-pub-3827702693493328/3640624112',
                refresh_sec = 30,
                min_banner_sec = 5
            WHERE id = 1
            """
        )
    )


def downgrade() -> None:
    """EN: Revert singleton ads settings row back to placeholder AdMob identifiers.
    RU: Вернуть singleton-строку ads settings к placeholder-идентификаторам AdMob.
    """

    op.execute(
        sa.text(
            """
            UPDATE ads_settings
            SET
                provider = 'admob_mediation',
                enabled = true,
                banner_enabled = true,
                rewarded_enabled = true,
                admob_app_id = 'ca-app-pub-XXXX~YYYY',
                banner_topbar_world = 'ca-app-pub-XXXX/BBBB',
                banner_topbar_cis = 'ca-app-pub-XXXX/CCCC',
                rewarded_gameover_world = 'ca-app-pub-XXXX/RRRR',
                rewarded_gameover_cis = 'ca-app-pub-XXXX/SSSS',
                refresh_sec = 30,
                min_banner_sec = 5
            WHERE id = 1
            """
        )
    )
