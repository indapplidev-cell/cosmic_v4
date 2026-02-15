"""EN: Controller for game screen actions and callbacks.
RU: Контроллер для действий экрана игры и колбэков.
"""

from typing import Callable, Optional


class GameScreenController:
    """EN: Dispatch-only controller for the game screen.
    RU: Контроллер только для диспетчеризации экрана игры.
    """

    def __init__(
        self,
        on_show_hud: Optional[Callable[[], None]] = None,
        on_hide_hud: Optional[Callable[[], None]] = None,
        on_back: Optional[Callable[[], None]] = None,
    ) -> None:
        """EN: Store callbacks for UI actions.
        RU: Сохранить колбэки для действий UI.
        """
        self._on_show_hud = on_show_hud
        self._on_hide_hud = on_hide_hud
        self._on_back = on_back

    def show_hud(self) -> None:
        """EN: Dispatch HUD show action.
        RU: Диспетчеризовать показ HUD.
        """
        if self._on_show_hud:
            self._on_show_hud()

    def hide_hud(self) -> None:
        """EN: Dispatch HUD hide action.
        RU: Диспетчеризовать скрытие HUD.
        """
        if self._on_hide_hud:
            self._on_hide_hud()

    def back(self) -> None:
        """EN: Dispatch back navigation action.
        RU: Диспетчеризовать действие назад.
        """
        if self._on_back:
            self._on_back()
