# --- logging bootstrap (must be before any kivy/kivymd imports) ---
from kivy.config import Config

Config.set("kivy", "log_level", "info")
# ---------------------------------------------------------------

import logging
from pathlib import Path

"""EN: Application entry point for the KivyMD app. Starts the app only.
RU: Точка входа для приложения KivyMD. Только запуск приложения.
"""

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import BooleanProperty, StringProperty
from kivymd.app import MDApp

from manager import app_focus_tracker
from manager.ads import AdsManager
from manager.trace import TraceManager, trace_log
from manager.tg_debug_log import tglog
from uix.debug.debug_borders import enable_debug_borders
from uix.debug.debug_config import DEBUG_UI_BORDERS
from uix.screens.routes import LOAD_APP
from uix.window_config import apply_window_config
from uix.screens.builders.auth_builder import build_auth_flow
from uix.screens.root_view import RootView
from uix.screens.screen_manager import AppScreenManager

# Pillow (PIL) не должен шуметь в DEBUG
logging.getLogger("PIL").setLevel(logging.WARNING)


class CosmicApp(MDApp):
    """EN: MDApp that provides the root view.
    RU: MDApp, который предоставляет корневое представление.
    """

    is_logged_in = BooleanProperty(False)
    user_email = StringProperty("")

    def build(self) -> RootView:
        """EN: Build and return the root view.
        RU: Создать и вернуть корневое представление.
        """
        apply_window_config()
        self.title = "Escape to Mars"
        Window.title = "Escape to Mars"
        TraceManager.instance()
        trace_log("SESSION", "APP_BUILD_START")
        enable_debug_borders(DEBUG_UI_BORDERS)
        self.theme_cls.theme_style = "Dark"
        manager = AppScreenManager()
        self._manager = manager
        root = Path(__file__).resolve().parent
        Builder.load_file(str(root / "ads" / "banner" / "banner_slot.kv"))
        AdsManager.init(app=self)
        build_auth_flow(manager)
        manager.go(LOAD_APP, push_history=False)
        Window.bind(on_focus=self._on_window_focus)
        trace_log("SESSION", "APP_BUILD_DONE")
        return RootView(manager)

    def on_start(self) -> None:
        """EN: Apply Android runtime orientation hint after app start.
        RU: Применить подсказку ориентации для Android после запуска приложения.
        """
        from kivy.utils import platform as kivy_platform
        trace_log("SESSION", "APP_START", platform=kivy_platform)

        if kivy_platform == "android":
            try:
                from android_tools.orientation import force_landscape

                force_landscape()
            except Exception:
                pass
            Clock.schedule_once(lambda _dt: Window.release_all_keyboards(), 0)
        elif kivy_platform == "ios":
            Clock.schedule_once(lambda _dt: Window.release_all_keyboards(), 0)

    def on_pause(self) -> bool:
        """EN: Track blur on mobile pause and keep app state.
        RU: Отслеживать blur при mobile pause и сохранять состояние приложения.
        """

        ts = app_focus_tracker.mark_blur()
        tglog(f"[TGDBG] focus blur via on_pause ts={ts}")
        trace_log("SESSION", "APP_PAUSE", ts=ts)
        return True

    def on_resume(self) -> None:
        """EN: Track focus on mobile resume.
        RU: Отслеживать фокус при возврате приложения на mobile.
        """

        ts = app_focus_tracker.mark_focus()
        tglog(f"[TGDBG] focus focus via on_resume ts={ts}")
        trace_log("SESSION", "APP_RESUME", ts=ts)

    def _on_window_focus(self, _window, focused: bool) -> None:
        """EN: Track desktop focus/blur transitions from window events.
        RU: Отслеживать desktop focus/blur по событиям окна.
        """

        if focused:
            ts = app_focus_tracker.mark_focus()
        else:
            ts = app_focus_tracker.mark_blur()
        tglog(f"[TGDBG] focus desktop focus={bool(focused)} ts={ts}")
        trace_log("SESSION", "WINDOW_FOCUS", focused=bool(focused), ts=ts)

    def set_logged_in(self, email: str) -> None:
        """EN: Mark user as logged in and store email.
        RU: Отметить пользователя как авторизованного и сохранить email.
        """
        email_value = (email or "").strip()
        if not email_value:
            return
        self.user_email = email_value
        self.is_logged_in = True

    def logout(self) -> None:
        """EN: Reset login state and clear stored email.
        RU: Сбросить состояние входа и очистить email.
        """
        self.user_email = ""
        self.is_logged_in = False

    def change_screen(self, name: str) -> None:
        """EN: Navigate to the screen by route name.
        RU: Перейти на экран по имени маршрута.
        """
        manager = getattr(self, "_manager", None)
        if manager:
            manager.go(name)


if __name__ == "__main__":
    CosmicApp().run()
