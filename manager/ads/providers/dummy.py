"""EN: Dummy provider used on desktop and current Android stub builds without SDK.
RU: Dummy-провайдер для desktop и текущих Android stub-сборок без SDK.
"""

from __future__ import annotations

from typing import Callable

from kivy.clock import Clock

from ads.rewarded.rewarded_modal import RewardedAdModal
from manager.ads.ads_types import AdsPlacementConfig, RewardedResult, ads_log
from manager.ads.providers.base import BaseAdsProvider


class DummyAdProvider(BaseAdsProvider):
    """EN: Non-SDK provider that preserves placeholder banner and rewarded modal flow.
    RU: Провайдер без SDK, сохраняющий placeholder-баннер и rewarded modal flow.
    """

    def __init__(self, provider_name: str) -> None:
        """EN: Store logical provider name used only for logs and callbacks.
        RU: Сохранить логическое имя провайдера, используемое только в логах и callback.
        """

        self._provider_name = str(provider_name or "dummy")
        self._rewarded_modal: RewardedAdModal | None = None
        self._rewarded_finish_ev = None
        self._rewarded_completed = False

    def attach_banner(self, slot_widget, placement: AdsPlacementConfig) -> None:
        """EN: Keep existing slot placeholder without changing size or layout.
        RU: Оставить существующий placeholder слота без изменения размера или layout.
        """

        del slot_widget
        ads_log("banner provider attach noop", placement=placement.name, provider=self._provider_name)

    def detach_banner(self, slot_widget) -> None:
        """EN: Release dummy banner state without touching the slot widget geometry.
        RU: Освободить состояние dummy-баннера, не трогая геометрию slot-виджета.
        """

        del slot_widget
        ads_log("banner provider detach noop", placement="topbar_banner", provider=self._provider_name)

    def show_rewarded(
        self,
        placement: AdsPlacementConfig,
        on_result: Callable[[RewardedResult], None],
        *,
        flow_id: str = "",
        screen: str = "Unknown",
        user_id: int = 0,
    ) -> None:
        """EN: Show rewarded modal, deny reward on close, and grant only on timer completion.
        RU: Показать rewarded modal, не выдавать награду при закрытии и выдавать только по завершению таймера.
        """

        ads_log(
            "rewarded provider show",
            flow_id=flow_id,
            placement=placement.name,
            screen=screen,
            user_id=user_id,
            provider=self._provider_name,
            debug=False,
        )
        self._rewarded_completed = False

        def _handle_close() -> None:
            if self._rewarded_completed:
                return
            if self._rewarded_finish_ev is not None:
                self._rewarded_finish_ev.cancel()
                self._rewarded_finish_ev = None
            self._rewarded_modal = None
            on_result(
                RewardedResult(
                    reward_granted=False,
                    placement=placement.name,
                    provider=self._provider_name,
                    message="Реклама закрыта",
                    debug=False,
                    flow_id=flow_id,
                )
            )

        modal = RewardedAdModal(on_close=_handle_close)
        self._rewarded_modal = modal
        modal.open()

        def _finish(_dt: float) -> None:
            self._rewarded_finish_ev = None
            self._rewarded_completed = True
            current_modal = self._rewarded_modal
            if current_modal is not None and getattr(current_modal, "parent", None) is not None:
                current_modal.dismiss()
            self._rewarded_modal = None
            on_result(
                RewardedResult(
                    reward_granted=True,
                    placement=placement.name,
                    provider=self._provider_name,
                    message="",
                    debug=False,
                    flow_id=flow_id,
                )
            )

        self._rewarded_finish_ev = Clock.schedule_once(_finish, 10)


DummyAdsProvider = DummyAdProvider
