"""EN: Shared ad config, event, and result dataclasses for the client ads layer.
RU: Общие dataclass-структуры конфига, событий и результатов для клиентского слоя рекламы.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def ads_log(message: str, **fields: object) -> None:
    """EN: Print one unified `[ADS]` log line with stable key=value fields.
    RU: Печатать единую строку лога `[ADS]` со стабильными полями key=value.
    """

    suffix = ""
    if fields:
        suffix = " " + " ".join(f"{key}={value}" for key, value in fields.items())
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
    banner_enabled: bool = False
    rewarded_enabled: bool = False
    placements: dict[str, AdsPlacementConfig] = field(default_factory=dict)
    ts: int = 0


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


@dataclass(slots=True)
class AdsEvent:
    """EN: Client event payload posted to `/ads/event` for server-side collection.
    RU: Payload клиентского события, отправляемый на `/ads/event` для серверного сбора.
    """

    user_id: int
    provider: str
    placement: str
    event: str
    ts: int
    extra: dict[str, Any] = field(default_factory=dict)
