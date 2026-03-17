"""EN: View for the start screen.
RU: Р СџРЎР‚Р ВµР Т‘РЎРѓРЎвЂљР В°Р Р†Р В»Р ВµР Р…Р С‘Р Вµ РЎРѓРЎвЂљР В°РЎР‚РЎвЂљР С•Р Р†Р С•Р С–Р С• РЎРЊР С”РЎР‚Р В°Р Р…Р В°.
"""

from pathlib import Path

from kivy.lang import Builder
from kivy.logger import Logger
from kivymd.uix.screen import MDScreen

from uix.debug.debug_borders import apply_debug_borders_to_ids
from uix.screens.common.button_text_style import apply_button_text_style, caps

from .start_controller import StartScreenController
from .start_layout import START_DEBUG_IDS, apply_start_layout
from .start_vm import StartScreenVM

KV_PATH = Path(__file__).with_name("start.kv")
Builder.load_file(str(KV_PATH))


class StartScreenView(MDScreen):
    """EN: Start screen view that wires layout, VM, and controller.
    RU: Р СџРЎР‚Р ВµР Т‘РЎРѓРЎвЂљР В°Р Р†Р В»Р ВµР Р…Р С‘Р Вµ РЎРѓРЎвЂљР В°РЎР‚РЎвЂљР В°, РЎРѓР Р†РЎРЏР В·РЎвЂ№Р Р†Р В°РЎР‹РЎвЂ°Р ВµР Вµ РЎР‚Р В°РЎРѓР С”Р В»Р В°Р Т‘Р С”РЎС“, VM Р С‘ Р С”Р С•Р Р…РЎвЂљРЎР‚Р С•Р В»Р В»Р ВµРЎР‚.
    """

    def on_kv_post(self, base_widget) -> None:
        """EN: Apply layout after KV is ready.
        RU: Р СџРЎР‚Р С‘Р СР ВµР Р…Р С‘РЎвЂљРЎРЉ РЎР‚Р В°РЎРѓР С”Р В»Р В°Р Т‘Р С”РЎС“ Р С—Р С•РЎРѓР В»Р Вµ Р В·Р В°Р С–РЎР‚РЎС“Р В·Р С”Р С‘ KV.
        """
        Logger.info("[UI] apply_layout screen=Start before main_layout=%s" % self.ids.get("main_layout"))
        apply_start_layout(self)
        Logger.info("[UI] apply_layout screen=Start after main_layout=%s" % self.ids.get("main_layout"))
        apply_button_text_style(
            self,
            [
                self.ids.game_btn_text,
                self.ids.profile_btn_text,
                self.ids.settings_btn_text,
            ],
        )
        apply_debug_borders_to_ids(self, START_DEBUG_IDS)
        self._ids_keepalive = dict(self.ids)
        for _key, _widget in self._ids_keepalive.items():
            self.ids[_key] = _widget
        self._contentbar_widget = getattr(self.ids.contentbar, "__self__", self.ids.contentbar)
        self._bottombar_widget = getattr(self.ids.bottombar, "__self__", self.ids.bottombar)

    def configure(self, vm: StartScreenVM, controller: StartScreenController) -> None:
        """EN: Configure texts and bind callbacks.
        RU: Р СњР В°РЎРѓРЎвЂљРЎР‚Р С•Р С‘РЎвЂљРЎРЉ РЎвЂљР ВµР С”РЎРѓРЎвЂљРЎвЂ№ Р С‘ Р С—РЎР‚Р С‘Р Р†РЎРЏР В·Р В°РЎвЂљРЎРЉ Р С”Р С•Р В»Р В±РЎРЊР С”Р С‘.
        """
        self.ids.title_lbl.text = vm.title
        self.ids.game_btn_text.text = caps(vm.game_text)
        self.ids.profile_btn_text.text = caps(vm.profile_text)
        self.ids.settings_btn_text.text = caps(vm.settings_text)

        self._game_callback = lambda *_: controller.game()
        self._profile_callback = lambda *_: controller.profile()
        self._settings_callback = lambda *_: controller.settings()
        self.ids.game_btn.unbind(on_release=self._game_callback)
        self.ids.game_btn.bind(on_release=self._game_callback)
        self.ids.profile_btn.unbind(on_release=self._profile_callback)
        self.ids.profile_btn.bind(on_release=self._profile_callback)
        self.ids.settings_btn.unbind(on_release=self._settings_callback)
        self.ids.settings_btn.bind(on_release=self._settings_callback)

    def get_shell_content_widget(self):
        """EN: Return the reusable content bar widget for the shared shell host.
        RU: Р’РµСЂРЅСѓС‚СЊ РїРµСЂРµРёСЃРїРѕР»СЊР·СѓРµРјС‹Р№ content bar-РІРёРґР¶РµС‚ РґР»СЏ РѕР±С‰РµРіРѕ host-РєРѕРЅС‚РµР№РЅРµСЂР° shell.
        """

        return self._contentbar_widget

    def get_shell_bottom_widget(self):
        """EN: Return the reusable bottom bar widget for the shared shell host.
        RU: Р’РµСЂРЅСѓС‚СЊ РїРµСЂРµРёСЃРїРѕР»СЊР·СѓРµРјС‹Р№ bottom bar-РІРёРґР¶РµС‚ РґР»СЏ РѕР±С‰РµРіРѕ host-РєРѕРЅС‚РµР№РЅРµСЂР° shell.
        """

        return self._bottombar_widget


