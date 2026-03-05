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
        self._backspace_bound = False

    def on_kv_post(self, _base_widget) -> None:
        """EN: Bind mobile key handler once after widget tree is ready.
        RU: Один раз привязать обработчик мобильных клавиш после готовности дерева виджетов.
        """
        if self._backspace_bound:
            return
        if kivy_platform in ("android", "ios"):
            Window.bind(on_key_down=self._on_window_key_down)
            self._backspace_bound = True

    def _on_window_key_down(self, _window, key, _scancode, _codepoint, _modifiers):
        """EN: Normalize mobile backspace/delete for focused text inputs.
        RU: Нормализовать backspace/delete мобильной клавиатуры для активных текстовых полей.
        """
        if kivy_platform not in ("android", "ios"):
            return False
        if key not in (8, 67, 112, 127):
            return False

        focused = getattr(Window, "keyboard_focused", None)
        if not isinstance(focused, TextInput):
            return False

        mode = "bkspc" if key in (8, 67) else "del"
        focused.do_backspace(mode=mode)
        return True

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
