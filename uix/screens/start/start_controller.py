"""EN: Controller for start screen actions and callbacks.
RU: Контроллер для действий стартового экрана и колбэков.
"""

from typing import Callable, Optional


class StartScreenController:
    """EN: Dispatch-only controller for the start screen.
    RU: Контроллер только для диспетчеризации стартового экрана.
    """

    def __init__(
        self,
        on_game: Optional[Callable[[], None]] = None,
        on_profile: Optional[Callable[[], None]] = None,
        on_settings: Optional[Callable[[], None]] = None,
    ) -> None:
        """EN: Store callbacks for UI actions.
        RU: Сохранить колбэки для действий UI.
        """
        self._on_game = on_game
        self._on_profile = on_profile
        self._on_settings = on_settings

    def game(self) -> None:
        """EN: Dispatch game action.
        RU: Диспетчеризовать действие игры.
        """
        if self._on_game:
            self._on_game()

    def profile(self) -> None:
        """EN: Dispatch profile action.
        RU: Диспетчеризовать действие профиля.
        """
        if self._on_profile:
            self._on_profile()

    def settings(self) -> None:
        """EN: Dispatch settings action.
        RU: Диспетчеризовать действие настроек.
        """
        if self._on_settings:
            self._on_settings()
