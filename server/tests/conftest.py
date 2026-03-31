"""EN: Shared pytest bootstrap for server-side tests.
RU: Общий bootstrap pytest для серверных тестов.
"""

from __future__ import annotations

import os

import pytest


os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://user:pass@db.example.com:5432/game_galaxy?sslmode=require")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")
os.environ.setdefault("RESET_SECRET", "test-reset-secret")
os.environ.setdefault("PAY_BOT_TOKEN", "123456:TEST_PAY_BOT_TOKEN")
os.environ.setdefault("PAYOUT_MINIAPP_SECRET", "test-payout-miniapp-secret")
os.environ.setdefault("PAYOUT_MINIAPP_BOT_USERNAME", "escape2mars_bot")
os.environ.setdefault("ESCAPE2MARS_MINIAPP_SHORT_NAME", "escape2mars")
os.environ.setdefault("PAYOUT_MINIAPP_SESSION_TTL_SEC", "300")
os.environ.setdefault("PAYOUT_MINIAPP_AUTH_MAX_AGE_SEC", "300")


@pytest.fixture(autouse=True)
def _force_current_db_schema(monkeypatch):
    """EN: Force schema guard to current revision in API tests that do not validate Alembic itself.
    RU: Принудительно считать схему БД актуальной в API-тестах, которые не проверяют Alembic.
    """

    monkeypatch.setattr(
        "server.api.main.get_db_schema_status",
        lambda force_refresh=False: {
            "ok": True,
            "is_current": True,
            "current_revision": "test",
            "head_revision": "test",
        },
    )
