# -*- coding: utf-8 -*-
"""
Score label widget for displaying the current score value.

EN: Lightweight label that formats the score as plain text.
RU: Лёгкий лейбл, который форматирует счёт как обычный текст.
"""

from kivy.properties import NumericProperty, StringProperty
from kivymd.uix.label import MDLabel


class ScoreLabel(MDLabel):
    """
    Display-only score label with centered vertical alignment.

    EN: Updates its text when the score changes.
    RU: Обновляет текст при изменении счёта.
    """

    score_value = NumericProperty(0)
    score_text = StringProperty("SCORE: 0")

    def on_kv_post(self, *_args) -> None:
        """
        Initialize label alignment and text sizing.

        EN: Ensures valign works by syncing text_size with widget size.
        RU: Обеспечивает работу valign синхронизацией text_size с размером виджета.
        """
        self.size_hint = (None, None)
        self.halign = "left"
        self.valign = "middle"
        self.max_lines = 1
        self.shorten = True
        self.shorten_from = "right"
        self.text_size = (None, self.height)
        self.bind(height=self._sync_text_size)
        self.text = self.score_text
        self._sync_text_size()

    def _sync_text_size(self, *_args) -> None:
        """
        Sync text_size to enable vertical alignment.

        EN: Keeps text_size equal to widget size.
        RU: Держит text_size равным размеру виджета.
        """
        self.text_size = (None, self.height)

    def set_score(self, value: int) -> None:
        """
        Update score value and label text.

        EN: Formats score as 'SCORE: N'.
        RU: Форматирует счёт как 'SCORE: N'.
        """
        self.score_value = int(value)
        self.score_text = f"SCORE: {self.score_value}"
        self.text = self.score_text
        self._sync_text_size()
