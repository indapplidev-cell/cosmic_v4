"""EN: Controller for profile change screen actions.
RU: РљРѕРЅС‚СЂРѕР»Р»РµСЂ РґРµР№СЃС‚РІРёР№ СЌРєСЂР°РЅР° СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ РїСЂРѕС„РёР»СЏ.
"""

from __future__ import annotations

import logging
from threading import Thread
from time import monotonic

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivymd.app import MDApp
from manager import auth_backend
from manager.config import TG_DEBUG_FLOW, TELEGRAM_BOT_USERNAME, TG_VERIFY_TIMEOUT_SEC
from manager.telegram_deeplink import cancel_open_flow, open_bot_two_stage
from manager.trace import trace_exception, trace_log
from manager.lang.lang_manager import t, user_value_text
from manager.session_manager import sync_user_snapshot_from_payload
from manager.tg_debug_log import tglog

from data.format.phone import attach_phone_mask, format_phone, normalize_phone
from manager.profile_change.profile_change_manager import ProfileChangeManager
from uix.screens.common.bottom_bar_buttons import apply_bottom_buttons
from uix.screens.layouts.layout_constants import ZONE_SPACING
from uix.screens.routes import LOGIN, PROFILE

_LOG = logging.getLogger("cosmic.profile_change.telegram")


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
        self._tg_verify_active = False
        self._tg_verify_started_at = 0.0
        self._tg_open_fallback_scheduled = False
        self._tg_verify_timeout_event = None
        self._tg_verify_poll_event = None
        self._tg_open_attempted = False
        self._tg_open_started_at = 0.0
        self._tg_urls: tuple[str, str] = ("", "")
        self._tg_fallback_ev = None

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
        ids.inp_tg.bind(focus=self._on_tg_input_focus)
        ids.chk_tg.bind(active=self._on_tg_checkbox_active)
        attach_phone_mask(ids.inp_phone)

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
        view.right_text = user_value_text(current.get("login"))

    def _on_tg_input_focus(self, widget, focused: bool) -> None:
        """EN: Log Telegram input value when focus leaves the field.
        RU: Логировать значение Telegram-поля при потере фокуса.
        """

        if focused:
            return
        value = str((widget.text or "").strip())
        tglog(f"[TGDBG] step1 telegram_input text='{value}'")
        trace_log("UI", "UI.INPUT_CHANGED", field="telegram", text=value, text_len=len(value))

    def _on_tg_checkbox_active(self, _widget, active: bool) -> None:
        """EN: Log Telegram checkbox state changes.
        RU: Логировать изменения состояния чекбокса Telegram.
        """

        tglog(f"[TGDBG] step2 telegram_checkbox active={bool(active)}")
        trace_log("UI", "UI.CHECKBOX_TOGGLE", field="telegram", active=bool(active))

    def on_ok(self) -> None:
        """EN: Apply selected non-empty edits, keep user on the same screen, and show success popup.
        RU: РџСЂРёРјРµРЅРёС‚СЊ РІС‹Р±СЂР°РЅРЅС‹Рµ РЅРµРїСѓСЃС‚С‹Рµ РёР·РјРµРЅРµРЅРёСЏ, РѕСЃС‚Р°РІРёС‚СЊ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ РЅР° С‚РµРєСѓС‰РµРј СЌРєСЂР°РЅРµ Рё РїРѕРєР°Р·Р°С‚СЊ popup РѕР± СѓСЃРїРµС…Рµ.
        """
        view = self._view
        tglog(f"[TGDBG] step1 telegram_input text='{str((view.ids.inp_tg.text or '').strip())}'")
        tglog(f"[TGDBG] step2 telegram_checkbox active={bool(view.ids.chk_tg.active)}")
        tglog("[TGDBG] step3 click CHANGE")
        trace_log("UI", "UI.BUTTON_CLICK", button="CHANGE")
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
        if not changes:
            return
        if view.ids.chk_tg.active:
            if not self._apply_changes_and_show_result(changes, show_success_popup=False):
                return
            user_id = self._resolve_current_user_id()
            if user_id <= 0:
                tglog("[TGDBG] step10 DONE fail error=NO_USER_ID")
                return
            if not self._ensure_server_telegram(user_id=user_id, changes=changes):
                tglog("[TGDBG] step10 DONE fail error=PROFILE_UPDATE_FAILED")
                return
            self._show_tg_verify_ask_popup(changes)
            return
        self._apply_changes_and_show_result(changes)

    def _apply_changes_and_show_result(self, changes: dict, show_success_popup: bool = True) -> bool:
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
        if show_success_popup:
            self._show_changed_popup()
        return True

    def _show_tg_verify_ask_popup(self, changes: dict) -> None:
        """EN: Ask user whether Telegram verification flow should start for checked Telegram update.
        RU: РЎРїСЂРѕСЃРёС‚СЊ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ, РЅСѓР¶РЅРѕ Р»Рё Р·Р°РїСѓСЃРєР°С‚СЊ РїРѕС‚РѕРє РІРµСЂРёС„РёРєР°С†РёРё Telegram РґР»СЏ РѕС‚РјРµС‡РµРЅРЅРѕРіРѕ РѕР±РЅРѕРІР»РµРЅРёСЏ Telegram.
        """

        tglog("[TGDBG] step6 show popup TG_CONFIRM")
        trace_log("UI", "UI.POPUP_SHOW", popup="TG_CONFIRM")
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
            tglog("[TGDBG] step7 click popup BACK")
            tglog("[TGDBG] step10 DONE fail error=USER_BACK")
            trace_log("UI", "UI.BUTTON_CLICK", button="POPUP_BACK")
            trace_log("UI", "UI.POPUP_CLOSE", popup="TG_CONFIRM", action="BACK")
            self._uncheck_tg_checkbox()
            popup.dismiss()

        def _on_ok(_instance) -> None:
            tglog("[TGDBG] step7 click popup OK")
            trace_log("UI", "UI.BUTTON_CLICK", button="POPUP_OK")
            trace_log("UI", "UI.POPUP_CLOSE", popup="TG_CONFIRM", action="OK")
            self._uncheck_tg_checkbox()
            popup.dismiss()
            self._start_tg_verify_flow(changes)

        ok_btn.bind(on_release=_on_ok)
        back_btn.bind(on_release=_on_back)
        popup.open()

    def _start_tg_verify_flow(self, changes: dict) -> None:
        """EN: Request code, run two-stage Telegram open, and poll server ack until used=true.
        RU: Запросить code, выполнить двухстадийное открытие Telegram и опрашивать server ack до used=true.
        """

        def _worker() -> None:
            try:
                user_id = self._resolve_current_user_id()
                trace_log("STATE", "FLOW.USER_ID_RESOLVED", user_id=user_id)
                if user_id <= 0:
                    tglog("[TGDBG] step10 DONE fail error=NO_USER_ID")
                    trace_log("STATE", "FLOW.DONE", ok=False, reason="NO_USER_ID")
                    return

                ok, payload = auth_backend.telegram_link_request(user_id=user_id)
                payload_ok = bool(isinstance(payload, dict) and payload.get("ok"))
                payload_error = str(payload.get("error") if isinstance(payload, dict) else "API_ERROR")
                ttl_sec = int((payload.get("ttl_sec") or 0) if isinstance(payload, dict) else 0)
                tglog(f"[TGVERIFY] step8 result: ok={ok} body_ok={payload_ok} error={payload_error}")
                trace_log("HTTP", "FLOW.STEP8_RESULT", ok=ok, body_ok=payload_ok, error=payload_error)
                code = str((payload.get("code") or "").strip()) if isinstance(payload, dict) else ""
                tglog(f"[TGVERIFY] step8 link_request ok={ok} has_code={bool(code)} ttl={ttl_sec}")
                if not ok or not code:
                    error_code = payload_error
                    if error_code in {"NO_SESSION", "UNAUTHORIZED"}:
                        Clock.schedule_once(lambda _dt: self._show_session_expired_popup(), 0)
                    tglog(f"[TGVERIFY] step10 fail error={error_code}")
                    trace_log("STATE", "FLOW.DONE", ok=False, reason=error_code)
                    return

                tglog(f"[TGVERIFY] step9 code={self._mask_token(code)}")
                trace_log("STATE", "FLOW.STEP9_CODE", code=code, debug_mode=bool(TG_DEBUG_FLOW))
                tglog(f"[TGVERIFY] step10 open scheduled code={self._mask_token(code)}")

                def _open_and_poll(_dt: float) -> None:
                    self._start_tg_verify_state(user_id=int(user_id))
                    open_bot_two_stage(TELEGRAM_BOT_USERNAME, code, "TGVERIFY", warmup=True)
                    self._show_tg_enter_code_popup(user_id=int(user_id))

                Clock.schedule_once(_open_and_poll, 0)
            except Exception as exc:
                trace_exception("STATE", "FLOW.EXCEPTION", exc)
                tglog("[TGDBG] step10 DONE fail error=EXCEPTION")

        Thread(target=_worker, daemon=True).start()

    def _start_tg_verify_state(self, user_id: int) -> None:
        """EN: Initialize active Telegram verification state and timeout timer.
        RU: ???????????????? ???????? ????????? ??????????? Telegram ? ?????? ????????.
        """

        self._cancel_tg_events()
        self._tg_verify_active = True
        self._tg_verify_started_at = monotonic()
        self._tg_open_fallback_scheduled = False
        self._tg_verify_timeout_event = Clock.schedule_once(
            self._on_tg_verify_timeout,
            float(TG_VERIFY_TIMEOUT_SEC),
        )
        tglog(f"[TGVERIFY] verify timeout armed user_id={user_id} timeout={TG_VERIFY_TIMEOUT_SEC}")

    def _cancel_tg_events(self) -> None:
        """EN: Cancel Telegram verification timers and polling events safely.
        RU: ????????? ???????? ??????? ? polling ??????? ??????????? Telegram.
        """

        if self._tg_verify_timeout_event is not None:
            try:
                self._tg_verify_timeout_event.cancel()
            except Exception:
                pass
        self._tg_verify_timeout_event = None

    def _on_tg_verify_timeout(self, _dt) -> None:
        """EN: Handle overall verify timeout by showing fail popup once.
        RU: ?????????? ????? ??????? ??????????? ? ???????? fail-popup ???? ???.
        """

        if not self._tg_verify_active:
            return
        tglog("[TGVERIFY] timeout popup shown")
        self._tg_verify_active = False
        cancel_open_flow("TGVERIFY")
        self._cancel_tg_events()
        self._show_tg_fail_popup(message=t("tg.verify_timeout"))

    def _ensure_server_telegram(self, user_id: int, changes: dict) -> bool:
        """EN: Ensure Telegram handle is persisted in server profile before verify request.
        RU: ?????????, ??? Telegram-??? ???????? ? ??????? ?? ??????? ?? ??????? verify.
        """

        tg_value = str((changes.get("tg") or "").strip())
        if not tg_value:
            return False
        if not auth_backend.get_refresh_token():
            tglog("[SESSION] blocked authorized request: no refresh_token path=/profile/user/update")
            trace_log("SESSION", "SESSION.BLOCKED_REQUEST", path="/profile/user/update", reason="NO_REFRESH_TOKEN")
            Clock.schedule_once(lambda _dt: self._show_session_expired_popup(), 0)
            return False
        req_body = {"user_id": int(user_id), "telegram": tg_value}
        tglog(f"[TGDBG] step4 POST /profile/user/update payload={req_body}")
        trace_log(
            "HTTP",
            "FLOW.STEP4_PROFILE_UPDATE_SEND",
            endpoint="/profile/user/update",
            method="POST",
            payload_keys=sorted(req_body.keys()),
            user_id=int(user_id),
            telegram=tg_value,
            auth_present=True,
        )
        ok = auth_backend.save_profile_user(user_id=int(user_id), telegram=tg_value)
        tglog(f"[TGDBG] step5 /profile/user/update ok={ok}")
        trace_log(
            "HTTP",
            "FLOW.STEP5_PROFILE_UPDATE_RESPONSE",
            endpoint="/profile/user/update",
            ok=bool(ok),
            response_ok=bool(ok),
            response_error=None if ok else "API_ERROR",
        )
        if not ok:
            tglog("[TGDBG] step5 FAIL save_profile")
        return bool(ok)

    def _show_tg_instruction_popup(self) -> None:
        """EN: Show instructions after Telegram open attempt.
        RU: Показать инструкцию после попытки открытия Telegram.
        """

        text = f"{t('tg.opening')}\n\n{t('tg.verify.instruction')}"
        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        content.add_widget(Label(text=text))
        trace_log("UI", "UI.POPUP_SHOW", popup="TG_INSTRUCTION")
        ok_btn = Button(text=t("common.ok"), size_hint_y=None, height=dp(40))
        content.add_widget(ok_btn)
        popup = Popup(title="", content=content, size_hint=(0.9, 0.45), auto_dismiss=False)

        def _on_ok(_instance) -> None:
            trace_log("UI", "UI.POPUP_CLOSE", popup="TG_INSTRUCTION", action="OK")
            self._uncheck_tg_checkbox()
            popup.dismiss()

        ok_btn.bind(on_release=_on_ok)
        self._tg_instruction_popup = popup
        popup.open()

    def _show_tg_enter_code_popup(self, user_id: int) -> None:
        """EN: Show popup for entering 6-digit Telegram confirm code from bot message.
        RU: Показать popup для ввода 6-значного Telegram confirm-кода из сообщения бота.

        EN: This popup is the final step of app-side verification: user manually copies code
        from Telegram chat and app sends it to server for trusted validation.
        RU: Этот popup — финальный шаг подтверждения со стороны приложения: пользователь
        вручную переносит код из Telegram-чата, а приложение отправляет его на сервер.
        """

        tglog("[TGVERIFY] step11 show popup ENTER_CODE")
        trace_log("UI", "UI.POPUP_SHOW", popup="TG_ENTER_CODE")

        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        content.add_widget(Label(text=t("tg.enter_code_title")))
        code_input = TextInput(
            hint_text=t("tg.enter_code_hint"),
            multiline=False,
            input_filter="int",
            password=False,
            size_hint_y=None,
            height=dp(44),
        )
        content.add_widget(code_input)

        buttons = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=dp(40))
        ok_btn = Button(text=t("common.ok"))
        back_btn = Button(text=t("common.back"))
        buttons.add_widget(ok_btn)
        buttons.add_widget(back_btn)
        content.add_widget(buttons)
        popup = Popup(title="", content=content, size_hint=(0.85, 0.45), auto_dismiss=False)

        def _on_back(_instance) -> None:
            trace_log("UI", "UI.POPUP_CLOSE", popup="TG_ENTER_CODE", action="BACK")
            self._tg_verify_active = False
            cancel_open_flow("TGVERIFY")
            self._cancel_tg_events()
            self._uncheck_tg_checkbox()
            popup.dismiss()

        def _on_ok(_instance) -> None:
            code_value = str((code_input.text or "").strip())
            if len(code_value) != 6 or not code_value.isdigit():
                self._show_popup(t("tg.code_invalid_input"))
                return
            trace_log(
                "UI",
                "UI.BUTTON_CLICK",
                button="TG_ENTER_CODE_OK",
                code_len=len(code_value),
                code_tail=code_value[-2:],
            )
            popup.dismiss()
            self._submit_tg_confirm_code(user_id=int(user_id), confirm_code=code_value)

        ok_btn.bind(on_release=_on_ok)
        back_btn.bind(on_release=_on_back)
        popup.open()

    def _submit_tg_confirm_code(self, user_id: int, confirm_code: str) -> None:
        """EN: Submit confirm code to backend, refresh snapshot, and show success/fail popup.
        RU: Отправить confirm-код на backend, обновить snapshot и показать popup успеха/ошибки.
        """

        tglog(f"[TGVERIFY] step11 confirm_code_entered mask=**{confirm_code[-2:]}")
        tglog(f"[TGVERIFY] step12 confirm send len(code)={len(confirm_code)}")
        trace_log(
            "HTTP",
            "FLOW.STEP12_CONFIRM_SEND",
            endpoint="/telegram/link/confirm",
            user_id=int(user_id),
            code_len=len(confirm_code),
        )

        def _worker() -> None:
            try:
                ok, payload = auth_backend.telegram_link_confirm(user_id=int(user_id), confirm_code=confirm_code)
                error_code = str(payload.get("error") if isinstance(payload, dict) else "API_ERROR")
                tglog(f"[TGVERIFY] step13 confirm resp ok={ok} error={error_code}")
                trace_log("HTTP", "FLOW.STEP13_CONFIRM_RESPONSE", ok=bool(ok), error=error_code)
                if not ok:
                    if error_code in {"NO_SESSION", "UNAUTHORIZED"}:
                        Clock.schedule_once(lambda _dt: self._show_session_expired_popup(), 0)
                        return
                    msg_key = {
                        "CODE_INVALID": "tg.code_invalid",
                        "CODE_EXPIRED": "tg.code_expired",
                        "CODE_USED": "tg.code_used",
                        "TG_ALREADY_LINKED": "tg.tg_already_linked",
                        "CONFIRM_422": "tg.confirm_unavailable",
                    }.get(error_code, "tg.code_invalid")
                    Clock.schedule_once(lambda _dt: self._show_tg_fail_popup(message=t(msg_key)), 0)
                    return

                self._tg_verify_active = False
                cancel_open_flow("TGVERIFY")
                self._cancel_tg_events()
                tglog("[TGVERIFY] confirm ok, syncing /auth/me")
                me_ok, me_payload = auth_backend.get_current_user_snapshot(timeout=10)
                if me_ok and isinstance(me_payload, dict) and me_payload.get("ok"):
                    sync_user_snapshot_from_payload(me_payload)
                user_payload = me_payload.get("user") if isinstance(me_payload, dict) else {}
                tglog(
                    "[TGDBG] snapshot telegram_username={u} telegram_user_id={uid} verified={ver}".format(
                        u=str((user_payload or {}).get("telegram_username") or ""),
                        uid=int((user_payload or {}).get("telegram_user_id") or 0),
                        ver=bool((user_payload or {}).get("telegram_verified")),
                    )
                )
                verified = bool(
                    me_ok
                    and isinstance(me_payload, dict)
                    and isinstance(me_payload.get("user"), dict)
                    and me_payload["user"].get("telegram_verified")
                )
                tglog(f"[TGDBG] step14 profile refreshed telegram_verified={verified}")
                trace_log("STATE", "FLOW.STEP14_PROFILE_REFRESHED", telegram_verified=verified)
                Clock.schedule_once(lambda _dt: self._apply_tg_snapshot_to_current_view(me_payload), 0)
                Clock.schedule_once(lambda _dt: self._show_changed_popup(), 0)
            except Exception as exc:
                trace_exception("STATE", "FLOW.CONFIRM_EXCEPTION", exc)
                Clock.schedule_once(lambda _dt: self._show_tg_fail_popup(message=t("tg.code_invalid")), 0)

        Thread(target=_worker, daemon=True).start()

    def _apply_tg_snapshot_to_current_view(self, me_payload: dict | None) -> None:
        """EN: Apply Telegram values from server snapshot to current edit view fields.
        RU: Применить Telegram-значения из серверного snapshot в текущие поля экрана редактирования.
        """

        try:
            if not isinstance(me_payload, dict):
                return
            user_payload = me_payload.get("user")
            if not isinstance(user_payload, dict):
                return
            telegram_display = str((user_payload.get("telegram") or "").strip())
            if not telegram_display:
                telegram_display = str((user_payload.get("telegram_username") or "").strip())
            if not telegram_display:
                telegram_display = t("common.no_data")
            if self._view is not None and "inp_tg" in self._view.ids:
                self._view.ids.inp_tg.text = "" if telegram_display == t("common.no_data") else telegram_display
            tglog(f"[TGDBG] ui updated telegram label={telegram_display}")
        except Exception:
            return

    def _start_tg_polling(self, user_id: int) -> None:
        """EN: Start periodic poll of /auth/me to detect telegram_verified transition.
        RU: Запустить периодический опрос /auth/me для отслеживания telegram_verified.
        """

        def _poll(_dt) -> bool:
            if not self._tg_verify_active:
                return False
            ok, payload = auth_backend.get_current_user_snapshot(timeout=8)
            if not ok or not isinstance(payload, dict) or not payload.get("ok"):
                self._dbg("[TG] poll telegram_verified=unknown (network/api error)")
                return True
            user_payload = payload.get("user") if isinstance(payload, dict) else None
            verified = bool(isinstance(user_payload, dict) and user_payload.get("telegram_verified"))
            self._dbg(f"[TG] poll telegram_verified={verified}")
            if verified:
                self._on_tg_verify_success()
                return False
            return True

        self._tg_verify_poll_event = Clock.schedule_interval(_poll, 2.0)

    def _on_tg_verify_success(self) -> None:
        """EN: Complete Telegram verification flow and show standard success popup.
        RU: ????????? ????? ??????????? Telegram ? ???????? ??????????? popup ??????.
        """

        self._tg_verify_active = False
        self._cancel_tg_events()
        if self._tg_instruction_popup is not None:
            try:
                self._tg_instruction_popup.dismiss()
            except Exception:
                pass
        self._tg_instruction_popup = None
        self._show_changed_popup()

    def _show_tg_fail_popup(self, message: str | None = None) -> None:
        """EN: Show Telegram-flow failure popup and uncheck Telegram checkbox after close.
        RU: ???????? popup ?????? Telegram-flow ? ????? ??????? Telegram ????? ????????.
        """

        self._tg_verify_active = False
        self._cancel_tg_events()
        if self._tg_instruction_popup is not None:
            try:
                self._tg_instruction_popup.dismiss()
            except Exception:
                pass
        self._tg_instruction_popup = None

        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        content.add_widget(Label(text=str(message or t("tg_verify.fail"))))
        trace_log("UI", "UI.POPUP_SHOW", popup="TG_FAIL")
        ok_btn = Button(text=t("common.ok"), size_hint_y=None, height=dp(40))
        content.add_widget(ok_btn)
        popup = Popup(title="", content=content, size_hint=(0.8, 0.4), auto_dismiss=False)

        def _on_ok(_instance) -> None:
            trace_log("UI", "UI.POPUP_CLOSE", popup="TG_FAIL", action="OK")
            self._uncheck_tg_checkbox()
            popup.dismiss()

        ok_btn.bind(on_release=_on_ok)
        popup.open()

    def _resolve_current_user_id(self) -> int:
        """EN: Resolve numeric current user_id from cache or the protected current-session snapshot.
        RU: Получить числовой текущий user_id из кэша или через защищённый snapshot текущей сессии.
        """

        ok, payload = auth_backend.get_current_user_id()
        if not ok:
            return 0
        try:
            return int(payload)
        except Exception:
            return 0

    def _mask_token(self, token: str) -> str:
        """EN: Return masked token value for safe app logs.
        RU: Вернуть маскированный токен для безопасных логов приложения.
        """

        value = str((token or "").strip())
        if len(value) <= 8:
            return "*" * len(value)
        return f"{value[:4]}...{value[-4:]}"

    def _dbg(self, message: str) -> None:
        """EN: Emit Telegram-flow debug line to logger and stdout.
        RU: Вывести debug-строку Telegram-flow в logger и stdout.
        """

        _LOG.info(message)
        print(message, flush=True)

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

        blocked_selected = view.ids.chk_email.active
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
        self._tg_verify_active = False
        self._cancel_tg_events()
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
        self._app.change_screen(PROFILE)

    def _refresh_right_login(self) -> None:
        """EN: Reload current cache and update right top text with login or localized no-data fallback.
        RU: РџРµСЂРµС‡РёС‚Р°С‚СЊ С‚РµРєСѓС‰РёР№ РєСЌС€ Рё РѕР±РЅРѕРІРёС‚СЊ right top С‚РµРєСЃС‚ Р»РѕРіРёРЅРѕРј РёР»Рё Р»РѕРєР°Р»РёР·РѕРІР°РЅРЅС‹Рј fallback no-data.
        """
        current = self._manager.load_current_user_data() or {}
        self._view.right_text = user_value_text(current.get("login"))

    def _show_popup(self, message: str) -> None:
        """EN: Show modal popup with a message and one OK button, matching register popup style.
        RU: РџРѕРєР°Р·Р°С‚СЊ РјРѕРґР°Р»СЊРЅС‹Р№ popup СЃ СЃРѕРѕР±С‰РµРЅРёРµРј Рё РѕРґРЅРѕР№ РєРЅРѕРїРєРѕР№ OK РІ СЃС‚РёР»Рµ popup СЌРєСЂР°РЅР° СЂРµРіРёСЃС‚СЂР°С†РёРё.
        """
        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        content.add_widget(Label(text=message))
        trace_log("UI", "UI.POPUP_SHOW", popup="GENERIC", message=str(message)[:120])
        ok_btn = Button(text=t("common.ok"), size_hint_y=None, height=dp(40))
        content.add_widget(ok_btn)

        popup = Popup(title="", content=content, size_hint=(0.8, 0.4), auto_dismiss=False)
        ok_btn.bind(
            on_release=lambda _instance: (
                trace_log("UI", "UI.POPUP_CLOSE", popup="GENERIC", action="OK"),
                popup.dismiss(),
            )
        )
        popup.open()

    def _show_session_expired_popup(self) -> None:
        """EN: Show session-expired popup, clear tokens, and route user to login after acknowledgement.
        RU: Показать popup об истечении сессии, очистить токены и перевести пользователя на экран входа после подтверждения.
        """

        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        content.add_widget(Label(text=t("tg.session.expired")))
        trace_log("UI", "UI.POPUP_SHOW", popup="SESSION_EXPIRED")
        ok_btn = Button(text=t("common.ok"), size_hint_y=None, height=dp(40))
        content.add_widget(ok_btn)
        popup = Popup(title="", content=content, size_hint=(0.8, 0.4), auto_dismiss=False)

        def _on_ok(_instance) -> None:
            auth_backend.force_logout(reason="UI_SESSION_EXPIRED_POPUP")
            trace_log("UI", "UI.POPUP_CLOSE", popup="SESSION_EXPIRED", action="OK")
            popup.dismiss()
            self._app.change_screen(LOGIN)

        ok_btn.bind(on_release=_on_ok)
        popup.open()

    def _show_changed_popup(self) -> None:
        """EN: Show changed-data popup and reset all edit checkboxes after clicking OK.
        RU: РџРѕРєР°Р·Р°С‚СЊ popup РѕР± РёР·РјРµРЅРµРЅРёРё РґР°РЅРЅС‹С… Рё СЃР±СЂРѕСЃРёС‚СЊ РІСЃРµ С‡РµРєР±РѕРєСЃС‹ СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ РїРѕСЃР»Рµ РЅР°Р¶Р°С‚РёСЏ OK.
        """
        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        content.add_widget(Label(text=t("profile_change.popup.changed")))
        trace_log("UI", "UI.POPUP_SHOW", popup="DATA_CHANGED")
        ok_btn = Button(text=t("common.ok"), size_hint_y=None, height=dp(40))
        content.add_widget(ok_btn)

        popup = Popup(title="", content=content, size_hint=(0.8, 0.4), auto_dismiss=False)

        def _on_ok(_instance) -> None:
            trace_log("UI", "UI.POPUP_CLOSE", popup="DATA_CHANGED", action="OK")
            self._reset_edit_checkboxes()
            popup.dismiss()

        ok_btn.bind(on_release=_on_ok)
        popup.open()

    def _reset_edit_checkboxes(self) -> None:
        """EN: Clear all profile-change edit checkboxes.
        RU: РЎРЅСЏС‚СЊ РІСЃРµ С‡РµРєР±РѕРєСЃС‹ СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ РЅР° СЌРєСЂР°РЅРµ РёР·РјРµРЅРµРЅРёСЏ РїСЂРѕС„РёР»СЏ.
        """
        ids = self._view.ids
        for name in ("chk_login", "chk_email", "chk_phone", "chk_tg"):
            cb = ids.get(name)
            if cb is not None:
                cb.active = False

    def attach_view(self, view) -> None:
        """EN: Attach view reference for handlers and helper methods.
        RU: РџРѕРґРєР»СЋС‡РёС‚СЊ СЃСЃС‹Р»РєСѓ РЅР° view РґР»СЏ РѕР±СЂР°Р±РѕС‚С‡РёРєРѕРІ Рё РІСЃРїРѕРјРѕРіР°С‚РµР»СЊРЅС‹С… РјРµС‚РѕРґРѕРІ.
        """
        self._view = view
