"""EN: View-model data for the settings screen texts.
RU: Данные view-model для текстов экрана настроек.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SettingsScreenVM:
    """EN: Text container for the settings screen.
    RU: Контейнер текстов для экрана настроек.
    """

    title: str
    back_text: str
    login_text: str
    action_text: str
