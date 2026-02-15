"""EN: View-model data for the game screen texts.
RU: Данные view-model для текстов экрана игры.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class GameScreenVM:
    """EN: Text container for the game screen.
    RU: Контейнер текстов для экрана игры.
    """

    title: str
    game_text: str
    back_text: str
