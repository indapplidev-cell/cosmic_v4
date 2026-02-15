"""EN: View-model data for profile change screen texts.
RU: Данные view-model для текстов экрана редактирования профиля.
"""

from kivy.event import EventDispatcher
from kivy.properties import StringProperty


class ProfileChangeVM(EventDispatcher):
    """EN: Text container for the profile change screen.
    RU: Контейнер текстов для экрана редактирования профиля.
    """

    title = StringProperty("")
    field_login = StringProperty("")
    field_email = StringProperty("")
    field_phone = StringProperty("")
    field_tg = StringProperty("")
    field_password = StringProperty("")
    btn_ok = StringProperty("")
    btn_delete = StringProperty("")
    btn_back = StringProperty("")
