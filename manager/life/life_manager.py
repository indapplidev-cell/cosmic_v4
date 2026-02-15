# -*- coding: utf-8 -*-
"""
Lives manager that syncs attempts state with the lives indicator.

EN: Delegates storage to a session manager and display to the indicator.
RU: Делегирует хранение менеджеру сессии, а отображение индикатору.
"""

from manager.life.attempts_session import GameSessionManager, LossOutcome
from manager.life.lives_indicator import LivesIndicator


class LifeManager:
    """
    Keep attempts state in sync with the HUD indicator.

    EN: Reads attempts from the session and updates the indicator.
    RU: Читает попытки из сессии и обновляет индикатор.
    """

    def __init__(self, session: GameSessionManager, indicator: LivesIndicator) -> None:
        """
        Store session manager and lives indicator references.

        EN: Keeps dependencies required to sync attempts and UI.
        RU: Хранит зависимости для синхронизации попыток и UI.
        """
        self._session = session
        self._indicator = indicator

    def sync(self) -> None:
        """
        Push current attempts state into the indicator.

        EN: Reads attempts from the session manager and updates the indicator.
        RU: Читает попытки из менеджера сессии и обновляет индикатор.
        """
        self._indicator.set_lives(
            self._session.get_attempts_left(),
            self._session.get_max_attempts(),
        )

    def reset(self) -> None:
        """
        Reset attempts to max and sync indicator.

        EN: Resets session attempts and refreshes the UI indicator.
        RU: Сбрасывает попытки сессии и обновляет UI-индикатор.
        """
        self._session.reset()
        self.sync()

    def reset_to_full(self) -> None:
        """
        Reset attempts and ensure full red hearts.

        EN: Resets session attempts and refreshes the indicator.
        RU: Сбрасывает попытки сессии и обновляет индикатор.
        """
        self._session.reset()
        self.sync()

    def register_loss(self) -> LossOutcome:
        """
        Register a loss, update attempts, and sync indicator.

        EN: Returns the loss outcome after updating attempts and UI.
        RU: Возвращает исход потери после обновления попыток и UI.
        """
        outcome = self._session.register_loss()
        self.sync()
        return outcome
