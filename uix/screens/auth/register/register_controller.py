"""EN: Controller for register actions and callbacks.
RU: Контроллер для действий регистрации и колбэков экрана регистрации.
"""

from typing import Callable, Optional


class RegisterController:
    """EN: Dispatch-only controller for register screen.
    RU: Контроллер только для диспетчеризации экрана регистрации.
    """

    def __init__(
        self,
        on_create: Optional[Callable[[], None]] = None,
        on_to_login: Optional[Callable[[], None]] = None,
    ) -> None:
        """EN: Store callbacks for UI actions.
        RU: Сохранить колбэки для действий UI.
        """
        self._on_create = on_create
        self._on_to_login = on_to_login

    def create(self) -> None:
        """EN: Dispatch create-account action.
        RU: Диспетчеризовать создание аккаунта.
        """
        if self._on_create:
            self._on_create()

    def to_login(self) -> None:
        """EN: Dispatch navigation to login.
        RU: Диспетчеризовать переход на вход.
        """
        if self._on_to_login:
            self._on_to_login()
