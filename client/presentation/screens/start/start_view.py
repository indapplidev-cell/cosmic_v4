"""EN: View for the start screen.
RU: Р СџРЎР‚Р ВµР Т‘РЎРѓРЎвЂљР В°Р Р†Р В»Р ВµР Р…Р С‘Р Вµ РЎРѓРЎвЂљР В°РЎР‚РЎвЂљР С•Р Р†Р С•Р С–Р С• РЎРЊР С”РЎР‚Р В°Р Р…Р В°.
"""

from pathlib import Path
from threading import Thread

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.utils import get_color_from_hex
from kivymd.uix.screen import MDScreen
from client.gameplay.debug.gameplay_trace_flags import ENABLE_UI_SHELL_TRACE
from client.infrastructure.branding.remote_logo_loader import resolve_header_logo_source

from client.presentation.debug.debug_borders import apply_debug_borders_to_ids
from client.presentation.common.button_text_style import apply_button_text_style, caps
from client.presentation.themes import main_screen_theme as main_theme

from .start_controller import StartScreenController
from .start_layout import START_DEBUG_IDS, apply_start_layout
from .start_vm import StartScreenVM

KV_PATH = Path(__file__).with_name("start.kv")
Builder.load_file(str(KV_PATH))


class StartScreenView(MDScreen):
    """EN: Start screen view that wires layout, VM, and controller.
    RU: Р СџРЎР‚Р ВµР Т‘РЎРѓРЎвЂљР В°Р Р†Р В»Р ВµР Р…Р С‘Р Вµ РЎРѓРЎвЂљР В°РЎР‚РЎвЂљР В°, РЎРѓР Р†РЎРЏР В·РЎвЂ№Р Р†Р В°РЎР‹РЎвЂ°Р ВµР Вµ РЎР‚Р В°РЎРѓР С”Р В»Р В°Р Т‘Р С”РЎС“, VM Р С‘ Р С”Р С•Р Р…РЎвЂљРЎР‚Р С•Р В»Р В»Р ВµРЎР‚.
    """

    def on_kv_post(self, base_widget) -> None:
        """EN: Apply layout after KV is ready.
        RU: Р СџРЎР‚Р С‘Р СР ВµР Р…Р С‘РЎвЂљРЎРЉ РЎР‚Р В°РЎРѓР С”Р В»Р В°Р Т‘Р С”РЎС“ Р С—Р С•РЎРѓР В»Р Вµ Р В·Р В°Р С–РЎР‚РЎС“Р В·Р С”Р С‘ KV.
        """
        if ENABLE_UI_SHELL_TRACE:
            Logger.info("[UI] apply_layout screen=Start before main_layout=%s" % self.ids.get("main_layout"))
        apply_start_layout(self)
        if ENABLE_UI_SHELL_TRACE:
            Logger.info("[UI] apply_layout screen=Start after main_layout=%s" % self.ids.get("main_layout"))
        self._home_card_widget = self._strong_widget(self.ids.home_card)
        self._home_card_text_widget = self._strong_widget(self.ids.home_card_text)
        self._home_card_logo_widget = self._strong_widget(self.ids.home_card_logo)
        self._info_card_widget = self._strong_widget(self.ids.info_card)
        self._info_card_text_widget = self._strong_widget(self.ids.info_card_text)
        self._title_lbl_widget = self._strong_widget(self.ids.title_lbl)
        self._game_btn_text_widget = self._strong_widget(self.ids.game_btn_text)
        self._game_btn_icon_widget = self._strong_widget(self.ids.game_btn_icon)
        self._profile_btn_text_widget = self._strong_widget(self.ids.profile_btn_text)
        self._settings_btn_text_widget = self._strong_widget(self.ids.settings_btn_text)
        self._home_card_logo_source = ""
        self._home_card_logo_attempted = False
        apply_button_text_style(
            self,
            [
                self._game_btn_text_widget,
                self._profile_btn_text_widget,
                self._settings_btn_text_widget,
            ],
        )
        self._apply_main_screen_style()
        apply_debug_borders_to_ids(self, START_DEBUG_IDS)
        self._ids_keepalive = dict(self.ids)
        for _key, _widget in self._ids_keepalive.items():
            self.ids[_key] = _widget
        self._contentbar_widget = getattr(self.ids.contentbar, "__self__", self.ids.contentbar)
        self._bottombar_widget = getattr(self.ids.bottombar, "__self__", self.ids.bottombar)
        self._background_widget = getattr(self.ids.start_background, "__self__", self.ids.start_background)

    def configure(self, vm: StartScreenVM, controller: StartScreenController) -> None:
        """EN: Configure texts and bind callbacks.
        RU: Р СњР В°РЎРѓРЎвЂљРЎР‚Р С•Р С‘РЎвЂљРЎРЉ РЎвЂљР ВµР С”РЎРѓРЎвЂљРЎвЂ№ Р С‘ Р С—РЎР‚Р С‘Р Р†РЎРЏР В·Р В°РЎвЂљРЎРЉ Р С”Р С•Р В»Р В±РЎРЊР С”Р С‘.
        """
        self.ids.title_lbl.text = vm.title
        self.ids.game_btn_text.text = caps(vm.game_text)
        self.ids.profile_btn_text.text = caps(vm.profile_text)
        self.ids.settings_btn_text.text = caps(vm.settings_text)
        self._apply_main_screen_style()

        self._game_callback = lambda *_: controller.game()
        self._profile_callback = lambda *_: controller.profile()
        self._settings_callback = lambda *_: controller.settings()
        self.ids.game_btn.unbind(on_release=self._game_callback)
        self.ids.game_btn.bind(on_release=self._game_callback)
        self.ids.profile_btn.unbind(on_release=self._profile_callback)
        self.ids.profile_btn.bind(on_release=self._profile_callback)
        self.ids.settings_btn.unbind(on_release=self._settings_callback)
        self.ids.settings_btn.bind(on_release=self._settings_callback)

    def _apply_main_screen_style(self) -> None:
        """Apply centralized start-screen color tokens to KivyMD widgets."""

        ids = self.ids
        text_colors = (
            (self._cached_widget("_title_lbl_widget", "title_lbl"), main_theme.TEXT_MAIN),
            (self._cached_widget("_game_btn_text_widget", "game_btn_text"), "#FFFFFF"),
            (self._cached_widget("_game_btn_icon_widget", "game_btn_icon"), "#FFFFFF"),
            (self._cached_widget("_profile_btn_text_widget", "profile_btn_text"), main_theme.TEXT_MAIN),
            (self._cached_widget("_settings_btn_text_widget", "settings_btn_text"), main_theme.TEXT_MAIN),
            (self._cached_widget("_home_card_text_widget", "home_card_text"), main_theme.TEXT_MAIN),
            (self._cached_widget("_info_card_text_widget", "info_card_text"), main_theme.TEXT_SECONDARY),
        )
        for widget, color in text_colors:
            if hasattr(widget, "theme_text_color"):
                widget.theme_text_color = "Custom"
            if hasattr(widget, "text_color"):
                widget.text_color = get_color_from_hex(color)

        if not getattr(self, "_main_button_states_bound", False):
            self._bind_button_colors(
                ids.game_btn,
                normal=main_theme.ACCENT_MARS,
                hover=main_theme.ACCENT_MARS_HOVER,
                pressed=main_theme.ACCENT_MARS_PRESSED,
            )
            for btn in (ids.profile_btn, ids.settings_btn):
                self._bind_button_colors(
                    btn,
                    normal=main_theme.SURFACE,
                    hover=main_theme.SURFACE_ALT,
                    pressed=main_theme.SURFACE_DEEP,
                )
            self._main_button_states_bound = True

    def _bind_button_colors(self, button, *, normal: str, hover: str, pressed: str) -> None:
        """Keep MDButton background states on centralized color tokens."""

        def _sync(*_args) -> None:
            if getattr(button, "state", "normal") == "down":
                color = pressed
            elif bool(getattr(button, "hovering", False) or getattr(button, "state_hover", False)):
                color = hover
            else:
                color = normal
            button.md_bg_color = get_color_from_hex(color)

        button.bind(state=_sync)
        if "hovering" in button.properties():
            button.bind(hovering=_sync)
        if "state_hover" in button.properties():
            button.bind(state_hover=_sync)
        _sync()

    def on_shell_present(self, shell) -> None:
        """Mount start-specific top cards into the shared shell zones."""

        shell.ids.topbar.md_bg_color = get_color_from_hex(main_theme.APPBAR_BG)
        self._home_card_text_widget.text = shell.ids.top_left_title.text
        self._set_home_card_logo_source("")
        self._info_card_text_widget.text = shell.ids.top_right_user.text
        shell.set_top_left_widget(self._home_card_widget)
        shell.set_top_right_widget(self._info_card_widget)
        shell.set_user_info_visible(False)
        self._apply_main_screen_style()
        self._start_home_card_logo_resolve()

    def _start_home_card_logo_resolve(self) -> None:
        """Resolve the start-card logo in the background and update UI on the main thread."""

        if self._home_card_logo_source:
            self._set_home_card_logo_source(self._home_card_logo_source)
            return
        if self._home_card_logo_attempted:
            return
        self._home_card_logo_attempted = True

        def _worker() -> None:
            source = resolve_header_logo_source()
            Clock.schedule_once(lambda _dt: self._apply_resolved_home_card_logo(source), 0)

        Thread(target=_worker, daemon=True).start()

    def _apply_resolved_home_card_logo(self, source: str) -> None:
        """Apply resolved logo source, leaving the fallback text when unavailable."""

        source = str(source or "").strip()
        if not source:
            return
        self._home_card_logo_source = source
        self._set_home_card_logo_source(source)

    def _set_home_card_logo_source(self, source: str) -> None:
        """Toggle between fallback text and the cached local logo source."""

        source = str(source or "").strip()
        if source:
            self._home_card_logo_widget.source = source
            self._home_card_logo_widget.opacity = 1
            self._home_card_logo_widget.reload()
            self._home_card_text_widget.opacity = 0
            return
        self._home_card_logo_widget.opacity = 0
        self._home_card_logo_widget.source = ""
        self._home_card_text_widget.opacity = 1

    @staticmethod
    def _strong_widget(widget):
        """Return the real widget behind a Kivy ids weak proxy."""

        return getattr(widget, "__self__", widget)

    def _cached_widget(self, attr_name: str, id_name: str):
        """Return a cached strong widget, falling back to ids before shell moves it."""

        widget = getattr(self, attr_name, None)
        if widget is not None:
            return widget
        return self._strong_widget(self.ids[id_name])

    def get_shell_content_widget(self):
        """EN: Return the reusable content bar widget for the shared shell host.
        RU: Р’РµСЂРЅСѓС‚СЊ РїРµСЂРµРёСЃРїРѕР»СЊР·СѓРµРјС‹Р№ content bar-РІРёРґР¶РµС‚ РґР»СЏ РѕР±С‰РµРіРѕ host-РєРѕРЅС‚РµР№РЅРµСЂР° shell.
        """

        return self._contentbar_widget

    def get_shell_bottom_widget(self):
        """EN: Return the reusable bottom bar widget for the shared shell host.
        RU: Р’РµСЂРЅСѓС‚СЊ РїРµСЂРµРёСЃРїРѕР»СЊР·СѓРµРјС‹Р№ bottom bar-РІРёРґР¶РµС‚ РґР»СЏ РѕР±С‰РµРіРѕ host-РєРѕРЅС‚РµР№РЅРµСЂР° shell.
        """

        return self._bottombar_widget

    def get_shell_background_widget(self):
        """Return the start-screen dark root background for the shared shell."""

        return self._background_widget


