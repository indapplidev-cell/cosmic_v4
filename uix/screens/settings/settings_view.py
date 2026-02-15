"""EN: View for the settings screen.
RU: Представление экрана настроек.
"""

from pathlib import Path

from data.user_cache.user_cache_reader import get_user_cache
from data.user_cache.user_session import UserSession
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from manager.auth.account_delete import confirm_delete_account
from manager.lang.lang_manager import t
from uix.debug.debug_borders import apply_debug_borders_to_ids
from uix.screens.common.button_text_style import apply_button_text_style, caps

from .settings_controller import SettingsScreenController
from .settings_layout import SETTINGS_DEBUG_IDS, apply_settings_layout
from .settings_vm import SettingsScreenVM

KV_PATH = Path(__file__).with_name("settings.kv")
Builder.load_file(str(KV_PATH))


class SettingsScreenView(MDScreen):
    """EN: Settings screen view that wires layout, VM, and controller.
    RU: Представление настроек, связывающее раскладку, VM и контроллер.
    """

    def on_kv_post(self, base_widget) -> None:
        """EN: Apply layout after KV is ready.
        RU: Применить раскладку после загрузки KV.
        """
        apply_settings_layout(self)
        from manager.lang.lang_radio import bind_lang_radios
        bind_lang_radios(self.ids.lang_ru_radio, self.ids.lang_en_radio)
        apply_button_text_style(
            self,
            [
                self.ids.login_btn_text,
                self.ids.action_btn_text,
                self.ids.back_btn_text,
            ],
        )
        apply_debug_borders_to_ids(self, SETTINGS_DEBUG_IDS)

    def on_pre_enter(self, *args) -> None:
        """EN: Update login button text based on auth state.
        RU: Обновить текст кнопки входа по состоянию авторизации.
        """
        super().on_pre_enter(*args)
        no_data = t("common.no_data")
        app = MDApp.get_running_app()
        if hasattr(app, "is_logged_in"):
            app.is_logged_in = UserSession().is_logged_in()
        if getattr(app, "is_logged_in", False):
            cache = get_user_cache() or {}
            login_raw = cache.get("login") or ""
            login_val = login_raw.strip() or no_data
            self.ids.settings_top_right_login.text = login_val
        else:
            self.ids.settings_top_right_login.text = no_data

    def open_doc_popup(self, text: str) -> None:
        """EN: Open a simple document popup with the passed label text.
        RU: Открыть простой popup документа с переданным текстом лейбла.
        """
        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        content.add_widget(Label(text=text))
        ok_btn = Button(text=t("common.ok"), size_hint_y=None, height=dp(40))
        content.add_widget(ok_btn)

        popup = Popup(title="", content=content, size_hint=(0.8, 0.4), auto_dismiss=False)
        ok_btn.bind(on_release=lambda _instance: popup.dismiss())
        popup.open()

    def on_delete_account_pressed(self) -> None:
        confirm_delete_account(
            on_deleted=lambda: self._controller.logout(),
            on_cancel=lambda: None,
        )

    def configure(self, vm: SettingsScreenVM, controller: SettingsScreenController) -> None:
        """EN: Configure texts and bind callbacks.
        RU: Настроить тексты и привязать колбэки.
        """
        self._controller = controller
        self.ids.left_text.text = vm.title
        self.ids.login_btn_text.text = caps(vm.login_text)
        self.ids.action_btn_text.text = caps(vm.action_text)
        self.ids.back_btn_text.text = caps(vm.back_text)

        self.ids.login_btn.on_release = controller.payout
        self.ids.action_btn.on_release = controller.logout
        self.ids.back_btn.on_release = controller.back
