"""EN: View for the register screen.
RU: Представление экрана регистрации.
"""

from pathlib import Path

from data.user_cache.user_cache_writer import save_user
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivymd.uix.screen import MDScreen
from manager.auth.logup_manager import LogupManager
from manager.lang.lang_manager import t
from uix.debug.debug_borders import apply_debug_borders_to_ids
from uix.screens.common.button_text_style import apply_button_text_style, caps
from uix.screens.common.password_eye import wire_password_eye

from .register_controller import RegisterController
from .register_layout import REGISTER_DEBUG_IDS, apply_register_layout
from .register_vm import RegisterVM

KV_PATH = Path(__file__).with_name("register.kv")
Builder.load_file(str(KV_PATH))


class RegisterScreenView(MDScreen):
    """EN: Register screen view that wires layout, VM, and controller.
    RU: Представление регистрации, связывающее раскладку, VM и контроллер.
    """

    def on_kv_post(self, base_widget) -> None:
        """EN: Apply layout after KV is ready.
        RU: Применить раскладку после загрузки KV.
        """
        apply_register_layout(self)
        wire_password_eye(self.ids.register_password_field, self.ids.password_eye_btn, start_hidden=True)
        wire_password_eye(self.ids.register_password2_field, self.ids.password2_eye_btn, start_hidden=True)
        apply_button_text_style(
            self,
            [
                self.ids.create_btn_text,
                self.ids.to_login_btn_text,
            ],
        )
        apply_debug_borders_to_ids(self, REGISTER_DEBUG_IDS)

    def configure(self, vm: RegisterVM, controller: RegisterController) -> None:
        """EN: Configure texts and bind callbacks.
        RU: Настроить тексты и привязать колбэки.
        """
        self.controller = controller
        self.ids.title_lbl.text = vm.title_text
        self.ids.email_hint.text = vm.email_hint
        self.ids.password_hint.text = vm.password_hint
        self.ids.password2_hint.text = vm.password2_hint
        self.ids.create_btn_text.text = caps(vm.create_text)
        self.ids.to_login_btn_text.text = caps(vm.login_text)
        self.set_error(vm.error_text)
        self._wire_widgets()

        self.ids.create_btn.on_release = self._on_create_pressed
        self.ids.to_login_btn.on_release = controller.to_login

    def _wire_widgets(self) -> None:
        """EN: Cache field widgets for validation and focus control.
        RU: Сохранить ссылки на поля для валидации и управления фокусом.
        """
        self.email_field = self.ids.register_email_field
        self.password_field = self.ids.register_password_field
        self.password2_field = self.ids.register_password2_field

    def _on_create_pressed(self) -> None:
        """EN: Validate registration data, save cache, and dispatch create action.
        RU: Проверить данные регистрации, сохранить кэш и перейти к созданию.
        """
        email = (self.email_field.text or "").strip()
        password = (self.password_field.text or "").strip()
        password2 = (self.password2_field.text or "").strip()
        ok, message, focus_field = LogupManager.validate(email, password, password2)
        if not ok:
            self._show_error_popup(message, focus_field)
            return

        save_user(email, password)
        self._clear_fields()
        self.controller.create()

    def _show_error_popup(self, message: str, focus_field: str) -> None:
        """EN: Show validation error popup and set focus after closing.
        RU: Показать попап с ошибкой и вернуть фокус после закрытия.
        """
        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        content.add_widget(Label(text=message))
        ok_btn = Button(text=t("common.ok"), size_hint_y=None, height=dp(40))
        content.add_widget(ok_btn)

        popup = Popup(title="", content=content, size_hint=(0.8, 0.4), auto_dismiss=False)

        def _close_and_focus(_instance) -> None:
            popup.dismiss()
            self._focus_field(focus_field)

        ok_btn.bind(on_release=_close_and_focus)
        popup.open()

    def _focus_field(self, focus_field: str) -> None:
        """EN: Set focus to a field by its validation key.
        RU: Установить фокус на поле по ключу валидации.
        """
        mapping = {
            "email": self.email_field,
            "password": self.password_field,
            "password2": self.password2_field,
        }
        target = mapping.get(focus_field)
        if target is not None:
            target.focus = True

    def _clear_fields(self) -> None:
        """EN: Clear registration input fields after successful validation.
        RU: Очистить поля регистрации после успешной проверки.
        """
        self.email_field.text = ""
        self.password_field.text = ""
        self.password2_field.text = ""

    def set_error(self, text: str) -> None:
        """EN: Set error text visibility.
        RU: Установить видимость текста ошибки.
        """
        self.ids.error_lbl.text = text
        self.ids.error_lbl.opacity = 1 if text else 0
