"""EN: View-model data for the profile screen texts.
RU: Данные view-model для текстов экрана профиля.
"""

from dataclasses import dataclass


@dataclass(slots=True)
class ProfileScreenVM:
    """EN: Text container for the profile screen.
    RU: Контейнер текстов для экрана профиля.
    """

    title: str
    back_text: str
    payout_text: str
    login_text: str
