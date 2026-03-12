"""EN: In-memory ads mediation service for region resolution and temporary placement config serving.
RU: In-memory ads mediation service для определения региона и временной раздачи конфигов плейсментов.
"""

from __future__ import annotations

import time
from typing import Any

from server.api.schemas import AdsConfigRequest

_CIS_COUNTRIES = {"RU", "BY", "KZ", "UA", "AM", "AZ", "GE", "KG", "MD", "TJ", "TM", "UZ"}
_PLACEMENT_KEYS = {"topbar_banner", "rewarded_gameover"}
_ADS_CONFIGS = {
    "cis": {
        "provider": "dummy",
        "placements": {
            "topbar_banner": {
                "enabled": True,
                "refresh_sec": 30,
                "unit_id": "DUMMY_BANNER_TOPBAR",
            },
            "rewarded_gameover": {
                "enabled": True,
                "cooldown_sec": 0,
                "unit_id": "DUMMY_REWARDED_GAMEOVER",
                "reward_type": "life",
                "reward_amount": 1,
            },
        },
    },
    "world": {
        "provider": "dummy",
        "placements": {
            "topbar_banner": {
                "enabled": True,
                "refresh_sec": 30,
                "unit_id": "DUMMY_BANNER_TOPBAR",
            },
            "rewarded_gameover": {
                "enabled": True,
                "cooldown_sec": 0,
                "unit_id": "DUMMY_REWARDED_GAMEOVER",
                "reward_type": "life",
                "reward_amount": 1,
            },
        },
    },
}


def resolve_region(locale_country: str) -> str:
    """EN: Resolve ads region using a minimal CIS-vs-world locale country heuristic.
    RU: Определить ads-регион через минимальную эвристику locale country: CIS против world.
    """

    country = str(locale_country or "").strip().upper()
    return "cis" if country in _CIS_COUNTRIES else "world"


def validate_placement_list(placements: dict[str, Any]) -> dict[str, Any]:
    """EN: Validate expected placement names and return normalized placement mapping.
    RU: Проверить ожидаемые имена плейсментов и вернуть нормализованную карту плейсментов.
    """

    normalized = dict(placements or {})
    missing = sorted(_PLACEMENT_KEYS.difference(normalized.keys()))
    if missing:
        raise ValueError(f"MISSING_PLACEMENTS:{','.join(missing)}")
    extra = sorted(set(normalized.keys()).difference(_PLACEMENT_KEYS))
    if extra:
        raise ValueError(f"UNEXPECTED_PLACEMENTS:{','.join(extra)}")
    return normalized


def get_ads_config(user_id: int, req: AdsConfigRequest) -> dict[str, Any]:
    """EN: Build ads-config response from region rules and static in-memory placement settings.
    RU: Собрать ответ ads-config из правил региона и статических in-memory настроек плейсментов.
    """

    region = resolve_region(req.locale_country)
    region_config = _ADS_CONFIGS[region]
    placements = validate_placement_list(region_config["placements"])
    return {
        "ok": True,
        "region": region,
        "provider": region_config["provider"],
        "banner_enabled": bool(placements["topbar_banner"].get("enabled")),
        "rewarded_enabled": bool(placements["rewarded_gameover"].get("enabled")),
        "placements": placements,
        "ts": int(time.time()),
        "user_id": int(user_id),
    }


def log_ads_event(user_id: int, provider: str, placement: str, event: str, ts: int, extra: dict[str, Any]) -> dict[str, Any]:
    """EN: Log authenticated ads event to stdout and return lightweight acknowledgement payload.
    RU: Залогировать authenticated ads-событие в stdout и вернуть легковесный payload подтверждения.
    """

    print(
        "[ADS][SERVER] "
        f"user_id={int(user_id)} provider={provider} placement={placement} event={event} ts={int(ts)} extra={dict(extra or {})}",
        flush=True,
    )
    return {"ok": True}
