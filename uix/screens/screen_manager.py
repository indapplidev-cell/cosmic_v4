"""EN: Screen manager for registering screens and navigation.
RU: РњРµРЅРµРґР¶РµСЂ СЌРєСЂР°РЅРѕРІ РґР»СЏ СЂРµРіРёСЃС‚СЂР°С†РёРё Рё РЅР°РІРёРіР°С†РёРё.
"""

from __future__ import annotations

from kivy.logger import Logger
from kivy.uix.screenmanager import NoTransition
from kivymd.uix.screenmanager import MDScreenManager
from manager.ads import AdsManager
from manager.lang.lang_manager import t
from manager.screen_tracker import ScreenTracker, normalize_screen_name

_BANNER_ALLOWED_SCREENS = {"Start", "Settings", "Profile", "Edit", "Game"}
_USER_INFO_SCREENS = {"start", "profile", "profile_change", "settings", "game"}
_TITLE_KEYS = {
    "login": "shell.title.login",
    "register": "shell.title.register",
    "password_reset": "shell.title.password_reset",
    "start": "shell.title.start",
    "profile": "shell.title.profile",
    "profile_change": "shell.title.profile_change",
    "settings": "shell.title.settings",
    "game": "shell.title.game",
}


def _widget_name(widget) -> str:
    """EN: Return a safe class name for a mounted widget or weak proxy.
    RU: Р’РµСЂРЅСѓС‚СЊ Р±РµР·РѕРїР°СЃРЅРѕРµ РёРјСЏ РєР»Р°СЃСЃР° РґР»СЏ СЃРјРѕРЅС‚РёСЂРѕРІР°РЅРЅРѕРіРѕ РІРёРґР¶РµС‚Р° РёР»Рё weak proxy.
    """
    if widget is None:
        return "None"
    try:
        target = getattr(widget, "__self__", widget)
        return target.__class__.__name__
    except ReferenceError:
        return "DeadWeakProxy"


class AppScreenManager(MDScreenManager):
    """EN: Minimal screen manager with register and go methods.
    RU: РњРёРЅРёРјР°Р»СЊРЅС‹Р№ РјРµРЅРµРґР¶РµСЂ СЌРєСЂР°РЅРѕРІ СЃ РјРµС‚РѕРґР°РјРё register Рё go.
    """

    def __init__(self, **kwargs) -> None:
        """EN: Initialize manager with navigation history.
        RU: РРЅРёС†РёР°Р»РёР·РёСЂРѕРІР°С‚СЊ РјРµРЅРµРґР¶РµСЂ СЃ РёСЃС‚РѕСЂРёРµР№ РЅР°РІРёРіР°С†РёРё.
        """
        super().__init__(**kwargs)
        self.transition = NoTransition()
        self._history: list[str] = []
        self._shell = None

    def register(self, screen) -> None:
        """EN: Register a screen instance.
        RU: Р—Р°СЂРµРіРёСЃС‚СЂРёСЂРѕРІР°С‚СЊ СЌРєР·РµРјРїР»СЏСЂ СЌРєСЂР°РЅР°.
        """
        self.add_widget(screen)

    def attach_shell(self, shell) -> None:
        """EN: Attach the shared shell used to present cross-screen UI chrome.
        RU: РџРѕРґРєР»СЋС‡РёС‚СЊ РѕР±С‰РёР№ shell, РєРѕС‚РѕСЂС‹Р№ РїРѕРєР°Р·С‹РІР°РµС‚ СЃРєРІРѕР·РЅСѓСЋ UI-РѕР±РІСЏР·РєСѓ РјРµР¶РґСѓ СЌРєСЂР°РЅР°РјРё.
        """
        self._shell = shell

    def go(self, name: str, *, push_history: bool = True) -> None:
        """EN: Switch to the screen by name.
        RU: РџРµСЂРµРєР»СЋС‡РёС‚СЊСЃСЏ РЅР° СЌРєСЂР°РЅ РїРѕ РёРјРµРЅРё.
        """
        prev_name = str(self.current or "")
        if prev_name == str(name):
            return
        prev_screen = ScreenTracker.get_screen()
        screen_name = normalize_screen_name(name)
        changed = ScreenTracker.set_screen(name, reason="ScreenManager")
        if changed:
            print(f"[NAV] route to screen={screen_name} from={prev_screen}", flush=True)
        if push_history and self.current:
            self._history.append(self.current)
        self.current = name
        screen_widget = self.get_screen(name)
        self._present_screen(screen_widget, name)
        slot_widget = self._shell.get_banner_slot() if self._shell is not None else None
        AdsManager.on_screen_change(prev_screen, screen_name, slot_widget=slot_widget)

    def back(self) -> None:
        """EN: Navigate to the previous screen if available.
        RU: РџРµСЂРµР№С‚Рё РЅР° РїСЂРµРґС‹РґСѓС‰РёР№ СЌРєСЂР°РЅ, РµСЃР»Рё РѕРЅ РµСЃС‚СЊ.
        """
        if not self._history:
            return
        prev = self._history.pop()
        self.go(prev, push_history=False)

    def _present_screen(self, screen_widget, route_name: str) -> None:
        """EN: Mount logical screen widgets into the shared shell hosts for the current route.
        RU: РЎРјРѕРЅС‚РёСЂРѕРІР°С‚СЊ РІРёРґР¶РµС‚С‹ Р»РѕРіРёС‡РµСЃРєРѕРіРѕ СЌРєСЂР°РЅР° РІ РѕР±С‰РёРµ host-РѕР±Р»Р°СЃС‚Рё shell РґР»СЏ С‚РµРєСѓС‰РµРіРѕ РјР°СЂС€СЂСѓС‚Р°.
        """
        if self._shell is None:
            return

        route_key = str(route_name or "").strip().lower()
        if route_key == "load_app":
            content_widget = getattr(screen_widget, "get_shell_load_widget", lambda: screen_widget.children[0])()
            self._shell.present_load_screen(content_widget)
            Logger.info(
                "[UI] screen current=%s content_widget=%s children=%s"
                % (
                    route_name,
                    _widget_name(content_widget),
                    len(self._shell.ids.content_host.children),
                )
            )
            return

        title_key = _TITLE_KEYS.get(route_key, "")
        background_widget = getattr(screen_widget, "get_shell_background_widget", lambda: None)()
        content_widget = getattr(screen_widget, "get_shell_content_widget", lambda: None)()
        bottom_widget = getattr(screen_widget, "get_shell_bottom_widget", lambda: None)()

        self._shell.set_background_widget(background_widget)
        self._shell.set_title(t(title_key) if title_key else "")
        self._shell.refresh_user_info()
        self._shell.set_top_left_widget(None)
        self._shell.set_top_right_widget(None)
        self._shell.set_user_info_visible(route_key in _USER_INFO_SCREENS)
        self._shell.set_content_widget(content_widget)
        self._shell.set_bottom_widget(bottom_widget)
        self._shell.set_ads_visible(normalize_screen_name(route_name) in _BANNER_ALLOWED_SCREENS)
        self._shell.set_bar_visibility(top=True, content=True, bottom=True)

        Logger.info(
            "[UI] screen current=%s content_widget=%s bottom_widget=%s content_children=%s bottom_children=%s"
            % (
                route_name,
                _widget_name(content_widget),
                _widget_name(bottom_widget),
                len(self._shell.ids.content_host.children),
                len(self._shell.ids.bottom_host.children),
            )
        )

        on_shell_present = getattr(screen_widget, "on_shell_present", None)
        if callable(on_shell_present):
            on_shell_present(self._shell)
