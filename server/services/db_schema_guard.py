"""EN: Runtime guard for checking whether DB schema revision matches Alembic head.
RU: Runtime-защита для проверки, что ревизия схемы БД совпадает с Alembic head.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
import time

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text

from server.db import engine


_CACHE_LOCK = Lock()
_CACHE_TTL_SECONDS = 5.0
_CACHE_DATA: dict = {"expires_at": 0.0, "value": None}


def _utc_now_iso() -> str:
    """EN: Return current UTC timestamp in ISO format.
    RU: Вернуть текущий UTC-временной штамп в формате ISO.
    """

    return datetime.now(timezone.utc).isoformat()


def _get_alembic_ini_path() -> Path:
    """EN: Resolve absolute path to server alembic.ini.
    RU: Получить абсолютный путь к server/alembic.ini.
    """

    return Path(__file__).resolve().parents[1] / "alembic.ini"


def _get_head_revision() -> str | None:
    """EN: Resolve Alembic head revision from migration scripts.
    RU: Получить Alembic head-ревизию из migration-скриптов.
    """

    cfg = Config(str(_get_alembic_ini_path()))
    script_dir = ScriptDirectory.from_config(cfg)
    heads = script_dir.get_heads()
    if not heads:
        return None
    if len(heads) == 1:
        return str(heads[0])
    return ",".join(sorted(str(item) for item in heads))


def _get_current_revision() -> str | None:
    """EN: Read current DB revision from alembic_version table.
    RU: Прочитать текущую ревизию БД из таблицы alembic_version.
    """

    with engine.connect() as conn:
        return conn.scalar(text("SELECT version_num FROM alembic_version LIMIT 1"))


def _compute_status() -> dict:
    """EN: Compute DB schema freshness status against Alembic head.
    RU: Вычислить статус актуальности схемы БД относительно Alembic head.
    """

    timestamp = _utc_now_iso()
    try:
        head_revision = _get_head_revision()
        current_revision = _get_current_revision()
    except Exception as exc:
        return {
            "ok": False,
            "error": "DB_SCHEMA_CHECK_FAILED",
            "message": str(exc),
            "current_revision": None,
            "head_revision": None,
            "is_current": False,
            "checked_at": timestamp,
        }

    is_current = bool(head_revision and current_revision and current_revision == head_revision)
    return {
        "ok": True,
        "error": None,
        "message": None,
        "current_revision": current_revision,
        "head_revision": head_revision,
        "is_current": is_current,
        "checked_at": timestamp,
    }


def get_db_schema_status(*, force_refresh: bool = False) -> dict:
    """EN: Return cached DB schema status with short TTL to reduce request overhead.
    RU: Вернуть кешированный статус схемы БД с коротким TTL для снижения накладных расходов.
    """

    now = time.monotonic()
    with _CACHE_LOCK:
        if (
            not force_refresh
            and _CACHE_DATA["value"] is not None
            and float(_CACHE_DATA["expires_at"]) > now
        ):
            return dict(_CACHE_DATA["value"])

        value = _compute_status()
        _CACHE_DATA["value"] = dict(value)
        _CACHE_DATA["expires_at"] = now + _CACHE_TTL_SECONDS
        return value

