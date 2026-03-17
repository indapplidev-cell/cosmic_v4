"""EN: View for the login screen.
RU: РџСЂРµРґСЃС‚Р°РІР»РµРЅРёРµ СЌРєСЂР°РЅР° РІС…РѕРґР°.
"""

from pathlib import Path

from manager import auth_backend
from manager.config import TELEGRAM_BOT_USERNAME
from manager.input_validation import validate_login
from manager.lang.lang_manager import t
from manager.telegram_deeplink import open_telegram_bot_chat
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.utils import platform as kivy_platform
from kivymd.uix.button import MDIconButton
from kivymd.uix.screen import MDScreen
from manager.tg_debug_log import tglog
from uix.debug.debug_borders import apply_debug_borders_to_ids
from uix.screens.common.button_text_style import apply_button_text_style, caps
from uix.screens.common.password_eye import wire_password_eye

from .login_controller import LoginController
from .login_layout import LOGIN_DEBUG_IDS, apply_login_layout
from .login_vm import LoginVM

KV_PATH = Path(__file__).with_name("login.kv")
Builder.load_file(str(KV_PATH))


class LoginScreenView(MDScreen):
    """EN: Login screen view that wires layout, VM, and controller.
    RU: РџСЂРµРґСЃС‚Р°РІР»РµРЅРёРµ РІС…РѕРґР°, СЃРІСЏР·С‹РІР°СЋС‰РµРµ СЂР°СЃРєР»Р°РґРєСѓ, VM Рё РєРѕРЅС‚СЂРѕР»Р»РµСЂ.
    """

    def __init__(self, **kwargs) -> None:
        """EN: Initialize login view state for duplicate-click protection.
        RU: РРЅРёС†РёР°Р»РёР·РёСЂРѕРІР°С‚СЊ СЃРѕСЃС‚РѕСЏРЅРёРµ СЌРєСЂР°РЅР° РІС…РѕРґР° РґР»СЏ Р·Р°С‰РёС‚С‹ РѕС‚ РґРІРѕР№РЅС‹С… РєР»РёРєРѕРІ.

        EN: The in-flight flag blocks repeated taps while the auth request is being processed.
        RU: Р¤Р»Р°Рі in-flight Р±Р»РѕРєРёСЂСѓРµС‚ РїРѕРІС‚РѕСЂРЅС‹Рµ РЅР°Р¶Р°С‚РёСЏ, РїРѕРєР° РѕР±СЂР°Р±Р°С‚С‹РІР°РµС‚СЃСЏ auth-Р·Р°РїСЂРѕСЃ.
        """
        super().__init__(**kwargs)
        self._auth_inflight = False
        self._auth_inflight_reset_ev = None

    def on_kv_post(self, base_widget) -> None:
        """EN: Apply layout after KV is ready.
        RU: РџСЂРёРјРµРЅРёС‚СЊ СЂР°СЃРєР»Р°РґРєСѓ РїРѕСЃР»Рµ Р·Р°РіСЂСѓР·РєРё KV.
        """
        apply_login_layout(self)
        wire_password_eye(self.ids.password_field, self.ids.password_eye_btn, start_hidden=True)
        apply_button_text_style(
            self,
            [
                self.ids.forgot_btn_text,
                self.ids.login_btn_text,
                self.ids.register_btn_text,
            ],
        )
        apply_debug_borders_to_ids(self, LOGIN_DEBUG_IDS)
        self._ids_keepalive = dict(self.ids)
        for _key, _widget in self._ids_keepalive.items():
            self.ids[_key] = _widget
        self._contentbar_widget = getattr(self.ids.contentbar, "__self__", self.ids.contentbar)
        self._bottombar_widget = getattr(self.ids.bottombar, "__self__", self.ids.bottombar)

    def configure(self, vm: LoginVM, controller: LoginController) -> None:
        """EN: Configure texts and bind callbacks.
        RU: РќР°СЃС‚СЂРѕРёС‚СЊ С‚РµРєСЃС‚С‹ Рё РїСЂРёРІСЏР·Р°С‚СЊ РєРѕР»Р±СЌРєРё.
        """
        self.controller = controller
        self.ids.title_lbl.text = vm.title
        self.ids.email_hint.text = vm.email_hint
        self.ids.password_hint.text = vm.password_hint
        self.ids.forgot_btn_text.text = caps(vm.forgot_text)
        self.ids.login_btn_text.text = caps(vm.login_text)
        self.ids.register_btn_text.text = caps(vm.register_text)
        self.set_error(vm.error_text)

        self._register_callback = lambda *_: controller.register()
        self.ids.login_btn.unbind(on_release=self._on_login_pressed)
        self.ids.login_btn.bind(on_release=self._on_login_pressed)
        self.ids.forgot_btn.unbind(on_release=self._on_forgot_pressed)
        self.ids.forgot_btn.bind(on_release=self._on_forgot_pressed)
        self.ids.register_btn.unbind(on_release=self._register_callback)
        self.ids.register_btn.bind(on_release=self._register_callback)

    def on_pre_enter(self, *args) -> None:
        """EN: Ensure email field focus on screen entry.
        RU: РћР±РµСЃРїРµС‡РёС‚СЊ С„РѕРєСѓСЃ РЅР° РїРѕР»Рµ email РїСЂРё РІС…РѕРґРµ РЅР° СЌРєСЂР°РЅ.
        """
        super().on_pre_enter(*args)

        def _focus(_dt: float) -> None:
            """EN: Move focus to email field after layout is ready.
            RU: РџРµСЂРµРІРµСЃС‚Рё С„РѕРєСѓСЃ РЅР° РїРѕР»Рµ email РїРѕСЃР»Рµ РіРѕС‚РѕРІРЅРѕСЃС‚Рё СЂР°СЃРєР»Р°РґРєРё.
            """
            if kivy_platform in ("android", "ios"):
                return
            self.ids.password_field.focus = False
            self.ids.email_field.focus = True
            self.ids.email_field.cursor = (len(self.ids.email_field.text or ""), 0)

        Clock.schedule_once(_focus, 0)

    def _on_login_pressed(self, *args) -> None:
        """EN: Validate credentials before dispatching login.
        RU: РџСЂРѕРІРµСЂРёС‚СЊ СѓС‡РµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ РїРµСЂРµРґ РґРёСЃРїРµС‚С‡РµСЂРёР·Р°С†РёРµР№ РІС…РѕРґР°.
        """
        if self._auth_inflight:
            tglog("[AUTH] drop duplicate click action=login")
            return
        self._auth_inflight = True
        self._auth_inflight_reset_ev = Clock.schedule_once(self._reset_auth_inflight_safety, 3)

        email = (self.ids.email_field.text or "").strip()
        password = self.ids.password_field.text or ""
        try:
            ok_input, error_code, _field = validate_login(email, password)
            if not ok_input:
                msg_map = {
                    "EMAIL_FORMAT": "Invalid email format / РќРµРІРµСЂРЅС‹Р№ С„РѕСЂРјР°С‚ email",
                    "PASSWORD_LENGTH": "Password length must be 8..72 / Р”Р»РёРЅР° РїР°СЂРѕР»СЏ РґРѕР»Р¶РЅР° Р±С‹С‚СЊ 8..72",
                    "CONTROL_CHARS": "Password contains forbidden chars / РџР°СЂРѕР»СЊ СЃРѕРґРµСЂР¶РёС‚ Р·Р°РїСЂРµС‰С‘РЅРЅС‹Рµ СЃРёРјРІРѕР»С‹",
                }
                self.set_error(msg_map.get(error_code, "Invalid input / РќРµРєРѕСЂСЂРµРєС‚РЅС‹Р№ РІРІРѕРґ"))
                return
            ok_login, payload = auth_backend.login(email, password)
            if not ok_login:
                self.set_error(t("login.error.invalid_credentials"))
                return
            self.set_error("")
            self.controller.login()
            self._clear_fields()
        finally:
            self._clear_auth_inflight()

    def _on_forgot_pressed(self, *args) -> None:
        """EN: Run Telegram-only forgot-password flow from login screen via popup.
        RU: Р—Р°РїСѓСЃС‚РёС‚СЊ Telegram-only flow В«Р—Р°Р±С‹Р»Рё РїР°СЂРѕР»СЊВ» СЃ СЌРєСЂР°РЅР° РІС…РѕРґР° С‡РµСЂРµР· popup.
        """

        email = str((self.ids.email_field.text or "").strip())
        if not email:
            self.set_error(t("reset.error.email_required"))
            return

        ok, payload = auth_backend.password_reset_request(email, channel="telegram")
        if not ok:
            self._show_simple_popup(t("reset.error.request_failed"))
            return

        reset_link_code = str((payload.get("reset_link_code") or "").strip()) if isinstance(payload, dict) else ""
        ttl_sec = int((payload.get("ttl_sec") or 0)) if isinstance(payload, dict) else 0
        tglog(
            f"[TGDBG][RESET] open tg start={auth_backend.mask_token('R_' + reset_link_code) if reset_link_code else '-'} ttl={ttl_sec}"
        )
        if not reset_link_code:
            self._show_simple_popup(t("reset.telegram_not_verified"))
            return

        start_payload = f"R_{reset_link_code}"
        open_telegram_bot_chat(TELEGRAM_BOT_USERNAME, start_payload)
        self._show_reset_confirm_popup(email=email)

    def _show_simple_popup(self, message: str) -> None:
        """EN: Show one-button informational popup for login forgot-password flow.
        RU: РџРѕРєР°Р·Р°С‚СЊ РёРЅС„РѕСЂРјР°С†РёРѕРЅРЅС‹Р№ popup СЃ РѕРґРЅРѕР№ РєРЅРѕРїРєРѕР№ РґР»СЏ flow РІРѕСЃСЃС‚Р°РЅРѕРІР»РµРЅРёСЏ РЅР° login.
        """

        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        lbl = Label(text=message, halign="center", valign="middle")
        lbl.bind(size=lambda inst, _: setattr(inst, "text_size", inst.size))
        btn = Button(text=t("common.ok"), size_hint=(1, None), height=44)
        content.add_widget(lbl)
        content.add_widget(btn)
        popup = Popup(title="", content=content, size_hint=(0.85, 0.35), auto_dismiss=False)
        btn.bind(on_release=lambda *_: popup.dismiss())
        popup.open()

    def _show_reset_confirm_popup(self, email: str) -> None:
        """EN: Show popup for entering bot confirm_code and new password pair.
        RU: РџРѕРєР°Р·Р°С‚СЊ popup РІРІРѕРґР° bot confirm_code Рё РїР°СЂС‹ РЅРѕРІРѕРіРѕ РїР°СЂРѕР»СЏ.
        """

        content = BoxLayout(orientation="vertical", spacing=8, padding=10)
        info = Label(text=t("reset.popup_instruction"), halign="center", valign="middle", size_hint=(1, 0.28))
        info.bind(size=lambda inst, _: setattr(inst, "text_size", inst.size))
        code_row = BoxLayout(orientation="horizontal", spacing=8, size_hint=(1, 0.18))
        code_inp = TextInput(hint_text=t("reset.hint_code"), multiline=False, input_filter="int", size_hint=(0.86, 1))
        code_row.add_widget(code_inp)
        code_row.add_widget(Widget(size_hint=(0.14, 1)))

        psw_row = BoxLayout(orientation="horizontal", spacing=8, size_hint=(1, 0.18))
        psw_inp = TextInput(hint_text=t("reset.hint_new_password"), multiline=False, password=True, size_hint=(0.86, 1))
        psw_eye_btn = MDIconButton(
            icon="eye-off",
            size_hint=(0.14, 1),
            pos_hint={"center_y": 0.5},
        )
        psw_row.add_widget(psw_inp)
        psw_row.add_widget(psw_eye_btn)

        psw2_row = BoxLayout(orientation="horizontal", spacing=8, size_hint=(1, 0.18))
        psw2_inp = TextInput(hint_text=t("reset.hint_new_password_repeat"), multiline=False, password=True, size_hint=(0.86, 1))
        psw2_eye_btn = MDIconButton(
            icon="eye-off",
            size_hint=(0.14, 1),
            pos_hint={"center_y": 0.5},
        )
        psw2_row.add_widget(psw2_inp)
        psw2_row.add_widget(psw2_eye_btn)
        row = BoxLayout(orientation="horizontal", spacing=8, size_hint=(1, 0.18))
        ok_btn = Button(text=t("common.ok"))
        back_btn = Button(text=t("common.back"))
        row.add_widget(ok_btn)
        row.add_widget(back_btn)
        content.add_widget(info)
        content.add_widget(code_row)
        content.add_widget(psw_row)
        content.add_widget(psw2_row)
        content.add_widget(row)
        popup = Popup(title="", content=content, size_hint=(0.9, 0.55), auto_dismiss=False)

        wire_password_eye(psw_inp, psw_eye_btn, start_hidden=True)
        wire_password_eye(psw2_inp, psw2_eye_btn, start_hidden=True)

        def _submit(*_args) -> None:
            code_value = str((code_inp.text or "").strip())
            psw_value = str(psw_inp.text or "")
            psw2_value = str(psw2_inp.text or "")
            if not code_value.isdigit() or len(code_value) != 6:
                self._show_simple_popup(t("reset.error.invalid_code"))
                return
            if psw_value != psw2_value:
                self._show_simple_popup(t("reset.error.password_mismatch"))
                return
            ok_input, input_error, _field = validate_login(email, psw_value)
            if not ok_input:
                if input_error == "PASSWORD_LENGTH":
                    self._show_simple_popup(t("reset.error.password_length"))
                elif input_error == "CONTROL_CHARS":
                    self._show_simple_popup(t("reset.error.password_control"))
                else:
                    self._show_simple_popup(t("reset.error.invalid_input"))
                return

            ok_confirm, response = auth_backend.password_reset_confirm(email, code_value, psw_value)
            if not ok_confirm:
                error = str((response or {}).get("error") or "API_ERROR")
                if error == "CODE_EXPIRED":
                    self._show_simple_popup(t("reset.error.code_expired"))
                elif error in {"CODE_USED", "CODE_LOCKED"}:
                    self._show_simple_popup(t("reset.error.code_used"))
                elif error in {"CODE_INVALID", "EMAIL_NOT_FOUND"}:
                    self._show_simple_popup(t("reset.error.invalid_code"))
                else:
                    self._show_simple_popup(t("reset.error.confirm_failed"))
                return

            popup.dismiss()
            self._show_simple_popup(t("reset.success.password_changed"))

        ok_btn.bind(on_release=_submit)
        back_btn.bind(on_release=lambda *_: popup.dismiss())
        popup.open()

    def _reset_auth_inflight_safety(self, _dt: float) -> None:
        """EN: Safety reset for in-flight auth flag in case callback chain is interrupted.
        RU: Р—Р°С‰РёС‚РЅС‹Р№ СЃР±СЂРѕСЃ С„Р»Р°РіР° in-flight РґР»СЏ auth, РµСЃР»Рё С†РµРїРѕС‡РєР° РєРѕР»Р±СЌРєРѕРІ Р±С‹Р»Р° РїСЂРµСЂРІР°РЅР°.
        """
        if self._auth_inflight:
            tglog("[AUTH] inflight safety reset action=login")
            self._auth_inflight = False
        self._auth_inflight_reset_ev = None

    def _clear_auth_inflight(self) -> None:
        """EN: Clear in-flight state after auth request completion.
        RU: РЎР±СЂРѕСЃРёС‚СЊ СЃРѕСЃС‚РѕСЏРЅРёРµ in-flight РїРѕСЃР»Рµ Р·Р°РІРµСЂС€РµРЅРёСЏ auth-Р·Р°РїСЂРѕСЃР°.
        """
        if self._auth_inflight_reset_ev is not None:
            self._auth_inflight_reset_ev.cancel()
            self._auth_inflight_reset_ev = None
        self._auth_inflight = False

    def set_error(self, text: str) -> None:
        """EN: Set error text visibility.
        RU: РЈСЃС‚Р°РЅРѕРІРёС‚СЊ РІРёРґРёРјРѕСЃС‚СЊ С‚РµРєСЃС‚Р° РѕС€РёР±РєРё.
        """
        self.ids.error_lbl.text = text
        self.ids.error_lbl.opacity = 1 if text else 0

    def _clear_fields(self) -> None:
        """EN: Clear login input fields after successful validation.
        RU: РћС‡РёСЃС‚РёС‚СЊ РїРѕР»СЏ РІС…РѕРґР° РїРѕСЃР»Рµ СѓСЃРїРµС€РЅРѕР№ РїСЂРѕРІРµСЂРєРё.
        """
        self.ids.email_field.text = ""
        self.ids.password_field.text = ""

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

