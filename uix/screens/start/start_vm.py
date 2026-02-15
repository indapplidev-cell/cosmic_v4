"""EN: View-model data for the start screen texts.
RU: Данные view-model для текстов стартового экрана.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class StartScreenVM:
    """EN: Text container for the start screen.
    RU: Контейнер текстов для стартового экрана.
    """

    title: str
    game_text: str
    profile_text: str
    settings_text: str
