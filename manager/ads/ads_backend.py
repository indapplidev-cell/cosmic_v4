"""EN: Backend transport helpers for ads config and ads events requests.
RU: Транспортные helper-функции backend для запросов конфига рекламы и ads-событий.
"""

from __future__ import annotations

import locale
import platform
import time
from typing import Any

from kivy.utils import platform as kivy_platform

from manager import auth_backend
from manager.ads.ads_types import AdsConfig, AdsEvent, AdsPlacementConfig, ads_log
from manager.session_manager import get_session_user_id


def _detect_locale_country() -> str:
    """EN: Resolve two-letter locale country code or return `ZZ` when unavailable.
    RU: Определить двухбуквенный код страны locale или вернуть `ZZ`, если он недоступен.
    """

    locale_value = str(locale.getdefaultlocale()[0] or "").strip()
    if "_" in locale_value:
        country = locale_value.rsplit("_", 1)[-1].upper()
        if len(country) == 2:
            return country
    return "ZZ"


def _detect_tz_offset() -> str:
    """EN: Return local timezone offset string in `+HHMM` format for ads config.
    RU: Вернуть строку локального смещения часового пояса в формате `+HHMM` для ads config.
    """

    return time.strftime("%z") or "+0000"


def _build_config_request() -> dict[str, Any]:
    """EN: Build request payload for `/ads/config` from local runtime metadata.
    RU: Собрать payload запроса для `/ads/config` из локальных runtime-метаданных.
    """

    return {
        "user_id": int(get_session_user_id()),
        "platform": str(kivy_platform or "unknown"),
        "app_version": "debug",
        "locale_country": _detect_locale_country(),
        "tz_offset": _detect_tz_offset(),
        "device": f"{platform.system()} {platform.machine()}".strip(),
    }


def _parse_config(payload: dict[str, Any]) -> AdsConfig:
    """EN: Convert raw backend payload into strongly-typed client ads config objects.
    RU: Преобразовать сырой backend-payload в строго типизированные клиентские ads-объекты.
    """

    placements: dict[str, AdsPlacementConfig] = {}
    raw_placements = payload.get("placements") if isinstance(payload, dict) else {}
    if isinstance(raw_placements, dict):
        for name, item in raw_placements.items():
            if not isinstance(item, dict):
                continue
            placements[str(name)] = AdsPlacementConfig(
                name=str(name),
                enabled=bool(item.get("enabled")),
                unit_id=str(item.get("unit_id") or ""),
                refresh_sec=int(item["refresh_sec"]) if item.get("refresh_sec") is not None else None,
                cooldown_sec=int(item["cooldown_sec"]) if item.get("cooldown_sec") is not None else None,
                reward_type=str(item.get("reward_type") or "") or None,
                reward_amount=int(item["reward_amount"]) if item.get("reward_amount") is not None else None,
            )
    return AdsConfig(
        ok=bool(payload.get("ok")),
        region=str(payload.get("region") or ""),
        provider=str(payload.get("provider") or ""),
        banner_enabled=bool(payload.get("banner_enabled")),
        rewarded_enabled=bool(payload.get("rewarded_enabled")),
        placements=placements,
        ts=int(payload.get("ts") or 0),
    )


def fetch_config() -> AdsConfig | None:
    """EN: Request ads config from backend and return parsed config or `None` on failure.
    RU: Запросить ads-конфиг у backend и вернуть распарсенный конфиг или `None` при ошибке.
    """

    payload = _build_config_request()
    if int(payload["user_id"]) <= 0:
        ads_log("config fetch skipped", reason="no_session")
        return None
    ads_log("config fetch request", platform=payload["platform"], locale_country=payload["locale_country"])
    status_code, response = auth_backend.authorized_post_json(
        "/ads/config",
        payload,
        tag="ADS_CONFIG",
    )
    ok = bool(isinstance(response, dict) and response.get("ok"))
    error_value = str(response.get("error") or "") if isinstance(response, dict) else "NETWORK"
    ads_log("config fetch response", status=status_code, ok=ok, error=error_value or "-")
    if not ok or not isinstance(response, dict):
        ads_log(
            "config fetch disabled",
            status=status_code,
            error=error_value or "NETWORK",
        )
        return None
    config = _parse_config(response)
    return config


def post_event(event: AdsEvent) -> bool:
    """EN: Post ads event to backend when session exists, otherwise safely skip the call.
    RU: Отправить ads-событие в backend при наличии сессии, иначе безопасно пропустить вызов.
    """

    if int(event.user_id) <= 0:
        ads_log("server event skipped", event=event.event, placement=event.placement, reason="no_session")
        return False
    payload = {
        "user_id": int(event.user_id),
        "provider": str(event.provider),
        "placement": str(event.placement),
        "event": str(event.event),
        "ts": int(event.ts),
        "extra": dict(event.extra or {}),
    }
    status_code, response = auth_backend.authorized_post_json(
        "/ads/event",
        payload,
        tag=f"ADS_EVENT_{event.event}",
    )
    posted = bool(isinstance(response, dict) and response.get("ok"))
    ads_log("event post", event=event.event, placement=event.placement, ok=posted, status=status_code)
    return posted


def current_user_id() -> int:
    """EN: Return the best-effort current user id for ads event payloads.
    RU: Вернуть best-effort текущий user id для payload ads-событий.
    """

    return int(get_session_user_id())
