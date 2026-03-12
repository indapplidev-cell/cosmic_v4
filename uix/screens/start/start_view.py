"""EN: View for the start screen.
RU: Представление стартового экрана.
"""

from pathlib import Path

from kivy.lang import Builder
from kivymd.uix.screen import MDScreen

from manager.ads import AdsManager
from uix.debug.debug_borders import apply_debug_borders_to_ids
from uix.screens.common.button_text_style import apply_button_text_style, caps

from .start_controller import StartScreenController
from .start_layout import START_DEBUG_IDS, apply_start_layout
from .start_vm import StartScreenVM

KV_PATH = Path(__file__).with_name("start.kv")
Builder.load_file(str(KV_PATH))


class StartScreenView(MDScreen):
    """EN: Start screen view that wires layout, VM, and controller.
    RU: Представление старта, связывающее раскладку, VM и контроллер.
    """

    def on_kv_post(self, base_widget) -> None:
        """EN: Apply layout after KV is ready.
        RU: Применить раскладку после загрузки KV.
        """
        apply_start_layout(self)
        apply_button_text_style(
            self,
            [
                self.ids.game_btn_text,
                self.ids.profile_btn_text,
                self.ids.settings_btn_text,
            ],
        )
        apply_debug_borders_to_ids(self, START_DEBUG_IDS)

    def on_pre_enter(self, *args):
        """EN: Attach the shared top-bar banner slot before showing the screen.
        RU: Подключить общий banner-slot в верхней панели перед показом экрана.
        """
        AdsManager.attach_banner(self.ids.get("ads_banner_slot"))
        return super().on_pre_enter(*args)

    def on_pre_leave(self, *args):
        """EN: Detach the shared top-bar banner slot before leaving the screen.
        RU: Отсоединить общий banner-slot в верхней панели перед уходом с экрана.
        """
        AdsManager.detach_banner()
        return super().on_pre_leave(*args)

    def configure(self, vm: StartScreenVM, controller: StartScreenController) -> None:
        """EN: Configure texts and bind callbacks.
        RU: Настроить тексты и привязать колбэки.
        """
        self.ids.title_lbl.text = vm.title
        self.ids.game_btn_text.text = caps(vm.game_text)
        self.ids.profile_btn_text.text = caps(vm.profile_text)
        self.ids.settings_btn_text.text = caps(vm.settings_text)

        self.ids.game_btn.on_release = controller.game
        self.ids.profile_btn.on_release = controller.profile
        self.ids.settings_btn.on_release = controller.settings
