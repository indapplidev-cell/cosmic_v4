"""EN: Dummy provider used on desktop and current Android stub builds without SDK.
RU: Dummy-провайдер для desktop и текущих Android stub-сборок без SDK.
"""

from __future__ import annotations

from typing import Callable

from kivy.clock import Clock

from ads.rewarded.rewarded_modal import RewardedAdModal
from manager.ads.ads_types import AdsPlacementConfig, RewardedResult, ads_log
from manager.ads.providers.base import AdProvider


class DummyAdProvider(AdProvider):
    """EN: Non-SDK provider that preserves UI flow with placeholder banner and debug rewarded result.
    RU: Провайдер без SDK, сохраняющий UI-flow с placeholder-баннером и debug-результатом rewarded.
    """

    def __init__(self, provider_name: str) -> None:
        """EN: Store logical mediation provider name used only for logs and callbacks.
        RU: Сохранить логическое имя mediation-провайдера, используемое только для логов и callback.
        """

        self._provider_name = str(provider_name or "dummy")
        self._rewarded_modal: RewardedAdModal | None = None
        self._rewarded_finish_ev = None
        self._rewarded_completed = False

    def attach_banner(self, slot_widget, placement: AdsPlacementConfig) -> None:
        """EN: Keep slot placeholder unchanged because dummy provider renders no real banner.
        RU: Оставить placeholder слота без изменений, потому что dummy-провайдер не рисует реальный баннер.
        """

        del slot_widget, placement
        ads_log("banner provider attach noop", provider=self._provider_name)

    def detach_banner(self, slot_widget) -> None:
        """EN: Release dummy banner state without touching slot geometry or placeholder content.
        RU: Освободить состояние dummy-баннера, не трогая геометрию слота и placeholder-контент.
        """

        del slot_widget
        ads_log("banner provider detach noop", provider=self._provider_name)

    def show_rewarded(
        self,
        placement: AdsPlacementConfig,
        on_result: Callable[[RewardedResult], None],
    ) -> None:
        """EN: Show rewarded popup, grant reward only after timer completion, and deny reward on early close.
        RU: Показать rewarded-popup, выдавать награду только после завершения таймера и не выдавать при раннем закрытии.
        """

        ads_log("rewarded provider show", provider=self._provider_name, placement=placement.name)
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
                )
            )

        self._rewarded_finish_ev = Clock.schedule_once(_finish, 10)
