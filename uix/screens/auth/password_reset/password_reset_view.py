"""EN: View for the password reset screen with request/confirm actions.
RU: Представление экрана восстановления пароля с действиями запроса/подтверждения.
"""

from pathlib import Path

from kivy.lang import Builder
from kivy.utils import platform as kivy_platform
from kivymd.uix.screen import MDScreen

from manager import auth_backend
from manager.input_validation import validate_login
from manager.lang.lang_manager import t
from uix.debug.debug_borders import apply_debug_borders_to_ids
from uix.screens.common.button_text_style import apply_button_text_style, caps
from uix.screens.common.password_eye import wire_password_eye

from .password_reset_controller import PasswordResetController
from .password_reset_layout import PASSWORD_RESET_DEBUG_IDS, apply_password_reset_layout
from .password_reset_vm import PasswordResetVM

KV_PATH = Path(__file__).with_name("password_reset.kv")
Builder.load_file(str(KV_PATH))


class PasswordResetScreenView(MDScreen):
    """EN: Password reset screen view that binds VM texts and API actions.
    RU: Представление экрана восстановления пароля, связывающее тексты VM и действия API.
    """

    def on_kv_post(self, base_widget) -> None:
        """EN: Apply responsive layout and shared field/button helpers after KV load.
        RU: Применить адаптивную раскладку и общие хелперы полей/кнопок после загрузки KV.
        """

        apply_password_reset_layout(self)
        wire_password_eye(self.ids.new_password_field, self.ids.new_password_eye_btn, start_hidden=True)
        apply_button_text_style(
            self,
            [self.ids.send_btn_text, self.ids.confirm_btn_text, self.ids.back_btn_text],
        )
        self.ids.reset_channel_telegram.active = True
        apply_debug_borders_to_ids(self, PASSWORD_RESET_DEBUG_IDS)

    def configure(self, vm: PasswordResetVM, controller: PasswordResetController) -> None:
        """EN: Configure UI texts and bind controller/API callbacks.
        RU: Настроить тексты UI и привязать колбэки контроллера/API.
        """

        self.controller = controller
        self.ids.title_lbl.text = vm.title
        self.ids.email_hint.text = vm.email_hint
        self.ids.code_hint.text = vm.code_hint
        self.ids.new_password_hint.text = vm.new_password_hint
        self.ids.send_btn_text.text = caps(vm.send_code_text)
        self.ids.confirm_btn_text.text = caps(vm.confirm_text)
        self.ids.back_btn_text.text = caps(vm.back_text)
        self.ids.reset_channel_telegram_lbl.text = t("reset.channel.telegram")
        self.ids.reset_channel_email_lbl.text = t("reset.channel.email")
        self.set_error(vm.error_text)

        self.ids.send_btn.on_release = self._on_send_code_pressed
        self.ids.confirm_btn.on_release = self._on_confirm_pressed
        self.ids.back_btn.on_release = controller.back

    def _on_send_code_pressed(self) -> None:
        """EN: Request reset code while preserving anti-enumeration UX message.
        RU: Запросить reset-код с UX-сообщением без раскрытия существования аккаунта.
        """

        email = (self.ids.email_field.text or "").strip()
        if not email:
            self.set_error(t("reset.error.email_required"))
            return

        channel = "telegram" if self.ids.reset_channel_telegram.active else "email"
        ok, _error = auth_backend.password_reset_request(email, channel=channel)
        if not ok:
            self.set_error(t("reset.error.request_failed"))
            return
        self.set_error(t("reset.info.request_sent"))

    def _on_confirm_pressed(self) -> None:
        """EN: Confirm one-time code and set new password, then return to login.
        RU: Подтвердить одноразовый код и задать новый пароль, затем вернуться на вход.
        """

        email = (self.ids.email_field.text or "").strip()
        code = (self.ids.code_field.text or "").strip()
        new_psw = self.ids.new_password_field.text or ""

        if not code.isdigit() or len(code) != 6:
            self.set_error(t("reset.error.invalid_code"))
            return

        ok_input, input_error, _field = validate_login(email, new_psw)
        if not ok_input:
            if input_error == "EMAIL_FORMAT":
                self.set_error(t("reset.error.email_invalid"))
            elif input_error == "PASSWORD_LENGTH":
                self.set_error(t("reset.error.password_length"))
            elif input_error == "CONTROL_CHARS":
                self.set_error(t("reset.error.password_control"))
            else:
                self.set_error(t("reset.error.invalid_input"))
            return

        ok, error = auth_backend.password_reset_confirm(email, code, new_psw)
        if not ok:
            if error == "INVALID_CODE":
                self.set_error(t("reset.error.invalid_code"))
            else:
                self.set_error(t("reset.error.confirm_failed"))
            return

        self._clear_fields()
        self.set_error("")
        self.controller.back()

    def set_error(self, text: str) -> None:
        """EN: Set status text visibility in error/info label.
        RU: Установить видимость текста статуса в лейбле ошибок/информации.
        """

        self.ids.error_lbl.text = text
        self.ids.error_lbl.opacity = 1 if text else 0

    def on_pre_enter(self, *args) -> None:
        """EN: Focus email field on desktop for faster keyboard flow.
        RU: Ставить фокус на email на десктопе для быстрого ввода с клавиатуры.
        """

        super().on_pre_enter(*args)
        if kivy_platform in ("android", "ios"):
            return
        self.ids.email_field.focus = True

    def _clear_fields(self) -> None:
        """EN: Clear all reset form fields after successful password update.
        RU: Очистить все поля формы восстановления после успешной смены пароля.
        """

        self.ids.code_field.text = ""
        self.ids.new_password_field.text = ""
