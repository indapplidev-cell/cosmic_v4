# -*- coding: utf-8 -*-
"""EN: Local JSON persistence for survive_timed campaign progress.
RU: Р›РѕРєР°Р»СЊРЅРѕРµ JSON-С…СЂР°РЅРёР»РёС‰Рµ РїСЂРѕРіСЂРµСЃСЃР° РєР°РјРїР°РЅРёРё survive_timed.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from kivy.app import App

from shared.constants.survive_timed_levels import get_default_level_number, get_max_level_number


_DEFAULT_STATE: dict[str, Any] = {
    "last_completed_level_number": 0,
    "current_level_number": 1,
    "campaign_completed": False,
    "updated_at": "",
}


def _storage_path() -> Path:
    """EN: Return survive_timed campaign progress JSON path under user_data_dir.
    RU: Р’РµСЂРЅСѓС‚СЊ РїСѓС‚СЊ JSON РїСЂРѕРіСЂРµСЃСЃР° РєР°РјРїР°РЅРёРё survive_timed РІРЅСѓС‚СЂРё user_data_dir.
    """

    app = App.get_running_app()
    user_dir = Path(getattr(app, "user_data_dir", ".")) if app else Path(".")
    return user_dir / "gameplay" / "modes" / "survive_timed" / "campaign_progress.json"


def _utc_now_iso() -> str:
    """EN: Return current UTC timestamp in ISO format.
    RU: Р’РµСЂРЅСѓС‚СЊ С‚РµРєСѓС‰СѓСЋ UTC-РґР°С‚Сѓ РІ ISO-С„РѕСЂРјР°С‚Рµ.
    """

    return datetime.now(timezone.utc).isoformat()


def _normalize_level(level_number: int) -> int:
    """EN: Clamp level number into survive_timed shipped range.
    RU: РћРіСЂР°РЅРёС‡РёС‚СЊ РЅРѕРјРµСЂ СѓСЂРѕРІРЅСЏ РґРёР°РїР°Р·РѕРЅРѕРј РІСЃС‚СЂРѕРµРЅРЅС‹С… СѓСЂРѕРІРЅРµР№ survive_timed.
    """

    return min(max(int(level_number), get_default_level_number()), get_max_level_number())


def _normalize_payload(data: Any) -> dict[str, Any]:
    """EN: Normalize arbitrary JSON into supported survive_timed progress schema.
    RU: РќРѕСЂРјР°Р»РёР·РѕРІР°С‚СЊ РїСЂРѕРёР·РІРѕР»СЊРЅС‹Р№ JSON РІ РїРѕРґРґРµСЂР¶РёРІР°РµРјСѓСЋ СЃС…РµРјСѓ РїСЂРѕРіСЂРµСЃСЃР° survive_timed.
    """

    payload = dict(_DEFAULT_STATE)
    if isinstance(data, dict):
        payload["last_completed_level_number"] = max(int(data.get("last_completed_level_number", 0) or 0), 0)
        payload["current_level_number"] = _normalize_level(data.get("current_level_number", get_default_level_number()))
        payload["campaign_completed"] = bool(data.get("campaign_completed", False))
        payload["updated_at"] = str(data.get("updated_at", "") or "")
    if payload["last_completed_level_number"] >= get_max_level_number():
        payload["last_completed_level_number"] = get_max_level_number()
        payload["current_level_number"] = get_max_level_number()
        payload["campaign_completed"] = True
    return payload


def load_campaign_progress() -> dict[str, Any]:
    """EN: Load survive_timed campaign progress or defaults when file is absent/broken.
    RU: Р—Р°РіСЂСѓР·РёС‚СЊ РїСЂРѕРіСЂРµСЃСЃ РєР°РјРїР°РЅРёРё survive_timed РёР»Рё РґРµС„РѕР»С‚ РїСЂРё РѕС‚СЃСѓС‚СЃС‚РІРёРё/РїРѕРІСЂРµР¶РґРµРЅРёРё С„Р°Р№Р»Р°.
    """

    path = _storage_path()
    if not path.exists():
        return _normalize_payload(_DEFAULT_STATE)
    try:
        with path.open("r", encoding="utf-8") as fh:
            return _normalize_payload(json.load(fh))
    except Exception:
        return _normalize_payload(_DEFAULT_STATE)


def save_campaign_progress(payload: dict[str, Any]) -> dict[str, Any]:
    """EN: Persist normalized survive_timed campaign progress atomically.
    RU: РђС‚РѕРјР°СЂРЅРѕ СЃРѕС…СЂР°РЅРёС‚СЊ РЅРѕСЂРјР°Р»РёР·РѕРІР°РЅРЅС‹Р№ РїСЂРѕРіСЂРµСЃСЃ РєР°РјРїР°РЅРёРё survive_timed.
    """

    normalized = _normalize_payload(payload)
    normalized["updated_at"] = _utc_now_iso()
    return _write_campaign_progress(normalized)


def save_campaign_progress_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    """EN: Persist one server-authoritative survive_timed campaign progress snapshot.
    RU: РЎРѕС…СЂР°РЅРёС‚СЊ РѕРґРёРЅ server-authoritative snapshot РїСЂРѕРіСЂРµСЃСЃР° РєР°РјРїР°РЅРёРё survive_timed.
    """

    normalized = _normalize_payload(payload)
    normalized["updated_at"] = str((payload or {}).get("updated_at", "") or "")
    return _write_campaign_progress(normalized)


def _write_campaign_progress(normalized: dict[str, Any]) -> dict[str, Any]:
    """EN: Atomically write an already normalized survive_timed campaign progress payload.
    RU: РђС‚РѕРјР°СЂРЅРѕ Р·Р°РїРёСЃР°С‚СЊ СѓР¶Рµ РЅРѕСЂРјР°Р»РёР·РѕРІР°РЅРЅС‹Р№ payload РїСЂРѕРіСЂРµСЃСЃР° РєР°РјРїР°РЅРёРё survive_timed.
    """

    path = _storage_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp")
    with tmp_path.open("w", encoding="utf-8") as fh:
        json.dump(normalized, fh, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)
    return normalized

