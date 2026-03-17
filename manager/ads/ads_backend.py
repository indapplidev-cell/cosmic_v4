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
from manager.ads.ads_types import AdsConfig, AdsEvent, AdsPlacementConfig, ads_log, get_current_screen_name
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
        "screen": get_current_screen_name(),
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
        configured=bool(payload.get("configured")),
        banner_enabled=bool(payload.get("banner_enabled")),
        rewarded_enabled=bool(payload.get("rewarded_enabled")),
        admob_app_id=str(payload.get("admob_app_id") or "") or None,
        banner_ad_unit_id=str(payload.get("banner_ad_unit_id") or "") or None,
        rewarded_ad_unit_id=str(payload.get("rewarded_ad_unit_id") or "") or None,
        refresh_sec=int(payload.get("refresh_sec") or 30),
        min_banner_sec=int(payload.get("min_banner_sec") or 5),
        debug=bool(payload.get("debug")),
        error=str(payload.get("error") or "") or None,
        placements=placements,
    )


def fetch_config() -> AdsConfig | None:
    """EN: Request ads config from backend and return parsed config or `None` on failure.
    RU: Запросить ads-конфиг у backend и вернуть распарсенный конфиг или `None` при ошибке.
    """

    payload = _build_config_request()
    screen_name = get_current_screen_name()
    if int(payload["user_id"]) <= 0:
        ads_log("config fetch skipped", screen=screen_name, user_id=payload["user_id"], reason="no_session")
        return None
    ads_log(
        "config fetch request",
        screen=screen_name,
        user_id=payload["user_id"],
        platform=payload["platform"],
        locale_country=payload["locale_country"],
    )
    response = auth_backend.ads_config_fetch(
        int(payload["user_id"]),
        str(payload["platform"]),
        str(payload["locale_country"]),
        screen_name,
        app_version=str(payload["app_version"]),
    )
    status_code = int(response.get("_status", 0))
    response.pop("_status", None)
    ok = bool(isinstance(response, dict) and response.get("ok"))
    error_value = str(response.get("error") or "") if isinstance(response, dict) else "NETWORK"
    ads_log(
        "config fetch response",
        screen=screen_name,
        user_id=payload["user_id"],
        status=status_code,
        ok=ok,
        error=error_value or "-",
    )
    if not ok or not isinstance(response, dict):
        ads_log(
            "config fetch disabled",
            screen=screen_name,
            user_id=payload["user_id"],
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
        ads_log(
            "server event skipped",
            placement=event.placement,
            screen=get_current_screen_name(),
            user_id=event.user_id,
            provider=event.provider,
            event=event.event,
            reason="no_session",
        )
        return False
    payload = {
        "user_id": int(event.user_id),
        "screen": str(event.screen or get_current_screen_name()),
        "placement": str(event.placement),
        "event": str(event.event),
        "provider": str(event.provider),
        "flow_id": str(event.flow_id or "") or None,
        "ok": event.ok,
        "detail": str(event.detail or "") or None,
        "ts_client": float(event.ts_client or time.time()),
        "meta": dict(event.meta or {}),
    }
    response = auth_backend.ads_event_post(payload)
    status_code = int(response.get("_status", 0))
    response.pop("_status", None)
    posted = bool(isinstance(response, dict) and response.get("ok"))
    ads_log(
        "event post",
        placement=event.placement,
        screen=str(event.screen or get_current_screen_name()),
        user_id=event.user_id,
        provider=event.provider,
        event=event.event,
        ok=posted,
        status=status_code,
    )
    return posted


def current_user_id() -> int:
    """EN: Return the best-effort current user id for ads event payloads.
    RU: Вернуть best-effort текущий user id для payload ads-событий.
    """

    return int(get_session_user_id())
