"""EN: Screen manager for registering screens and navigation.
RU: Менеджер экранов для регистрации и навигации.
"""

from kivymd.uix.screenmanager import MDScreenManager


class AppScreenManager(MDScreenManager):
    """EN: Minimal screen manager with register and go methods.
    RU: Минимальный менеджер экранов с методами register и go.
    """

    def __init__(self, **kwargs) -> None:
        """EN: Initialize manager with navigation history.
        RU: Инициализировать менеджер с историей навигации.
        """
        super().__init__(**kwargs)
        self._history: list[str] = []

    def register(self, screen) -> None:
        """EN: Register a screen instance.
        RU: Зарегистрировать экземпляр экрана.
        """
        self.add_widget(screen)

    def go(self, name: str, *, push_history: bool = True) -> None:
        """EN: Switch to the screen by name.
        RU: Переключиться на экран по имени.
        """
        if push_history and self.current:
            self._history.append(self.current)
        self.current = name

    def back(self) -> None:
        """EN: Navigate to the previous screen if available.
        RU: Перейти на предыдущий экран, если он есть.
        """
        if not self._history:
            return
        prev = self._history.pop()
        self.go(prev, push_history=False)
