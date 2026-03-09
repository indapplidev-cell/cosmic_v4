"""EN: Controller for profile change screen actions.
RU: РљРѕРЅС‚СЂРѕР»Р»РµСЂ РґРµР№СЃС‚РІРёР№ СЌРєСЂР°РЅР° СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ РїСЂРѕС„РёР»СЏ.
"""

from __future__ import annotations

from threading import Thread
from time import monotonic, sleep

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivymd.app import MDApp
from manager import api_client, auth_backend
from manager.config import TELEGRAM_BOT_USERNAME
from manager.telegram_deeplink import open_telegram_chat
from data.user_cache.user_cache_reader import get_user_cache
from manager.lang.lang_manager import t

from data.format.phone import attach_phone_mask, format_phone, normalize_phone
from manager.profile_change.profile_change_manager import ProfileChangeManager
from uix.screens.common.password_eye import wire_password_eye
from uix.screens.common.bottom_bar_buttons import apply_bottom_buttons
from uix.screens.layouts.layout_constants import ZONE_SPACING
from uix.screens.routes import PROFILE


class ProfileChangeController:
    """EN: Handle profile change actions and navigation.
    RU: РћР±СЂР°Р±Р°С‚С‹РІР°С‚СЊ РґРµР№СЃС‚РІРёСЏ СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ РїСЂРѕС„РёР»СЏ Рё РЅР°РІРёРіР°С†РёСЋ.
    """

    def __init__(self) -> None:
        """EN: Initialize manager and app reference for data changes and routing.
        RU: РРЅРёС†РёР°Р»РёР·РёСЂРѕРІР°С‚СЊ РјРµРЅРµРґР¶РµСЂ Рё СЃСЃС‹Р»РєСѓ РЅР° РїСЂРёР»РѕР¶РµРЅРёРµ РґР»СЏ РёР·РјРµРЅРµРЅРёР№ РґР°РЅРЅС‹С… Рё СЂРѕСѓС‚РёРЅРіР°.
        """
        self._manager = ProfileChangeManager()
        self._app = MDApp.get_running_app()
        self._tg_instruction_popup: Popup | None = None

    def bind(self, view) -> None:
        """EN: Bind bottom buttons, styles, and handlers for edit/delete/back actions.
        RU: РџСЂРёРІСЏР·Р°С‚СЊ РЅРёР¶РЅРёРµ РєРЅРѕРїРєРё, СЃС‚РёР»Рё Рё РѕР±СЂР°Р±РѕС‚С‡РёРєРё РґР»СЏ РґРµР№СЃС‚РІРёР№ РёР·РјРµРЅРёС‚СЊ/СѓРґР°Р»РёС‚СЊ/РЅР°Р·Р°Рґ.
        """
        self._view = view
        ids = view.ids
        apply_bottom_buttons(
            bottombar=ids.bottombar,
            bottom_center=ids.bottom_center,
            btn_stack=ids.btn_stack,
            buttons=[ids.ok_btn, ids.delete_btn, ids.back_btn],
            spacing_dp=dp(ZONE_SPACING),
            width_ratio=0.5,
        )
        ids.ok_btn.style = "elevated"
        ids.delete_btn.style = "outlined"
        ids.back_btn.style = "outlined"
        ids.ok_btn.on_release = self.on_ok
        ids.delete_btn.on_release = self.on_delete
        ids.back_btn.on_release = self.on_back
        attach_phone_mask(ids.inp_phone)
        wire_password_eye(ids.inp_password, ids.edit_password_eye_btn, start_hidden=True)

    def on_enter(self, view) -> None:
        """EN: Prefill fields from cache and show session email in right top bar.
        RU: РџСЂРµРґР·Р°РїРѕР»РЅРёС‚СЊ РїРѕР»СЏ РёР· РєСЌС€Р° Рё РїРѕРєР°Р·Р°С‚СЊ email СЃРµСЃСЃРёРё РІ right top bar.
        """
        no_data = t("common.no_data")
        current = self._manager.load_current_user_data()
        view.ids.inp_login.text = "" if current.get("login") == no_data else current.get("login", "")
        view.ids.inp_email.text = "" if current.get("email") == no_data else current.get("email", "")
        raw_phone = current.get("phone", "")
        view.ids.inp_phone.text = "" if raw_phone == no_data else format_phone(normalize_phone(raw_phone))
        view.ids.inp_tg.text = "" if current.get("tg") == no_data else current.get("tg", "")
        view.ids.inp_password.text = "" if current.get("password") == no_data else current.get("password", "")
        login = (current.get("login") or "").strip()
        view.right_text = login if login else no_data

    def on_ok(self) -> None:
        """EN: Apply selected non-empty edits, keep user on the same screen, and show success popup.
        RU: РџСЂРёРјРµРЅРёС‚СЊ РІС‹Р±СЂР°РЅРЅС‹Рµ РЅРµРїСѓСЃС‚С‹Рµ РёР·РјРµРЅРµРЅРёСЏ, РѕСЃС‚Р°РІРёС‚СЊ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ РЅР° С‚РµРєСѓС‰РµРј СЌРєСЂР°РЅРµ Рё РїРѕРєР°Р·Р°С‚СЊ popup РѕР± СѓСЃРїРµС…Рµ.
        """
        view = self._view
        changes = {}
        if view.ids.chk_login.active and view.ids.inp_login.text.strip():
            changes["login"] = view.ids.inp_login.text.strip()
        if view.ids.chk_email.active and view.ids.inp_email.text.strip():
            changes["email"] = view.ids.inp_email.text.strip()
        if view.ids.chk_phone.active and view.ids.inp_phone.text.strip():
            phone_digits = normalize_phone(view.ids.inp_phone.text)
            if phone_digits:
                changes["phone"] = phone_digits
        if view.ids.chk_tg.active and view.ids.inp_tg.text.strip():
            changes["tg"] = view.ids.inp_tg.text.strip()
        if view.ids.chk_password.active and view.ids.inp_password.text.strip():
            changes["password"] = view.ids.inp_password.text.strip()
        if not changes:
            return
        if view.ids.chk_tg.active:
            self._show_tg_verify_ask_popup(changes)
            return
        self._apply_changes_and_show_result(changes)

    def _apply_changes_and_show_result(self, changes: dict) -> bool:
        """EN: Apply prepared patch, show validation popup on failure, and success popup on success.
        RU: РџСЂРёРјРµРЅРёС‚СЊ РїРѕРґРіРѕС‚РѕРІР»РµРЅРЅС‹Р№ patch, РїРѕРєР°Р·Р°С‚СЊ popup РІР°Р»РёРґР°С†РёРё РїСЂРё РѕС€РёР±РєРµ Рё popup СѓСЃРїРµС…Р° РїСЂРё СѓСЃРїРµС…Рµ.
        """

        result = self._manager.apply_patch(changes)
        if not result.get("ok"):
            field = str(result.get("field") or "field")
            error = str(result.get("error") or "FORMAT")
            msg_map = {
                "CONTROL_CHARS": f"Forbidden control characters in {field} / Р—Р°РїСЂРµС‰С‘РЅРЅС‹Рµ СЃРёРјРІРѕР»С‹ РІ РїРѕР»Рµ {field}",
                "CODE_LIKE": f"Code-like payload in {field} is forbidden / Code-like payload РІ РїРѕР»Рµ {field} Р·Р°РїСЂРµС‰С‘РЅ",
                "FORMAT": f"Invalid format for {field} / РќРµРІРµСЂРЅС‹Р№ С„РѕСЂРјР°С‚ РїРѕР»СЏ {field}",
            }
            self._show_popup(msg_map.get(error, f"Invalid input for {field} / РќРµРєРѕСЂСЂРµРєС‚РЅС‹Р№ РІРІРѕРґ РІ РїРѕР»Рµ {field}"))
            return False
        self._refresh_right_login()
        self._show_changed_popup()
        return True

    def _show_tg_verify_ask_popup(self, changes: dict) -> None:
        """EN: Ask user whether Telegram verification flow should start for checked Telegram update.
        RU: РЎРїСЂРѕСЃРёС‚СЊ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ, РЅСѓР¶РЅРѕ Р»Рё Р·Р°РїСѓСЃРєР°С‚СЊ РїРѕС‚РѕРє РІРµСЂРёС„РёРєР°С†РёРё Telegram РґР»СЏ РѕС‚РјРµС‡РµРЅРЅРѕРіРѕ РѕР±РЅРѕРІР»РµРЅРёСЏ Telegram.
        """

        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        content.add_widget(Label(text=t("tg.verify.ask")))
        buttons = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=dp(40))
        ok_btn = Button(text=t("common.ok"))
        back_btn = Button(text=t("common.back"))
        buttons.add_widget(ok_btn)
        buttons.add_widget(back_btn)
        content.add_widget(buttons)
        popup = Popup(title="", content=content, size_hint=(0.8, 0.4), auto_dismiss=False)

        def _on_back(_instance) -> None:
            self._uncheck_tg_checkbox()
            popup.dismiss()

        def _on_ok(_instance) -> None:
            self._uncheck_tg_checkbox()
            popup.dismiss()
            self._start_tg_verify_flow(changes)

        ok_btn.bind(on_release=_on_ok)
        back_btn.bind(on_release=_on_back)
        popup.open()

    def _start_tg_verify_flow(self, changes: dict) -> None:
        """EN: Save changes, request Telegram deep-link token, open bot chat, then start polling.
        RU: РЎРѕС…СЂР°РЅРёС‚СЊ РёР·РјРµРЅРµРЅРёСЏ, Р·Р°РїСЂРѕСЃРёС‚СЊ Telegram deep-link С‚РѕРєРµРЅ, РѕС‚РєСЂС‹С‚СЊ С‡Р°С‚ СЃ Р±РѕС‚РѕРј Рё Р·Р°РїСѓСЃС‚РёС‚СЊ polling.
        """
        def _worker() -> None:
            result = self._manager.apply_patch(changes)
            if not result.get("ok"):
                field = str(result.get("field") or "field")
                error = str(result.get("error") or "FORMAT")
                msg_map = {
                    "CONTROL_CHARS": f"Forbidden control characters in {field} / Р—Р°РїСЂРµС‰С‘РЅРЅС‹Рµ СЃРёРјРІРѕР»С‹ РІ РїРѕР»Рµ {field}",
                    "CODE_LIKE": f"Code-like payload in {field} is forbidden / Code-like payload РІ РїРѕР»Рµ {field} Р·Р°РїСЂРµС‰С‘РЅ",
                    "FORMAT": f"Invalid format for {field} / РќРµРІРµСЂРЅС‹Р№ С„РѕСЂРјР°С‚ РїРѕР»СЏ {field}",
                }
                text = msg_map.get(error, f"Invalid input for {field} / РќРµРєРѕСЂСЂРµРєС‚РЅС‹Р№ РІРІРѕРґ РІ РїРѕР»Рµ {field}")
                Clock.schedule_once(lambda *_: self._show_popup(text), 0)
                Clock.schedule_once(lambda *_: self._uncheck_tg_checkbox(), 0)
                return

            user_id = self._resolve_user_id_from_cache()
            if user_id <= 0:
                Clock.schedule_once(lambda *_: self._show_tg_fail_popup(), 0)
                return

            if not self._ensure_server_telegram(user_id=user_id, changes=changes):
                Clock.schedule_once(lambda *_: self._show_tg_fail_popup(), 0)
                return

            ok, payload = auth_backend.telegram_link_request(user_id=user_id)
            if not ok:
                Clock.schedule_once(lambda *_: self._show_tg_fail_popup(), 0)
                return

            start_token = str((payload.get("start_token") or "").strip())
            if not start_token:
                Clock.schedule_once(lambda *_: self._show_tg_fail_popup(), 0)
                return

            def _continue(_dt) -> None:
                self._refresh_right_login()
                if not open_telegram_chat(TELEGRAM_BOT_USERNAME, start_token):
                    self._show_popup(t("tg.open_fail"))
                    self._show_tg_fail_popup()
                    return
                self._show_tg_instruction_popup()
                self._start_tg_polling(user_id=user_id)

            Clock.schedule_once(_continue, 0)

        Thread(target=_worker, daemon=True).start()

    def _ensure_server_telegram(self, user_id: int, changes: dict) -> bool:
        """EN: Ensure Telegram handle is persisted in server profile before verify request.
        RU: РЈР±РµРґРёС‚СЊСЃСЏ, С‡С‚Рѕ Telegram-РЅРёРє СЃРѕС…СЂР°РЅС‘РЅ РІ РїСЂРѕС„РёР»Рµ РЅР° СЃРµСЂРІРµСЂРµ РґРѕ Р·Р°РїСЂРѕСЃР° verify.
        """

        tg_value = str((changes.get("tg") or "").strip())
        if not tg_value:
            return False
        ok, payload = api_client.request(
            "POST",
            "/profile/user/update",
            json={"user_id": int(user_id), "telegram": tg_value},
            timeout=10,
        )
        return bool(ok and isinstance(payload, dict) and payload.get("ok"))

    def _show_tg_instruction_popup(self) -> None:
        """EN: Show instructions after Telegram app open attempt.
        RU: РџРѕРєР°Р·Р°С‚СЊ РёРЅСЃС‚СЂСѓРєС†РёСЋ РїРѕСЃР»Рµ РїРѕРїС‹С‚РєРё РѕС‚РєСЂС‹С‚СЊ РїСЂРёР»РѕР¶РµРЅРёРµ Telegram.
        """

        text = f"{t('tg.opening')}\n\n{t('tg.instruction')}"
        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        content.add_widget(Label(text=text))
        ok_btn = Button(text=t("common.ok"), size_hint_y=None, height=dp(40))
        content.add_widget(ok_btn)
        popup = Popup(title="", content=content, size_hint=(0.9, 0.45), auto_dismiss=False)

        def _on_ok(_instance) -> None:
            self._uncheck_tg_checkbox()
            popup.dismiss()

        ok_btn.bind(on_release=_on_ok)
        self._tg_instruction_popup = popup
        popup.open()


    def _start_tg_polling(self, user_id: int) -> None:
        """EN: Poll server snapshot until telegram_verified becomes true or timeout/network error happens.
        RU: РћРїСЂРѕСЃРёС‚СЊ snapshot СЃРµСЂРІРµСЂР°, РїРѕРєР° telegram_verified РЅРµ СЃС‚Р°РЅРµС‚ true, Р»РёР±Рѕ РЅРµ СЃР»СѓС‡РёС‚СЃСЏ С‚Р°Р№РјР°СѓС‚/СЃРµС‚РµРІР°СЏ РѕС€РёР±РєР°.
        """

        poll_interval_sec = 2.0
        timeout_sec = 60.0

        def _worker() -> None:
            started = monotonic()
            while monotonic() - started < timeout_sec:
                ok, payload = api_client.get_me(user_id=user_id, timeout=8)
                if not ok or not isinstance(payload, dict) or not payload.get("ok"):
                    Clock.schedule_once(lambda *_: self._show_tg_fail_popup(), 0)
                    return
                user_payload = payload.get("user") if isinstance(payload, dict) else None
                if isinstance(user_payload, dict) and bool(user_payload.get("telegram_verified")):
                    Clock.schedule_once(lambda *_: self._on_tg_verify_success(), 0)
                    return
                sleep(poll_interval_sec)
            Clock.schedule_once(lambda *_: self._show_tg_fail_popup(), 0)

        Thread(target=_worker, daemon=True).start()

    def _on_tg_verify_success(self) -> None:
        """EN: Handle successful Telegram verification by closing instruction popup and showing standard success popup.
        RU: РћР±СЂР°Р±РѕС‚Р°С‚СЊ СѓСЃРїРµС€РЅСѓСЋ РІРµСЂРёС„РёРєР°С†РёСЋ Telegram: Р·Р°РєСЂС‹С‚СЊ popup-РёРЅСЃС‚СЂСѓРєС†РёСЋ Рё РїРѕРєР°Р·Р°С‚СЊ СЃС‚Р°РЅРґР°СЂС‚РЅС‹Р№ popup СѓСЃРїРµС…Р°.
        """

        if self._tg_instruction_popup is not None:
            try:
                self._tg_instruction_popup.dismiss()
            except Exception:
                pass
        self._tg_instruction_popup = None
        self._show_changed_popup()

    def _show_tg_fail_popup(self) -> None:
        """EN: Show Telegram verification failure popup and uncheck Telegram checkbox after close.
        RU: РџРѕРєР°Р·Р°С‚СЊ popup РѕС€РёР±РєРё РІРµСЂРёС„РёРєР°С†РёРё Telegram Рё СЃРЅСЏС‚СЊ С‡РµРєР±РѕРєСЃ Telegram РїРѕСЃР»Рµ Р·Р°РєСЂС‹С‚РёСЏ.
        """

        if self._tg_instruction_popup is not None:
            try:
                self._tg_instruction_popup.dismiss()
            except Exception:
                pass
        self._tg_instruction_popup = None

        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        content.add_widget(Label(text=t("tg_verify.fail")))
        ok_btn = Button(text=t("common.ok"), size_hint_y=None, height=dp(40))
        content.add_widget(ok_btn)
        popup = Popup(title="", content=content, size_hint=(0.8, 0.4), auto_dismiss=False)

        def _on_ok(_instance) -> None:
            self._uncheck_tg_checkbox()
            popup.dismiss()

        ok_btn.bind(on_release=_on_ok)
        popup.open()

    def _resolve_user_id_from_cache(self) -> int:
        """EN: Resolve numeric user_id from cache for Telegram verification requests.
        RU: РџРѕР»СѓС‡РёС‚СЊ С‡РёСЃР»РѕРІРѕР№ user_id РёР· РєСЌС€Р° РґР»СЏ Р·Р°РїСЂРѕСЃРѕРІ РІРµСЂРёС„РёРєР°С†РёРё Telegram.
        """

        cache = get_user_cache() or {}
        try:
            return int(cache.get("user_id") or 0)
        except Exception:
            return 0

    def _uncheck_tg_checkbox(self) -> None:
        """EN: Force Telegram checkbox into unchecked state.
        RU: РџСЂРёРЅСѓРґРёС‚РµР»СЊРЅРѕ СЃРЅСЏС‚СЊ РіР°Р»РѕС‡РєСѓ С‡РµРєР±РѕРєСЃР° Telegram.
        """

        if self._view is None:
            return
        checkbox = self._view.ids.get("chk_tg")
        if checkbox is not None:
            checkbox.active = False

    def on_delete(self) -> None:
        """EN: Clear selected allowed fields (login/phone/tg), block email/password deletion, and show popups.
        RU: РћС‡РёСЃС‚РёС‚СЊ РІС‹Р±СЂР°РЅРЅС‹Рµ СЂР°Р·СЂРµС€РµРЅРЅС‹Рµ РїРѕР»СЏ (login/phone/tg), Р·Р°РїСЂРµС‚РёС‚СЊ СѓРґР°Р»РµРЅРёРµ email/password Рё РїРѕРєР°Р·Р°С‚СЊ popup.
        """
        view = self._view
        delete_patch = {}
        if view.ids.chk_login.active:
            delete_patch["login"] = ""
        if view.ids.chk_phone.active:
            delete_patch["phone"] = ""
        if view.ids.chk_tg.active:
            delete_patch["tg"] = ""

        blocked_selected = view.ids.chk_email.active or view.ids.chk_password.active
        if blocked_selected:
            self._show_popup(t("profile_change.popup.delete_forbidden"))
            if not delete_patch:
                return

        if not delete_patch:
            return

        self._manager.apply_patch(delete_patch)
        if "login" in delete_patch:
            view.ids.inp_login.text = ""
        if "phone" in delete_patch:
            view.ids.inp_phone.text = ""
        if "tg" in delete_patch:
            view.ids.inp_tg.text = ""
        self._refresh_right_login()
        self._show_changed_popup()

    def on_back(self) -> None:
        """EN: Clear edit fields and return to profile screen without extra refresh hooks.
        RU: РћС‡РёСЃС‚РёС‚СЊ РїРѕР»СЏ СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ Рё РІРµСЂРЅСѓС‚СЊСЃСЏ РЅР° СЌРєСЂР°РЅ РїСЂРѕС„РёР»СЏ Р±РµР· РґРѕРїРѕР»РЅРёС‚РµР»СЊРЅС‹С… С„РѕСЂСЃ-РѕР±РЅРѕРІР»РµРЅРёР№.
        """
        if self._tg_instruction_popup is not None:
            try:
                self._tg_instruction_popup.dismiss()
            except Exception:
                pass
        self._tg_instruction_popup = None
        view = self._view
        view.ids.inp_login.text = ""
        view.ids.inp_email.text = ""
        view.ids.inp_phone.text = ""
        view.ids.inp_tg.text = ""
        view.ids.inp_password.text = ""
        self._app.change_screen(PROFILE)

    def _refresh_right_login(self) -> None:
        """EN: Reload current cache and update right top text with login or localized no-data fallback.
        RU: РџРµСЂРµС‡РёС‚Р°С‚СЊ С‚РµРєСѓС‰РёР№ РєСЌС€ Рё РѕР±РЅРѕРІРёС‚СЊ right top С‚РµРєСЃС‚ Р»РѕРіРёРЅРѕРј РёР»Рё Р»РѕРєР°Р»РёР·РѕРІР°РЅРЅС‹Рј fallback no-data.
        """
        current = self._manager.load_current_user_data() or {}
        login_val = (current.get("login") or "").strip()
        self._view.right_text = login_val if login_val else t("common.no_data")

    def _show_popup(self, message: str) -> None:
        """EN: Show modal popup with a message and one OK button, matching register popup style.
        RU: РџРѕРєР°Р·Р°С‚СЊ РјРѕРґР°Р»СЊРЅС‹Р№ popup СЃ СЃРѕРѕР±С‰РµРЅРёРµРј Рё РѕРґРЅРѕР№ РєРЅРѕРїРєРѕР№ OK РІ СЃС‚РёР»Рµ popup СЌРєСЂР°РЅР° СЂРµРіРёСЃС‚СЂР°С†РёРё.
        """
        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        content.add_widget(Label(text=message))
        ok_btn = Button(text=t("common.ok"), size_hint_y=None, height=dp(40))
        content.add_widget(ok_btn)

        popup = Popup(title="", content=content, size_hint=(0.8, 0.4), auto_dismiss=False)
        ok_btn.bind(on_release=lambda _instance: popup.dismiss())
        popup.open()

    def _show_changed_popup(self) -> None:
        """EN: Show changed-data popup and reset all edit checkboxes after clicking OK.
        RU: РџРѕРєР°Р·Р°С‚СЊ popup РѕР± РёР·РјРµРЅРµРЅРёРё РґР°РЅРЅС‹С… Рё СЃР±СЂРѕСЃРёС‚СЊ РІСЃРµ С‡РµРєР±РѕРєСЃС‹ СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ РїРѕСЃР»Рµ РЅР°Р¶Р°С‚РёСЏ OK.
        """
        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        content.add_widget(Label(text=t("profile_change.popup.changed")))
        ok_btn = Button(text=t("common.ok"), size_hint_y=None, height=dp(40))
        content.add_widget(ok_btn)

        popup = Popup(title="", content=content, size_hint=(0.8, 0.4), auto_dismiss=False)

        def _on_ok(_instance) -> None:
            self._reset_edit_checkboxes()
            popup.dismiss()

        ok_btn.bind(on_release=_on_ok)
        popup.open()

    def _reset_edit_checkboxes(self) -> None:
        """EN: Clear all profile-change edit checkboxes.
        RU: РЎРЅСЏС‚СЊ РІСЃРµ С‡РµРєР±РѕРєСЃС‹ СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ РЅР° СЌРєСЂР°РЅРµ РёР·РјРµРЅРµРЅРёСЏ РїСЂРѕС„РёР»СЏ.
        """
        ids = self._view.ids
        for name in ("chk_login", "chk_email", "chk_phone", "chk_tg", "chk_password"):
            cb = ids.get(name)
            if cb is not None:
                cb.active = False

    def attach_view(self, view) -> None:
        """EN: Attach view reference for handlers and helper methods.
        RU: РџРѕРґРєР»СЋС‡РёС‚СЊ СЃСЃС‹Р»РєСѓ РЅР° view РґР»СЏ РѕР±СЂР°Р±РѕС‚С‡РёРєРѕРІ Рё РІСЃРїРѕРјРѕРіР°С‚РµР»СЊРЅС‹С… РјРµС‚РѕРґРѕРІ.
        """
        self._view = view
