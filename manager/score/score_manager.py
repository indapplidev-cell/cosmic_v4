# -*- coding: utf-8 -*-
"""
Score manager that forwards updates to the score widget.

EN: Thin adapter for score display updates.
RU: Тонкий адаптер для обновления отображения счёта.
"""

from manager.score.score_widget import ScoreLabel


class ScoreManager:
    """
    Manage score updates for the HUD.

    EN: Delegates score changes to the label.
    RU: Делегирует изменения счёта в лейбл.
    """

    def __init__(self, label: ScoreLabel) -> None:
        """
        Store the score label reference.

        EN: Keeps a label instance for future updates.
        RU: Хранит экземпляр лейбла для последующих обновлений.
        """
        self._label = label

    def set_score(self, score: int) -> None:
        """
        Update the displayed score.

        EN: Forwards the score to the label.
        RU: Передаёт счёт в лейбл.
        """
        self._label.set_score(score)

    def reset(self) -> None:
        """
        Reset score to zero.

        EN: Forces the label to show SCORE: 0.
        RU: Принудительно показывает SCORE: 0.
        """
        self.set_score(0)
