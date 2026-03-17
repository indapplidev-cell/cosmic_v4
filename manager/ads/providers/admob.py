"""EN: Android AdMob Mediation provider backed by a pyjnius bridge on Android only.
RU: Android-провайдер AdMob Mediation, работающий через pyjnius bridge только на Android.
"""

from __future__ import annotations

import time
from typing import Callable

from kivy.clock import Clock
from kivy.utils import platform as kivy_platform

from manager.ads.ads_types import AdsPlacementConfig, RewardedResult, ads_log
from manager.ads.providers.base import BaseAdsProvider


class AdMobAdsProvider(BaseAdsProvider):
    """EN: Android runtime provider that delegates banner and rewarded operations into Java bridge.
    RU: Android runtime-провайдер, делегирующий banner и rewarded-операции в Java bridge.
    """

    def __init__(self, provider_name: str = "admob_mediation", admob_app_id: str | None = None) -> None:
        """EN: Store provider name and app id, then bind the Android bridge only on Android.
        RU: Сохранить имя провайдера и app id, затем подключить Android bridge только на Android.
        """

        self._provider_name = str(provider_name or "admob_mediation")
        self._admob_app_id = str(admob_app_id or "")
        self._bridge = None
        self._bridge_error = ""
        self._rewarded_poll_ev = None
        self._rewarded_load_deadline = 0.0
        if str(kivy_platform or "") == "android":
            try:
                from platforms.android.ads_bridge import AndroidAdsBridge

                self._bridge = AndroidAdsBridge()
                ads_log("provider bridge ready", provider=self._provider_name, platform=str(kivy_platform or ""), reason="android_bridge_ok")
            except Exception as exc:
                self._bridge = None
                self._bridge_error = f"{exc.__class__.__name__}: {exc}"
                ads_log(
                    "provider bridge unavailable",
                    provider=self._provider_name,
                    platform=str(kivy_platform or ""),
                    reason="android_bridge_import_fail",
                    detail=self._bridge_error,
                )
        else:
            self._bridge_error = "non_android_platform"

    def is_bridge_available(self) -> bool:
        """EN: Return whether the Android bridge is available for real AdMob operations.
        RU: ???????, ???????? ?? Android bridge ??? ???????? ???????? AdMob.
        """

        return self._bridge is not None

    def get_bridge_error(self) -> str:
        """EN: Return the last bridge availability error, if any.
        RU: ??????? ????????? ?????? ??????????? bridge, ???? ??? ????.
        """

        return str(self._bridge_error or "")

    def attach_banner(self, slot_widget, placement: AdsPlacementConfig) -> None:
        """EN: Initialize Mobile Ads and show a real native banner over the existing Kivy slot.
        RU: Инициализировать Mobile Ads и показать реальный нативный баннер поверх существующего Kivy-слота.
        """

        if self._bridge is not None:
            ads_log(
                "banner attach request",
                placement=placement.name,
                provider=self._provider_name,
                detail=f"unit_id={placement.unit_id or '-'}",
            )
            self._bridge.initialize(self._admob_app_id)
            ads_log(
                "mobileads init status",
                provider=self._provider_name,
                detail=self._bridge.get_last_init_detail() or ("initialized" if self._bridge.is_initialized() else "unknown"),
            )
            self._bridge.attach_banner(slot_widget, placement.unit_id)
            Clock.schedule_once(
                lambda *_: ads_log(
                    "banner attach result",
                    placement=placement.name,
                    provider=self._provider_name,
                    detail=self._bridge.get_last_banner_detail() or "requested",
                ),
                0.75,
            )
            return
        ads_log(
            "banner provider unavailable",
            placement=placement.name,
            provider=self._provider_name,
            detail=self._bridge_error or "ANDROID_BRIDGE_UNAVAILABLE",
        )

    def detach_banner(self, slot_widget) -> None:
        """EN: Hide the native banner on Android without touching Kivy widget geometry.
        RU: Скрыть нативный баннер на Android, не трогая геометрию Kivy-виджета.
        """

        del slot_widget
        if self._bridge is not None:
            self._bridge.detach_banner()
            ads_log("banner detached", placement="topbar_banner", provider=self._provider_name)
            return
        ads_log(
            "banner detach skip",
            placement="topbar_banner",
            provider=self._provider_name,
            detail=self._bridge_error or "ANDROID_BRIDGE_UNAVAILABLE",
        )

    def show_rewarded(
        self,
        placement: AdsPlacementConfig,
        on_result: Callable[[RewardedResult], None],
        *,
        flow_id: str = "",
        screen: str = "Unknown",
        user_id: int = 0,
    ) -> None:
        """EN: Load and show rewarded on Android, granting reward only when AdMob reports earned.
        RU: Загружать и показывать rewarded на Android, выдавая награду только когда AdMob сообщает earned.
        """

        if self._rewarded_poll_ev is not None:
            self._rewarded_poll_ev.cancel()
            self._rewarded_poll_ev = None
        if self._bridge is None:
            ads_log(
                "rewarded provider unavailable",
                flow_id=flow_id,
                placement=placement.name,
                screen=screen,
                user_id=user_id,
                provider=self._provider_name,
                debug=False,
                detail=self._bridge_error or "ANDROID_BRIDGE_UNAVAILABLE",
            )
            on_result(
                RewardedResult(
                    reward_granted=False,
                    placement=placement.name,
                    provider=self._provider_name,
                    message=self._bridge_error or "ANDROID_BRIDGE_UNAVAILABLE",
                    debug=False,
                    flow_id=flow_id,
                )
            )
            return

        ads_log(
            "rewarded provider show",
            flow_id=flow_id,
            placement=placement.name,
            screen=screen,
            user_id=user_id,
            provider=self._provider_name,
            debug=False,
            detail=f"unit_id={placement.unit_id or '-'}",
        )
        self._bridge.initialize(self._admob_app_id)
        ads_log(
            "mobileads init status",
            provider=self._provider_name,
            detail=self._bridge.get_last_init_detail() or ("initialized" if self._bridge.is_initialized() else "unknown"),
        )
        self._bridge.load_rewarded(placement.unit_id)
        self._rewarded_load_deadline = time.monotonic() + 15.0

        def _finish_result(granted: bool, detail: str) -> None:
            if self._rewarded_poll_ev is not None:
                self._rewarded_poll_ev.cancel()
                self._rewarded_poll_ev = None
            on_result(
                RewardedResult(
                    reward_granted=bool(granted),
                    placement=placement.name,
                    provider=self._provider_name,
                    message=str(detail or ""),
                    debug=False,
                    flow_id=flow_id,
                )
            )

        def _poll_finished(_dt: float) -> bool:
            if not self._bridge.is_rewarded_finished():
                return True
            earned = bool(self._bridge.consume_rewarded_earned())
            detail = str(self._bridge.get_last_rewarded_detail() or "")
            ads_log(
                "rewarded finish state",
                flow_id=flow_id,
                placement=placement.name,
                screen=screen,
                user_id=user_id,
                provider=self._provider_name,
                granted=earned,
                detail=detail or "-",
            )
            if earned:
                _finish_result(True, "")
            else:
                _finish_result(False, "??????? ???????" if detail in {"closed", "not_loaded"} else (detail or "??????? ???????"))
            return False

        def _poll_loaded(_dt: float) -> bool:
            detail = str(self._bridge.get_last_rewarded_detail() or "")
            if detail == "loaded":
                ads_log(
                    "rewarded loaded",
                    flow_id=flow_id,
                    placement=placement.name,
                    screen=screen,
                    user_id=user_id,
                    provider=self._provider_name,
                )
                self._bridge.show_rewarded()
                ads_log(
                    "rewarded show native",
                    flow_id=flow_id,
                    placement=placement.name,
                    screen=screen,
                    user_id=user_id,
                    provider=self._provider_name,
                )
                if self._rewarded_poll_ev is not None:
                    self._rewarded_poll_ev.cancel()
                self._rewarded_poll_ev = Clock.schedule_interval(_poll_finished, 0.25)
                return False
            if detail.startswith("load_failed") or detail == "not_loaded":
                _finish_result(False, detail or "??????? ??????????")
                return False
            if time.monotonic() >= self._rewarded_load_deadline:
                _finish_result(False, detail or "rewarded_load_timeout")
                return False
            return True

        self._rewarded_poll_ev = Clock.schedule_interval(_poll_loaded, 0.25)


AdMobProvider = AdMobAdsProvider
