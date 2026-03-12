"""EN: Abstract provider contract for banner and rewarded ads operations.
RU: Абстрактный контракт провайдера для операций banner и rewarded ads.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

from manager.ads.ads_types import AdsPlacementConfig, RewardedResult


class AdProvider(ABC):
    """EN: Provider interface consumed by `AdsManager` regardless of underlying SDK.
    RU: Интерфейс провайдера, который использует `AdsManager` независимо от базового SDK.
    """

    @abstractmethod
    def attach_banner(self, slot_widget, placement: AdsPlacementConfig) -> None:
        """EN: Attach banner content to the compatible slot widget.
        RU: Подключить содержимое баннера к совместимому slot-виджету.
        """

    @abstractmethod
    def detach_banner(self, slot_widget) -> None:
        """EN: Detach previously attached banner content from the slot widget.
        RU: Отсоединить ранее подключенное содержимое баннера от slot-виджета.
        """

    @abstractmethod
    def show_rewarded(
        self,
        placement: AdsPlacementConfig,
        on_result: Callable[[RewardedResult], None],
    ) -> None:
        """EN: Show rewarded flow and eventually return result into the UI callback.
        RU: Показать rewarded-flow и затем вернуть результат в UI callback.
        """
