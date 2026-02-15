"""EN: Controller for login actions and callbacks.
RU: Контроллер для действий входа и колбэков экрана входа.
"""

from typing import Callable, Optional


class LoginController:
    """EN: Dispatch-only controller for login screen.
    RU: Контроллер только для диспетчеризации экрана входа.
    """

    def __init__(
        self,
        on_login: Optional[Callable[[], None]] = None,
        on_forgot: Optional[Callable[[], None]] = None,
        on_register: Optional[Callable[[], None]] = None,
    ) -> None:
        """EN: Store callbacks for UI actions.
        RU: Сохранить колбэки для действий UI.
        """
        self._on_login = on_login
        self._on_forgot = on_forgot
        self._on_register = on_register

    def login(self) -> None:
        """EN: Dispatch login action.
        RU: Диспетчеризовать действие входа.
        """
        if self._on_login:
            self._on_login()

    def forgot(self) -> None:
        """EN: Dispatch forgot-password action.
        RU: Диспетчеризовать действие восстановления пароля.
        """
        if self._on_forgot:
            self._on_forgot()

    def register(self) -> None:
        """EN: Dispatch navigation to register.
        RU: Диспетчеризовать переход на регистрацию.
        """
        if self._on_register:
            self._on_register()
