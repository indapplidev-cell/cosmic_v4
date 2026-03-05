"""EN: Root view container for the screen manager.
RU: Корневой контейнер для менеджера экранов.
"""

from kivy.core.window import Window
from kivy.uix.textinput import TextInput
from kivy.utils import platform as kivy_platform
from kivymd.uix.screen import MDScreen

from .screen_manager import AppScreenManager


class RootView(MDScreen):
    """EN: Root screen that only hosts the screen manager.
    RU: Корневой экран, который размещает менеджер экранов.
    """

    def __init__(self, manager: AppScreenManager, **kwargs) -> None:
        """EN: Attach the provided screen manager.
        RU: Подключить переданный менеджер экранов.
        """
        super().__init__(**kwargs)
        self.add_widget(manager)

    def on_touch_down(self, touch):
        """EN: Hide mobile keyboard when user taps outside focused input.
        RU: Скрыть мобильную клавиатуру при тапе вне сфокусированного поля.
        """
        if kivy_platform in ("android", "ios"):
            focused = getattr(Window, "keyboard_focused", None)
            if isinstance(focused, TextInput) and not focused.collide_point(*touch.pos):
                focused.focus = False
                try:
                    Window.release_all_keyboards()
                except Exception:
                    pass
        return super().on_touch_down(touch)
