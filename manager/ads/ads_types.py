"""EN: Shared ad config, event, and result dataclasses for the client ads layer.
RU: Общие dataclass-структуры конфига, событий и результатов для клиентского слоя рекламы.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from manager.screen_tracker import ScreenTracker


def generate_flow_id() -> str:
    """EN: Generate a short stable flow identifier used to correlate one rewarded chain in logs.
    RU: Сгенерировать короткий стабильный flow identifier для связки одной rewarded-цепочки в логах.
    """

    return uuid4().hex[:8]


def get_current_screen_name(app=None) -> str:
    """EN: Resolve the currently active app screen name for ads diagnostics.
    RU: Определить имя текущего активного экрана приложения для ads-диагностики.
    """

    del app
    return ScreenTracker.get_screen()


def ads_log(message: str, **fields: object) -> None:
    """EN: Print one unified `[ADS]` log line with stable key=value fields.
    RU: Печатать единую строку лога `[ADS]` со стабильными полями key=value.
    """

    suffix = ""
    if fields:
        ordered_keys = [
            "flow_id",
            "placement",
            "screen",
            "user_id",
            "provider",
            "debug",
            "trigger",
            "event",
            "enabled",
            "attached",
            "granted",
            "status",
            "ok",
            "reason",
            "detail",
            "context",
            "locale_country",
            "platform",
        ]
        rendered: list[str] = []
        seen: set[str] = set()
        for key in ordered_keys:
            if key in fields:
                rendered.append(f"{key}={fields[key]}")
                seen.add(key)
        for key, value in fields.items():
            if key in seen:
                continue
            rendered.append(f"{key}={value}")
        suffix = " " + " ".join(rendered)
    print(f"[ADS] {message}{suffix}", flush=True)


@dataclass(slots=True)
class AdsPlacementConfig:
    """EN: Normalized client-side placement configuration received from backend.
    RU: Нормализованная клиентская конфигурация плейсмента, полученная от backend.
    """

    name: str
    enabled: bool
    unit_id: str
    refresh_sec: int | None = None
    cooldown_sec: int | None = None
    reward_type: str | None = None
    reward_amount: int | None = None


@dataclass(slots=True)
class AdsConfig:
    """EN: Normalized ads mediation config returned by `/ads/config`.
    RU: Нормализованный конфиг медиации рекламы, возвращаемый `/ads/config`.
    """

    ok: bool
    region: str
    provider: str
    configured: bool = False
    banner_enabled: bool = False
    rewarded_enabled: bool = False
    admob_app_id: str | None = None
    banner_ad_unit_id: str | None = None
    rewarded_ad_unit_id: str | None = None
    refresh_sec: int = 30
    min_banner_sec: int = 5
    debug: bool = False
    error: str | None = None
    placements: dict[str, AdsPlacementConfig] = field(default_factory=dict)


@dataclass(slots=True)
class BannerState:
    """EN: Lightweight banner state exposed to UI for diagnostics and attachment logic.
    RU: Легковесное состояние баннера для UI, диагностики и логики attach.
    """

    enabled: bool
    provider: str
    placement: str
    unit_id: str
    attached: bool = False


@dataclass(slots=True)
class RewardedResult:
    """EN: Rewarded flow result returned to UI callback after ad attempt finishes.
    RU: Результат rewarded-flow, возвращаемый в UI callback после завершения попытки показа.
    """

    reward_granted: bool
    placement: str
    provider: str
    message: str = ""
    debug: bool = False
    flow_id: str = ""


@dataclass(slots=True)
class AdsEvent:
    """EN: Client event payload posted to `/ads/event` for server-side collection.
    RU: Payload клиентского события, отправляемый на `/ads/event` для серверного сбора.
    """

    user_id: int
    provider: str
    placement: str
    event: str
    screen: str | None = None
    flow_id: str | None = None
    ok: bool | None = None
    detail: str | None = None
    ts_client: float | None = None
    meta: dict[str, Any] = field(default_factory=dict)
