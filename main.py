# --- logging bootstrap (must be before any kivy/kivymd imports) ---
from kivy.config import Config

Config.set("kivy", "log_level", "info")
# ---------------------------------------------------------------

import logging
from pathlib import Path

"""EN: Application entry point for the KivyMD app. Starts the app only.
RU: РўРѕС‡РєР° РІС…РѕРґР° РґР»СЏ РїСЂРёР»РѕР¶РµРЅРёСЏ KivyMD. РўРѕР»СЊРєРѕ Р·Р°РїСѓСЃРє РїСЂРёР»РѕР¶РµРЅРёСЏ.
"""

from kivy.lang import Builder
from kivy.properties import BooleanProperty, StringProperty
from kivymd.app import MDApp

from uix.debug.debug_borders import enable_debug_borders
from uix.debug.debug_config import DEBUG_UI_BORDERS
from uix.screens.routes import LOAD_APP
from uix.window_config import apply_window_config
from uix.screens.builders.auth_builder import build_auth_flow
from uix.screens.root_view import RootView
from uix.screens.screen_manager import AppScreenManager

# Pillow (PIL) РЅРµ РґРѕР»Р¶РµРЅ С€СѓРјРµС‚СЊ РІ DEBUG
logging.getLogger("PIL").setLevel(logging.WARNING)


class CosmicApp(MDApp):
    """EN: MDApp that provides the root view.
    RU: MDApp, РєРѕС‚РѕСЂС‹Р№ РїСЂРµРґРѕСЃС‚Р°РІР»СЏРµС‚ РєРѕСЂРЅРµРІРѕРµ РїСЂРµРґСЃС‚Р°РІР»РµРЅРёРµ.
    """

    is_logged_in = BooleanProperty(False)
    user_email = StringProperty("")

    def build(self) -> RootView:
        """EN: Build and return the root view.
        RU: РЎРѕР·РґР°С‚СЊ Рё РІРµСЂРЅСѓС‚СЊ РєРѕСЂРЅРµРІРѕРµ РїСЂРµРґСЃС‚Р°РІР»РµРЅРёРµ.
        """
        apply_window_config()
        enable_debug_borders(DEBUG_UI_BORDERS)
        self.theme_cls.theme_style = "Dark"
        manager = AppScreenManager()
        self._manager = manager
        root = Path(__file__).resolve().parent
        Builder.load_file(str(root / "ads" / "banner" / "banner_slot.kv"))
        build_auth_flow(manager)
        manager.go(LOAD_APP, push_history=False)
        return RootView(manager)

    def on_start(self) -> None:
        """EN: Apply Android runtime orientation hint after app start.
        RU: Применить подсказку ориентации для Android после запуска приложения.
        """
        from kivy.utils import platform as kivy_platform

        if kivy_platform == "android":
            try:
                from android_tools.orientation import force_landscape

                force_landscape()
            except Exception:
                pass

    def set_logged_in(self, email: str) -> None:
        """EN: Mark user as logged in and store email.
        RU: РћС‚РјРµС‚РёС‚СЊ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ РєР°Рє Р°РІС‚РѕСЂРёР·РѕРІР°РЅРЅРѕРіРѕ Рё СЃРѕС…СЂР°РЅРёС‚СЊ email.
        """
        email_value = (email or "").strip()
        if not email_value:
            return
        self.user_email = email_value
        self.is_logged_in = True

    def logout(self) -> None:
        """EN: Reset login state and clear stored email.
        RU: РЎР±СЂРѕСЃРёС‚СЊ СЃРѕСЃС‚РѕСЏРЅРёРµ РІС…РѕРґР° Рё РѕС‡РёСЃС‚РёС‚СЊ email.
        """
        self.user_email = ""
        self.is_logged_in = False

    def change_screen(self, name: str) -> None:
        """EN: Navigate to the screen by route name.
        RU: РџРµСЂРµР№С‚Рё РЅР° СЌРєСЂР°РЅ РїРѕ РёРјРµРЅРё РјР°СЂС€СЂСѓС‚Р°.
        """
        manager = getattr(self, "_manager", None)
        if manager:
            manager.go(name)
 

if __name__ == "__main__":
    CosmicApp().run()

