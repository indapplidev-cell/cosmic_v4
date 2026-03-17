"""EN: UI-facing ads manager that owns config, runtime provider choice, banner lifecycle, and rewarded flow.
RU: UI-ориентированный ads manager, который владеет конфигом, выбором runtime-провайдера, жизненным циклом баннера и rewarded-flow.
"""

from __future__ import annotations

import time
from typing import Callable

from kivy.utils import platform as kivy_platform

from manager.ads import ads_backend
from manager.ads.ads_types import (
    AdsConfig,
    AdsEvent,
    AdsPlacementConfig,
    BannerState,
    RewardedResult,
    ads_log,
    generate_flow_id,
    get_current_screen_name,
)
from manager.ads.providers.admob import AdMobAdsProvider
from manager.ads.providers.dummy import DummyAdProvider
from manager.session_manager import get_session_user_id

_BANNER_PLACEMENT = "topbar_banner"
_REWARDED_PLACEMENT = "rewarded_gameover"
_ALLOWED_BANNER_SCREENS = {"Start", "Profile", "Edit", "Settings", "Game"}
_SCREEN_DEBOUNCE_SEC = 0.25


class _AdsManager:
    """EN: Stateful ads manager singleton used by UI without exposing provider internals.
    RU: Состоянийный singleton ads manager, используемый UI без раскрытия внутренних деталей провайдера.
    """

    def __init__(self) -> None:
        """EN: Initialize empty manager state before the first runtime init.
        RU: Инициализировать пустое состояние manager до первого runtime-init.
        """

        self._initialized = False
        self._config: AdsConfig | None = None
        self._provider = DummyAdProvider("dummy")
        self._runtime_provider_name = "dummy"
        self._current_screen = "Unknown"
        self._last_screen = "Unknown"
        self._last_screen_ts = 0.0
        self._banner_slot = None
        self._banner_attached = False
        self._banner_attached_screen: str | None = None
        self._last_action_ts = 0.0
        self._last_action = ""
        self._pending_action_id = 0

    def init(self, app=None) -> None:
        """EN: Initialize ads subsystem on app start and fetch server-driven mediation config.
        RU: Инициализировать ads-подсистему на старте приложения и получить server-driven конфиг медиации.
        """

        del app
        if self._initialized:
            return
        ads_log("init start", screen=get_current_screen_name(), user_id=ads_backend.current_user_id())
        self._config = ads_backend.fetch_config()
        self._provider = self._select_runtime_provider(self._config)
        self._initialized = True
        if self._config is not None:
            ads_log(
                "config applied",
                screen=get_current_screen_name(),
                user_id=ads_backend.current_user_id(),
                provider=str(self._config.provider or self._runtime_provider_name),
                app_id=str(self._config.admob_app_id or "-"),
                banner_unit_id=str(self._config.banner_ad_unit_id or "-"),
                rewarded_unit_id=str(self._config.rewarded_ad_unit_id or "-"),
            )
        ads_log(
            "init ok",
            screen=get_current_screen_name(),
            user_id=ads_backend.current_user_id(),
            provider=self._runtime_provider_name,
            configured=bool(self._config and self._config.configured),
        )

    def _select_runtime_provider(self, config: AdsConfig | None):
        """EN: Select the runtime provider explicitly by platform and backend config with diagnostic logging.
        RU: ???? ??????? runtime-????????? ?? ????????? ? backend-??????? ? ???????????????? ??????.
        """

        platform_name = str(kivy_platform or "")
        provider_name = str(config.provider if config is not None else "dummy")
        if platform_name != "android":
            self._runtime_provider_name = "dummy"
            ads_log(
                "provider selected",
                provider=self._runtime_provider_name,
                platform=platform_name,
                reason="non_android_platform",
                detail=f"config_provider={provider_name}",
            )
            return DummyAdProvider(provider_name)

        if provider_name == "admob_mediation":
            provider = AdMobAdsProvider(provider_name, admob_app_id=str((config.admob_app_id if config is not None else "") or ""))
            self._runtime_provider_name = "admob_mediation"
            ads_log(
                "provider selected",
                provider=self._runtime_provider_name,
                platform=platform_name,
                reason="android_admob_config",
                detail=(
                    "bridge_available"
                    if provider.is_bridge_available()
                    else f"bridge_unavailable:{provider.get_bridge_error() or 'unknown'}"
                ),
            )
            return provider

        self._runtime_provider_name = "dummy"
        ads_log(
            "provider selected",
            provider=self._runtime_provider_name,
            platform=platform_name,
            reason="unsupported_config_provider",
            detail=f"config_provider={provider_name}",
        )
        return DummyAdProvider(provider_name)

    def _banner_placement(self) -> AdsPlacementConfig:
        """EN: Build normalized banner placement object from current config.
        RU: Собрать нормализованный banner-placement объект из текущего конфига.
        """

        if self._config is None:
            return AdsPlacementConfig(name=_BANNER_PLACEMENT, enabled=False, unit_id="")
        return AdsPlacementConfig(
            name=_BANNER_PLACEMENT,
            enabled=bool(self._config.banner_enabled),
            unit_id=str(self._config.banner_ad_unit_id or ""),
            refresh_sec=int(self._config.refresh_sec or 30),
        )

    def _rewarded_placement(self) -> AdsPlacementConfig:
        """EN: Build normalized rewarded placement object from current config.
        RU: Собрать нормализованный rewarded-placement объект из текущего конфига.
        """

        if self._config is None:
            return AdsPlacementConfig(
                name=_REWARDED_PLACEMENT,
                enabled=True,
                unit_id="DUMMY_REWARDED_DEBUG",
                reward_type="life",
                reward_amount=1,
            )
        return AdsPlacementConfig(
            name=_REWARDED_PLACEMENT,
            enabled=bool(self._config.rewarded_enabled),
            unit_id=str(self._config.rewarded_ad_unit_id or ""),
            reward_type="life",
            reward_amount=1,
        )

    def get_banner_state(self) -> BannerState:
        """EN: Return banner state snapshot for diagnostics and attach decisions.
        RU: Вернуть snapshot состояния баннера для диагностики и решений по attach.
        """

        placement = self._banner_placement()
        return BannerState(
            enabled=bool(placement.enabled and placement.unit_id),
            provider=self._runtime_provider_name,
            placement=placement.name,
            unit_id=placement.unit_id,
            attached=bool(self._banner_attached),
        )

    def on_screen_change(self, exit_screen: str, enter_screen: str, slot_widget=None) -> None:
        """EN: Handle one real screen transition and bind banner logs/events to exit and enter hooks explicitly.
        RU: Обработать один реальный переход экрана и явно привязать banner-логи/ивенты к хукам exit и enter.
        """

        if not self._initialized:
            self.init()
        exit_name = str(exit_screen or "Unknown")
        enter_name = str(enter_screen or "Unknown")
        now = time.monotonic()
        if enter_name == self._last_screen and (now - self._last_screen_ts) < _SCREEN_DEBOUNCE_SEC:
            ads_log(
                "screen_change skip",
                placement=_BANNER_PLACEMENT,
                screen=enter_name,
                user_id=ads_backend.current_user_id(),
                provider=self._runtime_provider_name,
                reason="debounce",
            )
            return
        self._current_screen = enter_name
        self._last_screen = enter_name
        self._last_screen_ts = now

        placement = self._banner_placement()
        should_show_on_enter = bool(enter_name in _ALLOWED_BANNER_SCREENS and placement.enabled and placement.unit_id)
        should_detach_on_exit = bool(
            self._banner_attached
            and self._banner_attached_screen == exit_name
            and not should_show_on_enter
        )

        if exit_name != "Unknown":
            ads_log(
                "[BANNER] on_screen_exit",
                placement=_BANNER_PLACEMENT,
                screen=exit_name,
                user_id=ads_backend.current_user_id(),
                provider=self._runtime_provider_name,
                action="detach" if should_detach_on_exit else "skip",
            )
            self.banner_sync(
                screen=exit_name,
                should_show=False,
                slot_widget=None,
                reason="on_screen_exit",
            )

        ads_log(
            "[BANNER] on_screen_enter",
            placement=_BANNER_PLACEMENT,
            screen=enter_name,
            user_id=ads_backend.current_user_id(),
            provider=self._runtime_provider_name,
            action="attach" if should_show_on_enter else "skip",
        )
        self.banner_sync(
            screen=enter_name,
            should_show=enter_name in _ALLOWED_BANNER_SCREENS,
            slot_widget=slot_widget,
            reason="on_screen_enter",
        )

    def banner_sync(self, screen: str, should_show: bool, slot_widget=None, *, reason: str) -> None:
        """EN: Idempotently synchronize banner attach/detach state for one screen transition.
        RU: Идемпотентно синхронизировать состояние attach/detach баннера для одного screen transition.
        """

        if not self._initialized:
            self.init()
        self._pending_action_id += 1
        current_action_id = self._pending_action_id
        now = time.monotonic()
        screen_name = str(screen or "Unknown")
        self._current_screen = screen_name
        placement = self._banner_placement()
        desired_show = bool(should_show and placement.enabled and placement.unit_id)
        ads_log(
            "banner_sync",
            placement=_BANNER_PLACEMENT,
            screen=screen_name,
            user_id=ads_backend.current_user_id(),
            provider=self._runtime_provider_name,
            should_show=int(desired_show),
            attached=int(bool(self._banner_attached)),
            attached_screen=self._banner_attached_screen or "-",
            reason=reason,
        )
        if (
            reason not in {"on_screen_exit", "on_screen_enter"}
            and
            screen_name == str(self._banner_attached_screen or screen_name)
            and (now - self._last_action_ts) < _SCREEN_DEBOUNCE_SEC
            and self._last_action in {"attach", "detach", "skip"}
        ):
            ads_log(
                "banner_skip",
                placement=_BANNER_PLACEMENT,
                screen=screen_name,
                user_id=ads_backend.current_user_id(),
                provider=self._runtime_provider_name,
                reason="debounce",
            )
            self._last_action = "skip"
            return
        if desired_show:
            if self._banner_attached and self._banner_attached_screen == screen_name:
                ads_log(
                    "banner_skip",
                    placement=_BANNER_PLACEMENT,
                    screen=screen_name,
                    user_id=ads_backend.current_user_id(),
                    provider=self._runtime_provider_name,
                    reason="already_attached",
                )
                self._last_action = "skip"
                return
            if self._banner_attached and slot_widget is not None and slot_widget is self._banner_slot:
                self._banner_attached_screen = screen_name
                ads_log(
                    "banner_skip",
                    placement=_BANNER_PLACEMENT,
                    screen=screen_name,
                    user_id=ads_backend.current_user_id(),
                    provider=self._runtime_provider_name,
                    reason="shared_slot_reuse",
                )
                self._last_action = "skip"
                return
            if self._banner_attached:
                self._detach_banner_internal(self._banner_attached_screen or screen_name, current_action_id)
            self._attach_banner_internal(screen_name, slot_widget, current_action_id)
            self._last_action_ts = now
            self._last_action = "attach"
            return
        if not self._banner_attached:
            ads_log(
                "banner_skip",
                placement=_BANNER_PLACEMENT,
                screen=screen_name,
                user_id=ads_backend.current_user_id(),
                provider=self._runtime_provider_name,
                reason="already_detached",
            )
            self._last_action = "skip"
            return
        self._detach_banner_internal(self._banner_attached_screen or screen_name, current_action_id)
        self._last_action_ts = now
        self._last_action = "detach"

    def _attach_banner_internal(self, screen: str, slot_widget, action_id: int) -> None:
        """EN: Perform one real banner attach and emit one server event.
        RU: Выполнить один реальный attach баннера и отправить одно server event.
        """

        if action_id != self._pending_action_id:
            ads_log(
                "banner_skip",
                placement=_BANNER_PLACEMENT,
                screen=screen,
                user_id=ads_backend.current_user_id(),
                provider=self._runtime_provider_name,
                reason="outdated_action",
            )
            return
        placement = self._banner_placement()
        self._banner_slot = slot_widget
        self._banner_attached = True
        self._banner_attached_screen = screen
        if slot_widget is not None:
            self._provider.attach_banner(slot_widget, placement)
        ads_log(
            "banner attach",
            placement=_BANNER_PLACEMENT,
            screen=screen,
            user_id=ads_backend.current_user_id(),
            provider=self._runtime_provider_name,
            enabled=bool(placement.enabled and placement.unit_id),
        )
        self._post_event(
            event_name="banner_attach",
            placement=_BANNER_PLACEMENT,
            flow_id=None,
            ok=bool(placement.enabled and placement.unit_id),
            detail=None,
            screen=screen,
            meta={"enabled": bool(placement.enabled and placement.unit_id)},
        )

    def _detach_banner_internal(self, screen: str, action_id: int) -> None:
        """EN: Perform one real banner detach and emit one server event.
        RU: Выполнить один реальный detach баннера и отправить одно server event.
        """

        if action_id != self._pending_action_id:
            ads_log(
                "banner_skip",
                placement=_BANNER_PLACEMENT,
                screen=screen,
                user_id=ads_backend.current_user_id(),
                provider=self._runtime_provider_name,
                reason="outdated_action",
            )
            return
        if self._banner_slot is not None:
            self._provider.detach_banner(self._banner_slot)
        self._banner_slot = None
        self._banner_attached = False
        self._banner_attached_screen = None
        ads_log(
            "banner detach",
            placement=_BANNER_PLACEMENT,
            screen=screen,
            user_id=ads_backend.current_user_id(),
            provider=self._runtime_provider_name,
        )
        self._post_event(
            event_name="banner_detach",
            placement=_BANNER_PLACEMENT,
            flow_id=None,
            ok=True,
            detail=None,
            screen=screen,
            meta={},
        )

    def attach_banner(self, container_widget) -> None:
        """EN: Backward-compatible attach entry routed into banner state sync.
        RU: Backward-compatible точка attach, маршрутизируемая в banner state sync.
        """

        screen = get_current_screen_name()
        self.banner_sync(
            screen=screen,
            should_show=screen in _ALLOWED_BANNER_SCREENS,
            slot_widget=container_widget,
            reason="manual_attach",
        )

    def detach_banner(self) -> None:
        """EN: Backward-compatible detach entry routed into banner state sync.
        RU: Backward-compatible точка detach, маршрутизируемая в banner state sync.
        """

        self.banner_sync(screen=get_current_screen_name(), should_show=False, slot_widget=None, reason="manual_detach")

    def rewarded_click(
        self,
        placement: str = _REWARDED_PLACEMENT,
        on_result_callback: Callable[[RewardedResult], None] | None = None,
    ) -> None:
        """EN: Start rewarded flow from a user click and emit click->request->show->result logs/events.
        RU: Запустить rewarded-flow от пользовательского клика и выдать логи/события click->request->show->result.
        """

        flow_id = generate_flow_id()
        screen = get_current_screen_name()
        user_id = ads_backend.current_user_id()
        ads_log(
            "rewarded click",
            flow_id=flow_id,
            placement=placement,
            screen=screen,
            user_id=user_id,
            provider=self._runtime_provider_name,
            debug=False,
        )
        self._post_event(
            event_name="rewarded_click",
            placement=placement,
            flow_id=flow_id,
            ok=True,
            detail=None,
            screen=screen,
            meta={},
        )
        self.show_rewarded(
            context="gameover",
            on_result_callback=on_result_callback,
            flow_id=flow_id,
            trigger="click",
        )

    def show_rewarded(
        self,
        context: str = "gameover",
        on_result_callback: Callable[[RewardedResult], None] | None = None,
        *,
        flow_id: str | None = None,
        trigger: str = "unknown",
    ) -> None:
        """EN: Execute rewarded request/show/result flow using current runtime provider.
        RU: Выполнить rewarded request/show/result flow через текущий runtime-провайдер.
        """

        if not self._initialized:
            self.init()
        placement_name = _REWARDED_PLACEMENT if str(context) == "gameover" else str(context)
        placement = self._rewarded_placement()
        current_flow_id = str(flow_id or generate_flow_id())
        current_screen = get_current_screen_name()
        current_user_id = ads_backend.current_user_id()
        ads_log(
            "rewarded request",
            flow_id=current_flow_id,
            placement=placement_name,
            screen=current_screen,
            user_id=current_user_id,
            provider=self._runtime_provider_name,
            debug=bool(self._config.debug) if self._config is not None else False,
            trigger=str(trigger or "unknown"),
        )
        self._post_event(
            event_name="rewarded_request",
            placement=placement_name,
            flow_id=current_flow_id,
            ok=True,
            detail=None,
            screen=current_screen,
            meta={"trigger": str(trigger or "unknown"), "context": str(context)},
        )
        if not placement.enabled or not placement.unit_id:
            result = RewardedResult(
                reward_granted=False,
                placement=placement_name,
                provider=self._runtime_provider_name,
                message="Реклама недоступна",
                debug=False,
                flow_id=current_flow_id,
            )
            ads_log(
                "rewarded result",
                flow_id=current_flow_id,
                placement=placement_name,
                screen=current_screen,
                user_id=current_user_id,
                provider=self._runtime_provider_name,
                debug=False,
                granted=False,
                detail=result.message,
            )
            self._post_event(
                event_name="rewarded_result",
                placement=placement_name,
                flow_id=current_flow_id,
                ok=False,
                detail=result.message,
                screen=current_screen,
                meta={"trigger": str(trigger or "unknown"), "context": str(context)},
            )
            if on_result_callback is not None:
                on_result_callback(result)
            return
        ads_log(
            "rewarded show",
            flow_id=current_flow_id,
            placement=placement_name,
            screen=current_screen,
            user_id=current_user_id,
            provider=self._runtime_provider_name,
            debug=bool(self._config.debug) if self._config is not None else False,
        )
        self._post_event(
            event_name="rewarded_show",
            placement=placement_name,
            flow_id=current_flow_id,
            ok=True,
            detail=None,
            screen=current_screen,
            meta={"trigger": str(trigger or "unknown"), "context": str(context)},
        )

        def _handle_result(result: RewardedResult) -> None:
            result.flow_id = current_flow_id
            ads_log(
                "rewarded result",
                flow_id=current_flow_id,
                placement=result.placement,
                screen=get_current_screen_name(),
                user_id=ads_backend.current_user_id(),
                provider=result.provider,
                debug=result.debug,
                granted=result.reward_granted,
                detail=str(result.message or "-"),
            )
            self._post_event(
                event_name="rewarded_result",
                placement=result.placement,
                flow_id=current_flow_id,
                ok=bool(result.reward_granted),
                detail=str(result.message or ""),
                screen=get_current_screen_name(),
                meta={"trigger": str(trigger or "unknown"), "context": str(context)},
            )
            if on_result_callback is not None:
                on_result_callback(result)

        self._provider.show_rewarded(
            placement,
            _handle_result,
            flow_id=current_flow_id,
            screen=current_screen,
            user_id=current_user_id,
        )

    def _post_event(
        self,
        *,
        event_name: str,
        placement: str,
        flow_id: str | None,
        ok: bool | None,
        detail: str | None,
        screen: str,
        meta: dict[str, object],
    ) -> None:
        """EN: Post one non-fatal ads event to backend using the current authenticated user id.
        RU: Отправить одно нефатальное ads-событие в backend, используя текущий user id аутентифицированной сессии.
        """

        ads_backend.post_event(
            AdsEvent(
                user_id=int(get_session_user_id()),
                provider=self._runtime_provider_name,
                placement=str(placement),
                event=str(event_name),
                screen=str(screen or get_current_screen_name()),
                flow_id=str(flow_id or "") or None,
                ok=ok,
                detail=detail,
                ts_client=time.time(),
                meta=dict(meta or {}),
            )
        )


