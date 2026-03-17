"""EN: Backward-compatible root view alias for the shared application shell.
RU: Обратно совместимый alias корневого view для общего shell приложения.
"""

from kivy.core.window import Window

from uix.shell.app_shell import AppShell


class RootView(AppShell):
    """EN: Backward-compatible root view that now delegates to `AppShell`.
    RU: Обратно совместимый root view, который теперь делегирует в `AppShell`.
    """

    def __init__(self, manager, **kwargs) -> None:
        """EN: Initialize the shared shell and immediately present the already-selected screen.
        RU: Инициализировать общий shell и сразу показать уже выбранный текущий экран.
        """
        super().__init__(manager, **kwargs)
        manager.opacity = 0
        manager.disabled = True
        manager.size_hint = (None, None)
        manager.size = Window.size
        manager.pos = (-10_000, -10_000)
        if manager.current:
            manager._present_screen(manager.get_screen(manager.current), manager.current)
