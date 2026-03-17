"""EN: View for the password reset screen with request/confirm actions.
RU: РџСЂРµРґСЃС‚Р°РІР»РµРЅРёРµ СЌРєСЂР°РЅР° РІРѕСЃСЃС‚Р°РЅРѕРІР»РµРЅРёСЏ РїР°СЂРѕР»СЏ СЃ РґРµР№СЃС‚РІРёСЏРјРё Р·Р°РїСЂРѕСЃР°/РїРѕРґС‚РІРµСЂР¶РґРµРЅРёСЏ.
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
    RU: РџСЂРµРґСЃС‚Р°РІР»РµРЅРёРµ СЌРєСЂР°РЅР° РІРѕСЃСЃС‚Р°РЅРѕРІР»РµРЅРёСЏ РїР°СЂРѕР»СЏ, СЃРІСЏР·С‹РІР°СЋС‰РµРµ С‚РµРєСЃС‚С‹ VM Рё РґРµР№СЃС‚РІРёСЏ API.
    """

    def on_kv_post(self, base_widget) -> None:
        """EN: Apply responsive layout and shared field/button helpers after KV load.
        RU: РџСЂРёРјРµРЅРёС‚СЊ Р°РґР°РїС‚РёРІРЅСѓСЋ СЂР°СЃРєР»Р°РґРєСѓ Рё РѕР±С‰РёРµ С…РµР»РїРµСЂС‹ РїРѕР»РµР№/РєРЅРѕРїРѕРє РїРѕСЃР»Рµ Р·Р°РіСЂСѓР·РєРё KV.
        """

        apply_password_reset_layout(self)
        wire_password_eye(self.ids.new_password_field, self.ids.new_password_eye_btn, start_hidden=True)
        apply_button_text_style(
            self,
            [self.ids.send_btn_text, self.ids.confirm_btn_text, self.ids.back_btn_text],
        )
        self.ids.reset_channel_telegram.active = True
        apply_debug_borders_to_ids(self, PASSWORD_RESET_DEBUG_IDS)
        self._ids_keepalive = dict(self.ids)
        for _key, _widget in self._ids_keepalive.items():
            self.ids[_key] = _widget
        self._contentbar_widget = getattr(self.ids.contentbar, "__self__", self.ids.contentbar)
        self._bottombar_widget = getattr(self.ids.bottombar, "__self__", self.ids.bottombar)

    def configure(self, vm: PasswordResetVM, controller: PasswordResetController) -> None:
        """EN: Configure UI texts and bind controller/API callbacks.
        RU: РќР°СЃС‚СЂРѕРёС‚СЊ С‚РµРєСЃС‚С‹ UI Рё РїСЂРёРІСЏР·Р°С‚СЊ РєРѕР»Р±СЌРєРё РєРѕРЅС‚СЂРѕР»Р»РµСЂР°/API.
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

        self._back_callback = lambda *_: controller.back()
        self.ids.send_btn.unbind(on_release=self._on_send_code_pressed)
        self.ids.send_btn.bind(on_release=self._on_send_code_pressed)
        self.ids.confirm_btn.unbind(on_release=self._on_confirm_pressed)
        self.ids.confirm_btn.bind(on_release=self._on_confirm_pressed)
        self.ids.back_btn.unbind(on_release=self._back_callback)
        self.ids.back_btn.bind(on_release=self._back_callback)

    def _on_send_code_pressed(self, *args) -> None:
        """EN: Request reset code while preserving anti-enumeration UX message.
        RU: Р—Р°РїСЂРѕСЃРёС‚СЊ reset-РєРѕРґ СЃ UX-СЃРѕРѕР±С‰РµРЅРёРµРј Р±РµР· СЂР°СЃРєСЂС‹С‚РёСЏ СЃСѓС‰РµСЃС‚РІРѕРІР°РЅРёСЏ Р°РєРєР°СѓРЅС‚Р°.
        """

        email = (self.ids.email_field.text or "").strip()
        if not email:
            self.set_error(t("reset.error.email_required"))
            return

        channel = "telegram" if self.ids.reset_channel_telegram.active else "email"
        ok, payload = auth_backend.password_reset_request(email, channel=channel)
        if not ok:
            self.set_error(t("reset.error.request_failed"))
            return
        if isinstance(payload, dict) and payload.get("reset_link_code"):
            self.set_error(t("reset.info.request_sent"))
        else:
            self.set_error(t("reset.telegram_not_verified"))

    def _on_confirm_pressed(self, *args) -> None:
        """EN: Confirm one-time code and set new password, then return to login.
        RU: РџРѕРґС‚РІРµСЂРґРёС‚СЊ РѕРґРЅРѕСЂР°Р·РѕРІС‹Р№ РєРѕРґ Рё Р·Р°РґР°С‚СЊ РЅРѕРІС‹Р№ РїР°СЂРѕР»СЊ, Р·Р°С‚РµРј РІРµСЂРЅСѓС‚СЊСЃСЏ РЅР° РІС…РѕРґ.
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

        ok, payload = auth_backend.password_reset_confirm(email, code, new_psw)
        if not ok:
            error = str((payload or {}).get("error") or "")
            if error in {"CODE_INVALID", "EMAIL_NOT_FOUND"}:
                self.set_error(t("reset.error.invalid_code"))
            elif error == "CODE_EXPIRED":
                self.set_error(t("reset.error.code_expired"))
            elif error in {"CODE_USED", "CODE_LOCKED"}:
                self.set_error(t("reset.error.code_used"))
            else:
                self.set_error(t("reset.error.confirm_failed"))
            return

        self._clear_fields()
        self.set_error("")
        self.controller.back()

    def set_error(self, text: str) -> None:
        """EN: Set status text visibility in error/info label.
        RU: РЈСЃС‚Р°РЅРѕРІРёС‚СЊ РІРёРґРёРјРѕСЃС‚СЊ С‚РµРєСЃС‚Р° СЃС‚Р°С‚СѓСЃР° РІ Р»РµР№Р±Р»Рµ РѕС€РёР±РѕРє/РёРЅС„РѕСЂРјР°С†РёРё.
        """

        self.ids.error_lbl.text = text
        self.ids.error_lbl.opacity = 1 if text else 0

    def on_pre_enter(self, *args) -> None:
        """EN: Focus email field on desktop for faster keyboard flow.
        RU: РЎС‚Р°РІРёС‚СЊ С„РѕРєСѓСЃ РЅР° email РЅР° РґРµСЃРєС‚РѕРїРµ РґР»СЏ Р±С‹СЃС‚СЂРѕРіРѕ РІРІРѕРґР° СЃ РєР»Р°РІРёР°С‚СѓСЂС‹.
        """

        super().on_pre_enter(*args)
        if kivy_platform in ("android", "ios"):
            return
        self.ids.email_field.focus = True

    def _clear_fields(self) -> None:
        """EN: Clear all reset form fields after successful password update.
        RU: РћС‡РёСЃС‚РёС‚СЊ РІСЃРµ РїРѕР»СЏ С„РѕСЂРјС‹ РІРѕСЃСЃС‚Р°РЅРѕРІР»РµРЅРёСЏ РїРѕСЃР»Рµ СѓСЃРїРµС€РЅРѕР№ СЃРјРµРЅС‹ РїР°СЂРѕР»СЏ.
        """

        self.ids.code_field.text = ""
        self.ids.new_password_field.text = ""

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