class AdsManager:
    """EN: Static facade exposing the only UI entrypoints for the client ads layer.
    RU: Статический фасад, экспортирующий единственные UI-точки входа клиентского ads-слоя.
    """

    _manager = _AdsManager()

    @classmethod
    def init(cls, app=None) -> None:
        """EN: Initialize the shared ads manager.
        RU: Инициализировать общий ads manager.
        """

        cls._manager.init(app=app)

    @classmethod
    def get_banner_state(cls) -> BannerState:
        """EN: Return current banner state snapshot.
        RU: Вернуть текущий snapshot состояния баннера.
        """

        return cls._manager.get_banner_state()

    @classmethod
    def on_screen_change(cls, exit_screen: str, enter_screen: str, slot_widget=None) -> None:
        """EN: Notify ads layer about a real screen transition with explicit exit and enter screen names.
        RU: Уведомить ads-слой о реальном переходе экрана с явными именами exit и enter экранов.
        """

        cls._manager.on_screen_change(exit_screen, enter_screen, slot_widget=slot_widget)

    @classmethod
    def banner_sync(cls, screen: str, should_show: bool, slot_widget=None, *, reason: str = "screen_change") -> None:
        """EN: Synchronize banner state for compatibility with the current navigation hook.
        RU: Синхронизировать состояние баннера для совместимости с текущим navigation hook.
        """

        cls._manager.banner_sync(screen=screen, should_show=should_show, slot_widget=slot_widget, reason=reason)

    @classmethod
    def attach_banner(cls, container_widget) -> None:
        """EN: Attach banner content to the provided existing UI container.
        RU: Подключить banner-контент к переданному существующему UI-контейнеру.
        """

        cls._manager.attach_banner(container_widget)

    @classmethod
    def detach_banner(cls) -> None:
        """EN: Detach banner content from the current container.
        RU: Отключить banner-контент от текущего контейнера.
        """

        cls._manager.detach_banner()

    @classmethod
    def rewarded_click(
        cls,
        placement: str = _REWARDED_PLACEMENT,
        on_result_callback: Callable[[RewardedResult], None] | None = None,
    ) -> None:
        """EN: Start rewarded flow from the GameOver button click.
        RU: Запустить rewarded-flow от клика по кнопке GameOver.
        """

        cls._manager.rewarded_click(placement=placement, on_result_callback=on_result_callback)

    @classmethod
    def show_rewarded(
        cls,
        context: str = "gameover",
        on_result_callback: Callable[[RewardedResult], None] | None = None,
        *,
        flow_id: str | None = None,
        trigger: str = "unknown",
    ) -> None:
        """EN: Execute rewarded flow for the specified UI context.
        RU: Выполнить rewarded-flow для указанного UI-контекста.
        """

        cls._manager.show_rewarded(
            context=context,
            on_result_callback=on_result_callback,
            flow_id=flow_id,
            trigger=trigger,
        )
