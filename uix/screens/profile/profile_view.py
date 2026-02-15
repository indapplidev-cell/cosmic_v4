"""EN: View for the profile screen.
RU: Представление экрана профиля.
"""

from pathlib import Path

from data.gameplay.record_storage import RecordStorage
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivymd.uix.screen import MDScreen
from manager.lang.lang_manager import t
from uix.debug.debug_borders import apply_debug_borders_to_ids
from uix.screens.common.button_text_style import apply_button_text_style, caps

from .profile_controller import ProfileScreenController
from .profile_layout import PROFILE_DEBUG_IDS, apply_profile_layout
from .profile_vm import ProfileScreenVM

KV_PATH = Path(__file__).with_name("profile.kv")
Builder.load_file(str(KV_PATH))


class ProfileScreenView(MDScreen):
    """EN: Profile screen view that wires layout, VM, and controller.
    RU: Представление профиля, связывающее раскладку, VM и контроллер.
    """

    best_score_text = StringProperty("0")
    rating_text = StringProperty("0")
    balance_text = StringProperty("0")
    login_text = StringProperty(t("common.no_data"))
    phone_text = StringProperty(t("common.no_data"))
    tg_text = StringProperty(t("common.no_data"))

    def on_pre_enter(self, *args):
        """EN: Refresh profile data before showing the screen.
        RU: Обновить данные профиля перед показом экрана.
        """
        if hasattr(self, "vm"):
            self.ids.profile_top_left_title.text = self.vm.title
        self.controller.refresh_profile_cards(self)
        return super().on_pre_enter(*args)

    def on_kv_post(self, base_widget) -> None:
        """EN: Apply layout after KV is ready.
        RU: Применить раскладку после загрузки KV.
        """
        apply_profile_layout(self)
        apply_button_text_style(
            self,
            [
                self.ids.back_label,
                self.ids.payout_label,
                self.ids.login_label,
            ],
        )
        apply_debug_borders_to_ids(self, PROFILE_DEBUG_IDS)

    def configure(self, vm: ProfileScreenVM, controller: ProfileScreenController) -> None:
        """EN: Configure texts and bind callbacks.
        RU: Настроить тексты и привязать колбэки.
        """
        self.vm = vm
        self.controller = controller
        self.ids.back_label.text = caps(vm.back_text)
        self.ids.payout_label.text = caps(vm.payout_text)
        self.ids.login_label.text = caps(vm.login_text)

        self.ids.back_btn.on_release = controller.back
        self.ids.payout_btn.on_release = controller.payout
        self.ids.login_btn.on_release = controller.login
        self.best_score_text = str(RecordStorage().get_best_score())
