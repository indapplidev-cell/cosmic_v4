"""EN: View for the profile change screen.
RU: Представление экрана редактирования профиля.
"""

from pathlib import Path

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty
from kivymd.uix.screen import MDScreen

from uix.debug.debug_borders import apply_debug_borders_to_ids
from uix.screens.common.button_text_style import apply_button_text_style, caps

from .profile_change_controller import ProfileChangeController
from .profile_change_vm import ProfileChangeVM

KV_PATH = Path(__file__).with_name("profile_change.kv")
Builder.load_file(str(KV_PATH))

DEBUG_WIDGET_IDS = [
    "main_layout",
    "topbar",
    "lefttopbar",
    "midltopbar",
    "righttopbar",
    "contentbar",
    "content_center",
    "profile_change_card",
    "profile_change_left_col",
    "profile_change_right_col",
    "card_login",
    "card_email",
    "card_phone",
    "card_tg",
    "card_password",
    "card_spacer",
    "bottombar",
    "btn_stack",
    "ok_btn",
    "delete_btn",
    "delete_label",
    "back_btn",
]

class ProfileChangeView(MDScreen):
    """EN: Profile change screen view that wires VM and controller.
    RU: Представление редактирования профиля, связывающее VM и контроллер.
    """

    vm = ObjectProperty(None)
    controller = ObjectProperty(None)
    right_text = StringProperty("")

    def on_kv_post(self, base_widget) -> None:
        """EN: Apply layout after KV is ready.
        RU: Применить раскладку после загрузки KV.
        """
        self._apply_layout()
        apply_button_text_style(
            self,
            [self.ids.ok_label, self.ids.delete_label, self.ids.back_label],
        )

    def configure(self, vm: ProfileChangeVM, controller: ProfileChangeController) -> None:
        """EN: Configure texts and bind callbacks.
        RU: Настроить тексты и привязать колбэки.
        """
        self.vm = vm
        self.controller = controller
        self.ids.ok_label.text = caps(vm.btn_ok)
        self.ids.delete_label.text = caps(vm.btn_delete)
        self.ids.back_label.text = caps(vm.btn_back)
        self.controller.bind(self)

    def on_pre_enter(self, *args) -> None:
        """EN: Prefill fields before showing the screen.
        RU: Предзаполнить поля перед показом экрана.
        """
        if self.controller:
            self.controller.on_enter(self)
        return super().on_pre_enter(*args)

    def _apply_layout(self) -> None:
        """EN: Apply simple layout proportions like Profile/Settings.
        RU: Применить пропорции раскладки как у Profile/Settings.
        """
        def _recalc(*_args) -> None:
            ids = self.ids
            win_w, win_h = Window.size
            pad = win_h * 0.05

            ids.main_layout.orientation = "vertical"
            ids.main_layout.size_hint = (1, 1)
            ids.main_layout.size = (win_w, win_h)
            ids.main_layout.padding = (pad, pad, pad, pad)
            ids.main_layout.spacing = 0

            inner_h = max(win_h - pad * 2, 0)

            ids.topbar.orientation = "horizontal"
            if hasattr(ids.topbar, "adaptive_height"):
                ids.topbar.adaptive_height = False
            ids.topbar.size_hint_y = None
            ids.topbar.size_hint_x = 1
            ids.topbar.height = inner_h * 0.10
            ids.topbar.size = (ids.main_layout.width - pad * 2, ids.topbar.height)

            if hasattr(ids.contentbar, "adaptive_height"):
                ids.contentbar.adaptive_height = False
            ids.contentbar.size_hint_y = None
            ids.contentbar.size_hint_x = 1
            ids.contentbar.height = inner_h * 0.50
            ids.contentbar.size = (ids.main_layout.width - pad * 2, ids.contentbar.height)

            if hasattr(ids.bottombar, "adaptive_height"):
                ids.bottombar.adaptive_height = False
            ids.bottombar.size_hint_y = None
            ids.bottombar.size_hint_x = 1
            ids.bottombar.height = inner_h * 0.40
            ids.bottombar.size = (ids.main_layout.width - pad * 2, ids.bottombar.height)

            ids.lefttopbar.size_hint = (None, 1)
            ids.lefttopbar.width = ids.topbar.width * 0.20
            ids.midltopbar.size_hint = (None, 1)
            ids.midltopbar.width = ids.topbar.width * 0.60
            ids.righttopbar.size_hint = (None, 1)
            ids.righttopbar.width = ids.topbar.width * 0.20

            ids.content_center.anchor_x = "center"
            ids.content_center.anchor_y = "center"
            ids.content_center.size_hint = (1, 1)

            ids.profile_change_card.size_hint = (1, 1)
            apply_debug_borders_to_ids(self, DEBUG_WIDGET_IDS)

        if not getattr(self, "_layout_bound", False):
            Window.bind(size=_recalc)
            self._layout_bound = True
        Clock.schedule_once(_recalc, 0)
