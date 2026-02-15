# -*- coding: utf-8 -*-
"""
Visual-only lives indicator widget for the HUD.

EN: Renders a row of KivyMD icons based on max_lives and lives_left.
RU: Рисует ряд иконок KivyMD на основе max_lives и lives_left.
"""

from __future__ import annotations

from kivy.properties import NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.label import MDIcon

from manager.life import life_style


class LivesIndicator(BoxLayout):
    """
    Visual-only lives indicator (icons) for HUD.

    EN: Builds icon widgets without touching game logic or attempts state.
    RU: Формирует иконки без изменения игровой логики или попыток.
    """

    max_lives = NumericProperty(3)
    lives_left = NumericProperty(3)

    def __init__(self, **kwargs) -> None:
        """
        Initialize the indicator layout sizing and orientation.

        EN: Sets fixed size to allow accurate centering inside the host.
        RU: Задаёт фиксированный размер для корректного центрирования внутри контейнера.
        """
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint = (None, None)
        self.width = life_style.HUD_LIVES_WIDTH
        self.height = life_style.HUD_LIVES_HEIGHT
        self.spacing = life_style.HUD_LIVES_ICON_SPACING
        pad_y = max((life_style.HUD_LIVES_HEIGHT - life_style.HUD_LIVES_FONT) / 2, 0)
        self.padding = (0, pad_y, 0, pad_y)

    def on_kv_post(self, *_args) -> None:
        """
        Initialize icons after KV rules are applied.

        EN: Triggers a rebuild once the widget tree is ready.
        RU: Запускает пересборку после готовности дерева виджетов.
        """
        self.set_lives(self.lives_left, self.max_lives)

    def set_lives(self, lives_left: int, max_lives: int | None = None) -> None:
        """
        Update lives and optionally the max lives.

        EN: Stores values and rebuilds the icon row.
        RU: Сохраняет значения и пересобирает ряд иконок.
        """
        if max_lives is not None:
            self.max_lives = int(max_lives)
        self.lives_left = int(lives_left)
        self._rebuild()

    def on_max_lives(self, *_args) -> None:
        """
        Rebuild icons when max_lives changes.

        EN: Keeps the icon count in sync with max_lives.
        RU: Синхронизирует количество иконок с max_lives.
        """
        self._rebuild()

    def on_lives_left(self, *_args) -> None:
        """
        Rebuild icons when lives_left changes.

        EN: Updates filled/empty icons as lives change.
        RU: Обновляет заполненные/пустые иконки при изменении lives_left.
        """
        self._rebuild()

    def _rebuild(self) -> None:
        """
        Rebuild the icon row for the current lives state.

        EN: Adds a spacer then filled/empty icons aligned to the right.
        RU: Добавляет спейсер и заполненные/пустые иконки с выравниванием вправо.
        """
        left = max(0, min(int(self.lives_left), int(self.max_lives)))
        max_l = max(0, int(self.max_lives))

        self.clear_widgets()
        self.spacing = life_style.HUD_LIVES_ICON_SPACING
        self.width = (max_l * life_style.HUD_LIVES_FONT) + (max(max_l - 1, 0) * self.spacing)

        for index in range(max_l):
            is_full = index < left
            icon = "heart" if is_full else "heart-outline"
            self.add_widget(
                MDIcon(
                    icon=icon,
                    font_size=life_style.HUD_LIVES_FONT,
                    size_hint=(None, None),
                    width=life_style.HUD_LIVES_FONT,
                    height=life_style.HUD_LIVES_FONT,
                )
            )
