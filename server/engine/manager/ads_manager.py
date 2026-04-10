"""EN: Server-side ads mediation config and ads event persistence service.
RU: Серверный сервис конфигурации ads-медиации и сохранения ads-событий.
"""

from __future__ import annotations

import time
from typing import Any

from sqlalchemy.orm import Session

from server.app.api.schemas import AdsConfigRequest
from server.db.sessions.session_factory import get_session
from server.db.models.ads_event import AdsEvent
from server.db.models.ads_setting import AdsSetting

_CIS_COUNTRIES = {"RU", "BY", "KZ", "AM", "AZ", "GE", "KG", "MD", "TJ", "TM", "UZ"}
_DEFAULT_ADMOB_APP_ID = "ca-app-pub-3940256099942544~3347511713"
_DEFAULT_BANNER_WORLD = "ca-app-pub-3940256099942544/6300978111"
_DEFAULT_BANNER_CIS = "ca-app-pub-3940256099942544/6300978111"
_DEFAULT_REWARDED_WORLD = "ca-app-pub-3940256099942544/5224354917"
_DEFAULT_REWARDED_CIS = "ca-app-pub-3940256099942544/5224354917"


def resolve_region(locale_country: str) -> str:
    """EN: Map locale country to `CIS` or `WORLD` using a fixed allowlist heuristic.
    RU: Сопоставить locale country с `CIS` или `WORLD` через фиксированную allowlist-эвристику.
    """

    country = str(locale_country or "").strip().upper()
    return "CIS" if country in _CIS_COUNTRIES else "WORLD"


def _ensure_ads_settings(session: Session) -> AdsSetting:
    """EN: Ensure the singleton ads_settings row exists and return it.
    RU: Гарантировать существование singleton-строки ads_settings и вернуть её.
    """

    settings = session.get(AdsSetting, 1)
    if settings is not None:
        return settings
    settings = AdsSetting(
        id=1,
        provider="admob_mediation",
        enabled=True,
        banner_enabled=True,
        rewarded_enabled=True,
        admob_app_id=_DEFAULT_ADMOB_APP_ID,
        banner_topbar_world=_DEFAULT_BANNER_WORLD,
        banner_topbar_cis=_DEFAULT_BANNER_CIS,
        rewarded_gameover_world=_DEFAULT_REWARDED_WORLD,
        rewarded_gameover_cis=_DEFAULT_REWARDED_CIS,
        refresh_sec=30,
        min_banner_sec=5,
    )
    session.add(settings)
    session.flush()
    return settings


def _clean_text(value: object) -> str | None:
    """EN: Normalize optional text field into a stripped string or `None`.
    RU: Нормализовать опциональное текстовое поле в обрезанную строку или `None`.
    """

    text = str(value or "").strip()
    return text or None


def _configured_for(settings: AdsSetting, region: str) -> tuple[bool, str | None, str | None]:
    """EN: Resolve region-specific unit ids and whether AdMob mediation is fully configured.
    RU: Определить region-specific unit id и признак полной настройки AdMob Mediation.
    """

    banner_unit = (
        _clean_text(settings.banner_topbar_cis)
        if region == "CIS"
        else _clean_text(settings.banner_topbar_world)
    )
    rewarded_unit = (
        _clean_text(settings.rewarded_gameover_cis)
        if region == "CIS"
        else _clean_text(settings.rewarded_gameover_world)
    )
    configured = bool(
        _clean_text(settings.provider) == "admob_mediation"
        and bool(settings.enabled)
        and _clean_text(settings.admob_app_id)
        and banner_unit
        and rewarded_unit
    )
    return configured, banner_unit, rewarded_unit


def get_ads_config(user_id: int, req: AdsConfigRequest) -> dict[str, Any]:
    """EN: Build ads config response from DB-backed global settings and region rules.
    RU: Собрать ads-config ответ из глобальных настроек в БД и правил региона.
    """

    with get_session() as session:
        settings = _ensure_ads_settings(session)
        region = resolve_region(req.locale_country)
        provider = str(settings.provider or "dummy")
        configured, banner_unit, rewarded_unit = _configured_for(settings, region)

        if not bool(settings.enabled) or provider == "dummy":
            provider = "dummy"
            configured = False

        banner_enabled = bool(settings.banner_enabled) and bool(settings.enabled)
        rewarded_enabled = bool(settings.rewarded_enabled) and bool(settings.enabled)

        if not configured:
            banner_enabled = False
            rewarded_enabled = False

        return {
            "ok": True,
            "provider": provider,
            "region": region,
            "configured": bool(configured),
            "banner_enabled": bool(banner_enabled),
            "rewarded_enabled": bool(rewarded_enabled),
            "banner_ad_unit_id": banner_unit if configured else None,
            "rewarded_ad_unit_id": rewarded_unit if configured else None,
            "admob_app_id": _clean_text(settings.admob_app_id) if configured else None,
            "refresh_sec": max(int(settings.refresh_sec or 30), 0),
            "min_banner_sec": max(int(settings.min_banner_sec or 5), 5),
            "debug": False,
            "error": None,
            "user_id": int(user_id),
            "screen": _clean_text(req.screen) or "Unknown",
            "platform": str(req.platform or "unknown"),
            "locale_country": str(req.locale_country or "").upper(),
            "ts": int(time.time()),
        }


def log_ads_event(
    *,
    user_id: int,
    screen: str,
    placement: str,
    event: str,
    provider: str,
    flow_id: str | None,
    ok: bool | None,
    detail: str | None,
    ts_client: float | None,
    meta: dict[str, Any] | None,
) -> dict[str, Any]:
    """EN: Persist authenticated ads event and mirror a safe diagnostic line to stdout.
    RU: Сохранить аутентифицированное ads-событие и продублировать безопасную строку диагностики в stdout.
    """

    normalized_meta = dict(meta or {})
    if ts_client is not None:
        normalized_meta.setdefault("ts_client", float(ts_client))
    with get_session() as session:
        row = AdsEvent(
            user_id=int(user_id),
            screen=str(screen or "Unknown"),
            placement=str(placement),
            event=str(event),
            provider=str(provider),
            flow_id=_clean_text(flow_id),
            ok=ok if ok is None else bool(ok),
            detail=_clean_text(detail),
            meta=normalized_meta,
        )
        session.add(row)
        session.flush()
    print(
        "[ADS][SERVER] "
        f"user_id={int(user_id)} screen={screen or 'Unknown'} placement={placement} "
        f"event={event} provider={provider} flow_id={_clean_text(flow_id) or '-'} "
        f"ok={ok} detail={_clean_text(detail) or '-'}",
        flush=True,
    )
    return {"ok": True}
