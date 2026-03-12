"""EN: UI-facing ads manager that owns config, provider choice, banner attach, and rewarded flow.
RU: UI-ориентированный ads manager, который владеет конфигом, выбором провайдера, attach баннера и rewarded-flow.
"""

from __future__ import annotations

import time
from typing import Callable

from manager.ads import ads_backend
from manager.ads.ads_types import AdsConfig, AdsEvent, AdsPlacementConfig, BannerState, RewardedResult, ads_log
from manager.ads.providers.dummy import DummyAdProvider

_BANNER_PLACEMENT = "topbar_banner"
_REWARDED_GAMEOVER_PLACEMENT = "rewarded_gameover"


class _AdsManager:
    """EN: Stateful ads manager singleton used by UI without exposing provider internals.
    RU: Состоянийный singleton ads manager, используемый UI без раскрытия внутренних деталей провайдера.
    """

    def __init__(self) -> None:
        """EN: Initialize empty ads manager state before first runtime init call.
        RU: Инициализировать пустое состояние ads manager до первого runtime-вызова init.
        """

        self._initialized = False
        self._config: AdsConfig | None = None
        self._provider = DummyAdProvider("dummy")
        self._banner_slot = None
        self._banner_attached = False

    def init(self) -> None:
        """EN: Initialize ads subsystem, fetch config when possible, and select current provider stub.
        RU: Инициализировать ads-подсистему, запросить конфиг при возможности и выбрать текущий provider-stub.
        """

        ads_log("init start")
        self._config = ads_backend.fetch_config()
        provider_name = self._config.provider if self._config is not None else "dummy"
        self._provider = DummyAdProvider(provider_name)
        self._initialized = True
        ads_log("init ok", provider=provider_name, configured=bool(self._config))

    def get_banner_state(self) -> BannerState:
        """EN: Return current banner placement state for UI diagnostics and attach decisions.
        RU: Вернуть текущее состояние banner-плейсмента для диагностики UI и решений об attach.
        """

        placement = None
        if self._config is not None:
            placement = self._config.placements.get(_BANNER_PLACEMENT)
        return BannerState(
            enabled=bool(placement and placement.enabled and placement.unit_id),
            provider=self._config.provider if self._config is not None else "dummy",
            placement=_BANNER_PLACEMENT,
            unit_id=placement.unit_id if placement is not None else "",
            attached=bool(self._banner_attached),
        )

    def attach_banner(self, slot_widget) -> None:
        """EN: Attach compatible banner slot without changing geometry; keep placeholder on disabled/error/stub.
        RU: Подключить совместимый banner-slot без изменения геометрии; оставить placeholder при disabled/error/stub.
        """

        if not self._initialized:
            self.init()
        self._banner_slot = slot_widget
        self._banner_attached = True
        banner_state = self.get_banner_state()
        if banner_state.enabled and slot_widget is not None and self._config is not None:
            self._provider.attach_banner(slot_widget, self._config.placements[_BANNER_PLACEMENT])
        ads_log("banner attach", enabled=banner_state.enabled, provider=banner_state.provider)
        self._post_event("banner_attach", _BANNER_PLACEMENT, {"enabled": banner_state.enabled})

    def detach_banner(self) -> None:
        """EN: Detach current banner slot and provider resources while preserving placeholder fallback content.
        RU: Отсоединить текущий banner-slot и ресурсы провайдера, сохранив fallback-placeholder-контент.
        """

        if self._banner_slot is not None:
            self._provider.detach_banner(self._banner_slot)
        self._banner_slot = None
        self._banner_attached = False
        ads_log("banner detach")
        self._post_event("banner_detach", _BANNER_PLACEMENT, {})

    def show_rewarded(
        self,
        context: str = "gameover",
        on_result_callback: Callable[[RewardedResult], None] | None = None,
    ) -> None:
        """EN: Run rewarded flow for requested context and return result into provided callback.
        RU: Запустить rewarded-flow для запрошенного контекста и вернуть результат в переданный callback.
        """

        if not self._initialized:
            self.init()
        placement_name = _REWARDED_GAMEOVER_PLACEMENT if str(context) == "gameover" else str(context)
        placement = self._config.placements.get(placement_name) if self._config is not None else None
        ads_log("rewarded request", context=context, placement=placement_name)
        if placement is None and self._config is None:
            placement = AdsPlacementConfig(
                name=placement_name,
                enabled=True,
                unit_id="DUMMY_REWARDED_DEBUG",
                cooldown_sec=0,
                reward_type="life",
                reward_amount=1,
            )
        if placement is None or not placement.enabled or not placement.unit_id:
            result = RewardedResult(
                reward_granted=False,
                placement=placement_name,
                provider=self._config.provider if self._config is not None else "dummy",
                message="Реклама недоступна",
                debug=False,
            )
            ads_log("rewarded result", granted=False, placement=placement_name, reason="disabled")
            self._post_event("rewarded_unavailable", placement_name, {"context": str(context)})
            if on_result_callback is not None:
                on_result_callback(result)
            return
        ads_log(
            "rewarded show",
            provider=self._config.provider if self._config is not None else "dummy",
            placement=placement_name,
        )
        self._post_event("rewarded_show", placement_name, {"context": str(context)})

        def _handle_result(result: RewardedResult) -> None:
            ads_log(
                "rewarded result",
                granted=result.reward_granted,
                placement=result.placement,
                provider=result.provider,
                debug=result.debug,
            )
            self._post_event(
                "rewarded_result",
                result.placement,
                {"reward_granted": bool(result.reward_granted), "debug": bool(result.debug)},
            )
            if on_result_callback is not None:
                on_result_callback(result)

        self._provider.show_rewarded(placement, _handle_result)

    def _post_event(self, event_name: str, placement: str, extra: dict[str, object]) -> None:
        """EN: Post non-fatal ads event to backend using current cached user identity when available.
        RU: Отправить нефатальное ads-событие в backend, используя текущую кэшированную identity пользователя при наличии.
        """

        ads_backend.post_event(
            AdsEvent(
                user_id=ads_backend.current_user_id(),
                provider=self._config.provider if self._config is not None else "dummy",
                placement=str(placement),
                event=str(event_name),
                ts=int(time.time()),
                extra=dict(extra or {}),
            )
        )


