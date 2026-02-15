"""EN: Controller for settings screen actions and callbacks.
RU: Контроллер для действий экрана настроек и колбэков.
"""

from typing import Callable, Optional

from data.user_cache.user_session import UserSession


class SettingsScreenController:
    """EN: Dispatch-only controller for the settings screen.
    RU: Контроллер только для диспетчеризации экрана настроек.
    """

    def __init__(
        self,
        on_back: Optional[Callable[[], None]] = None,
        on_payout: Optional[Callable[[], None]] = None,
        on_logout: Optional[Callable[[], None]] = None,
        on_action: Optional[Callable[[], None]] = None,
    ) -> None:
        """EN: Store callbacks for UI actions.
        RU: Сохранить колбэки для действий UI.
        """
        self._on_back = on_back
        self._on_payout = on_payout
        self._on_logout = on_logout
        self._on_action = on_action

    def back(self) -> None:
        """EN: Dispatch back action.
        RU: Диспетчеризовать действие назад.
        """
        if self._on_back:
            self._on_back()

    def payout(self) -> None:
        """EN: Dispatch payout action without clearing the session.
        RU: Диспетчеризовать действие выплаты без очистки сессии.
        """
        if self._on_payout:
            self._on_payout()

    def logout(self) -> None:
        """EN: Clear session and dispatch logout action.
        RU: Очистить сессию и диспетчеризовать выход.
        """
        UserSession().clear()
        if self._on_logout:
            self._on_logout()

    def action(self) -> None:
        """EN: Dispatch action button.
        RU: Диспетчеризовать действие кнопки.
        """
        if self._on_action:
            self._on_action()
