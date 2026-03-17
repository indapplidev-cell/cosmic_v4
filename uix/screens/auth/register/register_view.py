"""EN: View for the register screen.
RU: РџСЂРµРґСЃС‚Р°РІР»РµРЅРёРµ СЌРєСЂР°РЅР° СЂРµРіРёСЃС‚СЂР°С†РёРё.
"""

from pathlib import Path

from manager import auth_backend
from manager.input_validation import validate_register
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.utils import platform as kivy_platform
from kivymd.uix.screen import MDScreen
from manager.auth.logup_manager import LogupManager
from manager.lang.lang_manager import t
from manager.tg_debug_log import tglog
from uix.debug.debug_borders import apply_debug_borders_to_ids
from uix.screens.common.button_text_style import apply_button_text_style, caps
from uix.screens.common.password_eye import wire_password_eye
from uix.screens.common.input_focus import blur_inputs_on_screen_enter

from .register_controller import RegisterController
from .register_layout import REGISTER_DEBUG_IDS, apply_register_layout
from .register_vm import RegisterVM

KV_PATH = Path(__file__).with_name("register.kv")
Builder.load_file(str(KV_PATH))


class RegisterScreenView(MDScreen):
    """EN: Register screen view that wires layout, VM, and controller.
    RU: РџСЂРµРґСЃС‚Р°РІР»РµРЅРёРµ СЂРµРіРёСЃС‚СЂР°С†РёРё, СЃРІСЏР·С‹РІР°СЋС‰РµРµ СЂР°СЃРєР»Р°РґРєСѓ, VM Рё РєРѕРЅС‚СЂРѕР»Р»РµСЂ.
    """

    def __init__(self, **kwargs) -> None:
        """EN: Initialize register view state for duplicate-click protection.
        RU: РРЅРёС†РёР°Р»РёР·РёСЂРѕРІР°С‚СЊ СЃРѕСЃС‚РѕСЏРЅРёРµ СЌРєСЂР°РЅР° СЂРµРіРёСЃС‚СЂР°С†РёРё РґР»СЏ Р·Р°С‰РёС‚С‹ РѕС‚ РґРІРѕР№РЅС‹С… РєР»РёРєРѕРІ.

        EN: The in-flight flag blocks repeated taps while the register request is being processed.
        RU: Р¤Р»Р°Рі in-flight Р±Р»РѕРєРёСЂСѓРµС‚ РїРѕРІС‚РѕСЂРЅС‹Рµ РЅР°Р¶Р°С‚РёСЏ, РїРѕРєР° РѕР±СЂР°Р±Р°С‚С‹РІР°РµС‚СЃСЏ Р·Р°РїСЂРѕСЃ СЂРµРіРёСЃС‚СЂР°С†РёРё.
        """
        super().__init__(**kwargs)
        self._auth_inflight = False
        self._auth_inflight_reset_ev = None

    def on_kv_post(self, base_widget) -> None:
        """EN: Apply layout after KV is ready.
        RU: РџСЂРёРјРµРЅРёС‚СЊ СЂР°СЃРєР»Р°РґРєСѓ РїРѕСЃР»Рµ Р·Р°РіСЂСѓР·РєРё KV.
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
        self._ids_keepalive = dict(self.ids)
        for _key, _widget in self._ids_keepalive.items():
            self.ids[_key] = _widget
        self._contentbar_widget = getattr(self.ids.contentbar, "__self__", self.ids.contentbar)
        self._bottombar_widget = getattr(self.ids.bottombar, "__self__", self.ids.bottombar)

    def configure(self, vm: RegisterVM, controller: RegisterController) -> None:
        """EN: Configure texts and bind callbacks.
        RU: РќР°СЃС‚СЂРѕРёС‚СЊ С‚РµРєСЃС‚С‹ Рё РїСЂРёРІСЏР·Р°С‚СЊ РєРѕР»Р±СЌРєРё.
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

        self._to_login_callback = lambda *_: controller.to_login()
        self.ids.create_btn.unbind(on_release=self._on_create_pressed)
        self.ids.create_btn.bind(on_release=self._on_create_pressed)
        self.ids.to_login_btn.unbind(on_release=self._to_login_callback)
        self.ids.to_login_btn.bind(on_release=self._to_login_callback)

    def _wire_widgets(self) -> None:
        """EN: Cache field widgets for validation and focus control.
        RU: РЎРѕС…СЂР°РЅРёС‚СЊ СЃСЃС‹Р»РєРё РЅР° РїРѕР»СЏ РґР»СЏ РІР°Р»РёРґР°С†РёРё Рё СѓРїСЂР°РІР»РµРЅРёСЏ С„РѕРєСѓСЃРѕРј.
        """
        self.email_field = self.ids.register_email_field
        self.password_field = self.ids.register_password_field
        self.password2_field = self.ids.register_password2_field

    def on_pre_enter(self, *args) -> None:
        """EN: Clear automatic input focus before showing the register screen.
        RU: ????? ?????????????? ????? ? ????? ????? ????? ??????? ?????? ???????????.
        """
        super().on_pre_enter(*args)
        blur_inputs_on_screen_enter(self)

    def _on_create_pressed(self, *args) -> None:
        """EN: Validate registration data, save cache, and dispatch create action.
        RU: РџСЂРѕРІРµСЂРёС‚СЊ РґР°РЅРЅС‹Рµ СЂРµРіРёСЃС‚СЂР°С†РёРё, СЃРѕС…СЂР°РЅРёС‚СЊ РєСЌС€ Рё РїРµСЂРµР№С‚Рё Рє СЃРѕР·РґР°РЅРёСЋ.
        """
        if self._auth_inflight:
            tglog("[AUTH] drop duplicate click action=register")
            return
        self._auth_inflight = True
        self._auth_inflight_reset_ev = Clock.schedule_once(self._reset_auth_inflight_safety, 3)

        email = (self.email_field.text or "").strip()
        password = (self.password_field.text or "").strip()
        password2 = (self.password2_field.text or "").strip()
        try:
            ok, message, focus_field = LogupManager.validate(email, password, password2)
            if not ok:
                self._show_error_popup(message, focus_field)
                return
            ok_input, error_code, input_field = validate_register(email, password)
            if not ok_input:
                msg_map = {
                    "EMAIL_FORMAT": "Invalid email format / РќРµРІРµСЂРЅС‹Р№ С„РѕСЂРјР°С‚ email",
                    "PASSWORD_LENGTH": "Password length must be 8..72 / Р”Р»РёРЅР° РїР°СЂРѕР»СЏ РґРѕР»Р¶РЅР° Р±С‹С‚СЊ 8..72",
                    "CONTROL_CHARS": "Password contains forbidden chars / РџР°СЂРѕР»СЊ СЃРѕРґРµСЂР¶РёС‚ Р·Р°РїСЂРµС‰С‘РЅРЅС‹Рµ СЃРёРјРІРѕР»С‹",
                }
                self._show_error_popup(msg_map.get(error_code, "Invalid input / РќРµРєРѕСЂСЂРµРєС‚РЅС‹Р№ РІРІРѕРґ"), input_field)
                return

            ok_register, payload = auth_backend.register(email, password)
            if not ok_register:
                if payload == "EMAIL_EXISTS":
                    self._show_error_popup("Email already exists / РўР°РєРѕР№ email СѓР¶Рµ Р·Р°СЂРµРіРёСЃС‚СЂРёСЂРѕРІР°РЅ", "email")
                elif payload == "DB_SCHEMA_OUTDATED":
                    self._show_error_popup("Server DB migration required / РќСѓР¶РЅР° РјРёРіСЂР°С†РёСЏ Р‘Р” РЅР° СЃРµСЂРІРµСЂРµ", "email")
                elif payload == "NETWORK":
                    self._show_error_popup("Network error / РћС€РёР±РєР° СЃРµС‚Рё", "email")
                else:
                    self._show_error_popup("Registration failed / РћС€РёР±РєР° СЂРµРіРёСЃС‚СЂР°С†РёРё", "email")
                return

            self._clear_fields()
            self.controller.create()
        finally:
            self._clear_auth_inflight()

    def _reset_auth_inflight_safety(self, _dt: float) -> None:
        """EN: Safety reset for in-flight register flag in case callback chain is interrupted.
        RU: Р—Р°С‰РёС‚РЅС‹Р№ СЃР±СЂРѕСЃ С„Р»Р°РіР° in-flight СЂРµРіРёСЃС‚СЂР°С†РёРё, РµСЃР»Рё С†РµРїРѕС‡РєР° РєРѕР»Р±СЌРєРѕРІ Р±С‹Р»Р° РїСЂРµСЂРІР°РЅР°.
        """
        if self._auth_inflight:
            tglog("[AUTH] inflight safety reset action=register")
            self._auth_inflight = False
        self._auth_inflight_reset_ev = None

    def _clear_auth_inflight(self) -> None:
        """EN: Clear in-flight state after register request completion.
        RU: РЎР±СЂРѕСЃРёС‚СЊ СЃРѕСЃС‚РѕСЏРЅРёРµ in-flight РїРѕСЃР»Рµ Р·Р°РІРµСЂС€РµРЅРёСЏ Р·Р°РїСЂРѕСЃР° СЂРµРіРёСЃС‚СЂР°С†РёРё.
        """
        if self._auth_inflight_reset_ev is not None:
            self._auth_inflight_reset_ev.cancel()
            self._auth_inflight_reset_ev = None
        self._auth_inflight = False

    def _show_error_popup(self, message: str, focus_field: str) -> None:
        """EN: Show validation error popup and set focus after closing.
        RU: РџРѕРєР°Р·Р°С‚СЊ РїРѕРїР°Рї СЃ РѕС€РёР±РєРѕР№ Рё РІРµСЂРЅСѓС‚СЊ С„РѕРєСѓСЃ РїРѕСЃР»Рµ Р·Р°РєСЂС‹С‚РёСЏ.
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
        RU: РЈСЃС‚Р°РЅРѕРІРёС‚СЊ С„РѕРєСѓСЃ РЅР° РїРѕР»Рµ РїРѕ РєР»СЋС‡Сѓ РІР°Р»РёРґР°С†РёРё.
        """
        mapping = {
            "email": self.email_field,
            "password": self.password_field,
            "password2": self.password2_field,
        }
        target = mapping.get(focus_field)
        if target is not None:
            if kivy_platform in ("android", "ios"):
                return
            target.focus = True
            try:
                target.select_all()
            except Exception:
                pass

    def _clear_fields(self) -> None:
        """EN: Clear registration input fields after successful validation.
        RU: РћС‡РёСЃС‚РёС‚СЊ РїРѕР»СЏ СЂРµРіРёСЃС‚СЂР°С†РёРё РїРѕСЃР»Рµ СѓСЃРїРµС€РЅРѕР№ РїСЂРѕРІРµСЂРєРё.
        """
        self.email_field.text = ""
        self.password_field.text = ""
        self.password2_field.text = ""

    def set_error(self, text: str) -> None:
        """EN: Set error text visibility.
        RU: РЈСЃС‚Р°РЅРѕРІРёС‚СЊ РІРёРґРёРјРѕСЃС‚СЊ С‚РµРєСЃС‚Р° РѕС€РёР±РєРё.
        """
        self.ids.error_lbl.text = text
        self.ids.error_lbl.opacity = 1 if text else 0

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

