"""EN: Root view container for the screen manager.
RU: Контейнер корневого представления для менеджера экранов.
"""

from kivymd.uix.screen import MDScreen

from .screen_manager import AppScreenManager


class RootView(MDScreen):
    """EN: Root screen that only hosts the screen manager.
    RU: Корневой экран, который только размещает менеджер экранов.
    """

    def __init__(self, manager: AppScreenManager, **kwargs) -> None:
        """EN: Attach the provided screen manager.
        RU: Подключить переданный менеджер экранов.
        """
        super().__init__(**kwargs)
        self.add_widget(manager)