class AdsManager:
    """EN: Static facade exposing the only client ads entrypoints allowed for UI code.
    RU: Статический фасад, экспортирующий единственные клиентские точки входа ads, разрешенные для UI-кода.
    """

    _manager = _AdsManager()

    @classmethod
    def init(cls) -> None:
        """EN: Initialize ads manager singleton.
        RU: Инициализировать singleton ads manager.
        """

        cls._manager.init()

    @classmethod
    def get_banner_state(cls) -> BannerState:
        """EN: Return current banner state snapshot.
        RU: Вернуть текущий snapshot состояния баннера.
        """

        return cls._manager.get_banner_state()

    @classmethod
    def attach_banner(cls, slot_widget) -> None:
        """EN: Attach banner to provided slot widget.
        RU: Подключить баннер к переданному slot-виджету.
        """

        cls._manager.attach_banner(slot_widget)

    @classmethod
    def detach_banner(cls) -> None:
        """EN: Detach banner from currently active slot widget.
        RU: Отсоединить баннер от текущего активного slot-виджета.
        """

        cls._manager.detach_banner()

    @classmethod
    def show_rewarded(
        cls,
        context: str = "gameover",
        on_result_callback: Callable[[RewardedResult], None] | None = None,
    ) -> None:
        """EN: Show rewarded flow for specified UI context.
        RU: Показать rewarded-flow для указанного UI-контекста.
        """

        cls._manager.show_rewarded(context=context, on_result_callback=on_result_callback)
