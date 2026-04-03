# -*- coding: utf-8 -*-
"""EN: Local JSON persistence for per-level survive_timed results.
RU: Локальное JSON-хранилище результатов survive_timed по уровням.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from kivy.app import App


_DEFAULT_DATA: dict[str, Any] = {
    "levels": {},
    "updated_at": "",
}


def _storage_path() -> Path:
    """EN: Return survive_timed level results JSON path under user_data_dir.
    RU: Вернуть путь JSON результатов survive_timed по уровням внутри user_data_dir.
    """

    app = App.get_running_app()
    user_dir = Path(getattr(app, "user_data_dir", ".")) if app else Path(".")
    return user_dir / "gameplay" / "modes" / "survive_timed" / "level_results.json"


def _utc_now_iso() -> str:
    """EN: Return current UTC timestamp in ISO format.
    RU: Вернуть текущую UTC-дату в ISO-формате.
    """

    return datetime.now(timezone.utc).isoformat()


def _normalize_level_state(data: Any) -> dict[str, Any]:
    """EN: Normalize one survive_timed level result payload.
    RU: Нормализовать payload результата одного уровня survive_timed.
    """

    source = data if isinstance(data, dict) else {}
    return {
        "best_survival_sec": max(float(source.get("best_survival_sec", 0.0) or 0.0), 0.0),
        "last_survival_sec": max(float(source.get("last_survival_sec", 0.0) or 0.0), 0.0),
        "attempts_count": max(int(source.get("attempts_count", 0) or 0), 0),
        "completed_count": max(int(source.get("completed_count", 0) or 0), 0),
        "last_result": str(source.get("last_result", "") or ""),
    }


def _normalize_payload(data: Any) -> dict[str, Any]:
    """EN: Normalize arbitrary JSON into supported survive_timed results schema.
    RU: Нормализовать произвольный JSON в поддерживаемую схему результатов survive_timed.
    """

    payload = dict(_DEFAULT_DATA)
    levels = {}
    if isinstance(data, dict):
        source_levels = data.get("levels", {})
        if isinstance(source_levels, dict):
            for raw_level, level_state in source_levels.items():
                try:
                    level_number = max(int(raw_level), 1)
                except Exception:
                    continue
                levels[str(level_number)] = _normalize_level_state(level_state)
        payload["updated_at"] = str(data.get("updated_at", "") or "")
    payload["levels"] = levels
    return payload


def load_level_results() -> dict[str, Any]:
    """EN: Load survive_timed level results or defaults when file is absent/broken.
    RU: Загрузить результаты survive_timed по уровням или дефолт при отсутствии/повреждении файла.
    """

    path = _storage_path()
    if not path.exists():
        return _normalize_payload(_DEFAULT_DATA)
    try:
        with path.open("r", encoding="utf-8") as fh:
            return _normalize_payload(json.load(fh))
    except Exception:
        return _normalize_payload(_DEFAULT_DATA)


def save_level_results(payload: dict[str, Any]) -> dict[str, Any]:
    """EN: Persist normalized survive_timed level results atomically.
    RU: Атомарно сохранить нормализованные результаты survive_timed по уровням.
    """

    normalized = _normalize_payload(payload)
    normalized["updated_at"] = _utc_now_iso()
    return _write_level_results(normalized)


def save_level_result_snapshot(level_number: int, level_state: dict[str, Any], *, updated_at: str = "") -> dict[str, Any]:
    """EN: Persist one server-authoritative survive_timed level-result snapshot.
    RU: Сохранить один server-authoritative snapshot результата уровня survive_timed.
    """

    payload = load_level_results()
    levels = dict(payload.get("levels", {}))
    levels[str(max(int(level_number), 1))] = _normalize_level_state(level_state)
    normalized = _normalize_payload({"levels": levels, "updated_at": str(updated_at or "")})
    return _write_level_results(normalized)


def _write_level_results(normalized: dict[str, Any]) -> dict[str, Any]:
    """EN: Atomically write an already normalized survive_timed level-results payload.
    RU: Атомарно записать уже нормализованный payload результатов survive_timed.
    """

    path = _storage_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp")
    with tmp_path.open("w", encoding="utf-8") as fh:
        json.dump(normalized, fh, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)
    return normalized
