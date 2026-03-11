"""EN: View for the settings screen.
RU: Представление экрана настроек.
"""

from pathlib import Path
from threading import Thread
from time import monotonic

import requests
from data.user_cache.user_cache_reader import get_user_cache
from data.user_cache.user_session import UserSession
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivymd.app import MDApp
from kivymd.uix.button import MDIconButton
from kivymd.uix.screen import MDScreen
from manager.auth.account_delete import confirm_delete_account
from manager import auth_backend
from manager.config import API_BASE_URL, PAYOUT_TELEGRAM_BOT_USERNAME, TG_LINK_STATUS_POLL_SEC, VERIFY_OPEN_TIMEOUT_SEC
from manager.docs.doc_locale import get_lang_code
from manager.game_control.hud_layout_store import get_swapped, toggle_swapped
from manager.lang.lang_manager import t
from manager.telegram_deeplink import cancel_open_flow, open_bot_two_stage
from manager.trace import trace_log
from manager.tg_debug_log import tglog
from uix.debug.debug_borders import apply_debug_borders_to_ids
from uix.screens.common.button_text_style import apply_button_text_style, caps
from uix.screens.routes import LOGIN

from .settings_controller import SettingsScreenController
from .settings_layout import SETTINGS_DEBUG_IDS, apply_settings_layout
from .settings_vm import SettingsScreenVM

KV_PATH = Path(__file__).with_name("settings.kv")
DOC_KEY_RULES = "rules"
DOC_KEY_POLICY = "policy"
DOC_KEY_ABOUT = "about"


class ToggleIconButton(MDIconButton):
    """EN: Icon button that toggles between two icon names on every release.
    RU: Кнопка-иконка, переключающаяся между двумя именами иконок при отпускании.
    """

    toggled = BooleanProperty(False)
    icon_on = StringProperty("music")
    icon_off = StringProperty("music-off")

    def on_kv_post(self, base_widget) -> None:
        """EN: Initialize visible icon from current toggle state after KV binding.
        RU: Инициализировать отображаемую иконку из текущего состояния после KV.
        """
        super().on_kv_post(base_widget)
        self._apply_icon()

    def on_release(self, *args) -> None:
        """EN: Toggle local icon state only; external callbacks may be added later.
        RU: Переключить только локальное состояние иконки; внешние callback можно добавить позже.
        """
        self.toggled = not self.toggled
        self._apply_icon()
        return super().on_release(*args)

    def _apply_icon(self) -> None:
        """EN: Apply icon name according to the current toggle state.
        RU: Применить имя иконки согласно текущему состоянию переключателя.
        """
        self.icon = self.icon_off if self.toggled else self.icon_on


class MirrorToggleIconButton(MDIconButton):
    """EN: Icon button that toggles horizontal mirroring using a canvas transform.
    RU: Кнопка-иконка, переключающая горизонтальное зеркало через canvas-трансформацию.
    """

    mirrored = BooleanProperty(False)

    def on_kv_post(self, base_widget) -> None:
        """EN: Enforce the fixed icon used for keyboard-side placeholder toggle.
        RU: Зафиксировать иконку заглушки для переключения стороны управления.
        """
        super().on_kv_post(base_widget)
        self.icon = "gamepad-square-outline"

    def on_release(self, *args) -> None:
        """EN: Dispatch release event; mirrored state is synced by settings view handler.
        RU: Пробросить событие release; зеркальность синхронизируется в settings view.
        """
        return super().on_release(*args)


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
        self._sync_hud_layout_icon()
        apply_button_text_style(
            self,
            [
                self.ids.login_btn_text,
                self.ids.action_btn_text,
                self.ids.back_btn_text,
            ],
        )
        apply_debug_borders_to_ids(self, SETTINGS_DEBUG_IDS)
        self._pay_open_started_at = 0.0
        self._pay_status_poll_event = None
        self._pay_flow_active = False

    def on_pre_enter(self, *args) -> None:
        """EN: Update login button text based on auth state.
        RU: Обновить текст/логин в верхней панели по состоянию авторизации.
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
        self._sync_hud_layout_icon()

    def _sync_hud_layout_icon(self) -> None:
        """EN: Sync settings gamepad icon mirror state with persisted HUD layout flag.
        RU: Синхронизировать зеркальность иконки gamepad с сохранённым флагом раскладки HUD.
        """
        gamepad_icon = self.ids.get("middle_card_keyboard_side_icon")
        if gamepad_icon is not None:
            gamepad_icon.mirrored = bool(get_swapped())

    def toggle_hud_layout(self) -> None:
        """EN: Toggle persisted HUD touch-layout swap flag and refresh gamepad icon state.
        RU: Переключить флаг перестановки тач-раскладки HUD и обновить иконку gamepad.
        """
        new_val = toggle_swapped()
        gamepad_icon = self.ids.get("middle_card_keyboard_side_icon")
        if gamepad_icon is not None:
            gamepad_icon.mirrored = bool(new_val)

    def open_doc_popup(self, text: str) -> None:
        """EN: Open "About" document loaded from backend API.
        RU: Открыть документ "О нас", загруженный из backend API.

        EN: `text` argument is kept only for KV backward compatibility.
        RU: Аргумент `text` сохранён только для обратной совместимости с KV.
        """
        _ = text
        self.open_text_doc(
            t("settings.docs.about"),
            DOC_KEY_ABOUT,
            "File not found.",
        )

    def _read_text_doc(self, doc_key: str, missing_message: str) -> str:
        """EN: Read localized markdown document text from backend API.
        RU: Считать локализованный markdown-текст документа из backend API.

        EN: Network timeout is limited to keep UI responsive.
        RU: Таймаут сети ограничен, чтобы не блокировать UI надолго.
        """
        try:
            response = requests.get(
                f"{API_BASE_URL}/docs/{doc_key}",
                params={"lang": get_lang_code()},
                timeout=8,
            )
            if response.status_code != 200:
                return missing_message
            payload = response.json()
            if not isinstance(payload, dict) or not payload.get("ok"):
                return missing_message
            content = payload.get("content")
            if not isinstance(content, str) or not content.strip():
                return missing_message
            return content
        except Exception:
            return missing_message

    def open_text_doc(self, title: str, doc_key: str, missing_message: str) -> None:
        """EN: Open a scrollable popup with text fetched from backend API.
        RU: Открыть прокручиваемый popup с текстом, полученным из backend API.
        """
        text = self._read_text_doc(doc_key, missing_message)

        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))
        scroller = ScrollView(do_scroll_x=False, do_scroll_y=True, size_hint=(1, 1))
        text_lbl = Label(text=text, halign="left", valign="top", size_hint_y=None)

        def _sync_text_size(inst, _val):
            inst.text_size = (inst.width, None)

        def _sync_height(inst, val):
            inst.height = val[1]

        text_lbl.bind(width=_sync_text_size, texture_size=_sync_height)
        scroller.add_widget(text_lbl)
        content.add_widget(scroller)

        close_btn = Button(text="Закрыть", size_hint_y=None, height=dp(40))
        content.add_widget(close_btn)

        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.9, 0.85),
            auto_dismiss=False,
        )
        close_btn.bind(on_release=lambda _instance: popup.dismiss())
        popup.open()

    def open_privacy_policy(self) -> None:
        """EN: Open localized policy document fetched from backend API.
        RU: Открыть локализованный документ политики из backend API.
        """
        self.open_text_doc(
            t("settings.docs.policy"),
            DOC_KEY_POLICY,
            "File not found.",
        )

    def open_game_rules(self) -> None:
        """EN: Open localized rules document fetched from backend API.
        RU: Открыть локализованный документ правил из backend API.
        """
        self.open_text_doc(
            t("settings.docs.rules"),
            DOC_KEY_RULES,
            "File not found.",
        )

    def on_delete_account_pressed(self) -> None:
        """EN: Ask for delete-account confirmation and delegate to controller on success.
        RU: Попросить подтверждение удаления аккаунта и делегировать контроллеру при успехе.
        """
        confirm_delete_account(
            on_deleted=lambda: self._controller.logout(),
            on_cancel=lambda: None,
        )

    def configure(self, vm: SettingsScreenVM, controller: SettingsScreenController) -> None:
        """EN: Configure texts and bind callbacks.
        RU: Настроить тексты и привязать callback-и.
        """
        self._controller = controller
        self.ids.left_text.text = vm.title
        self.ids.login_btn_text.text = caps(vm.login_text)
        self.ids.action_btn_text.text = caps(vm.action_text)
        self.ids.back_btn_text.text = caps(vm.back_text)

        self.ids.login_btn.on_release = controller.payout
        self.ids.action_btn.on_release = controller.logout
        self.ids.back_btn.on_release = controller.back

    def start_payout_flow(self) -> None:
        """EN: Start payout bot open flow from Settings button.
        RU: Запустить flow открытия payout-бота по кнопке из Настроек.
        """

        tglog("[PAY] step1 click PAYOUT")
        trace_log("OPEN", "PAYOUT.CLICK")
        if not auth_backend.get_refresh_token():
            self._show_session_expired_popup()
            return

        cache = get_user_cache() or {}
        try:
            user_id = int(cache.get("user_id") or 0)
        except Exception:
            user_id = 0
        if user_id <= 0:
            self._show_session_expired_popup()
            return

        def _worker() -> None:
            ok, payload = auth_backend.payout_link_request(user_id)
            error_code = str(payload.get("error") if isinstance(payload, dict) else "API_ERROR")
            code = str((payload.get("code") or "").strip()) if isinstance(payload, dict) else ""
            if not ok or not code:
                if error_code in {"NO_SESSION", "UNAUTHORIZED"}:
                    Clock.schedule_once(lambda _dt: self._show_session_expired_popup(), 0)
                else:
                    Clock.schedule_once(lambda _dt: self._show_info_popup(t("pay.request_fail")), 0)
                return

            tglog(f"[PAY] step4 open scheduled code={auth_backend.mask_token(code)}")
            self._pay_flow_active = True
            self._pay_open_started_at = float(monotonic())

            def _open_and_poll(_dt: float) -> None:
                open_bot_two_stage(
                    PAYOUT_TELEGRAM_BOT_USERNAME,
                    code,
                    "PAY",
                    warmup=True,
                    retry_always=True,
                )
                self._start_payout_status_polling(user_id=int(user_id))

            Clock.schedule_once(_open_and_poll, 0)

        Thread(target=_worker, daemon=True).start()

    def _start_payout_status_polling(self, user_id: int) -> None:
        """EN: Poll `/payout/link/status` until bot ack marks code used or timeout is reached.
        RU: Опрашивать `/payout/link/status`, пока bot ack не пометит код used или не выйдет timeout.
        """

        if self._pay_status_poll_event is not None:
            try:
                self._pay_status_poll_event.cancel()
            except Exception:
                pass
            self._pay_status_poll_event = None

        def _poll(_dt: float) -> bool:
            if not self._pay_flow_active:
                return False
            elapsed = float(monotonic() - float(self._pay_open_started_at or 0.0))
            ok, payload = auth_backend.payout_link_status(int(user_id))
            used = bool(isinstance(payload, dict) and payload.get("used"))
            ttl_sec = int((payload.get("ttl_sec") or 0) if isinstance(payload, dict) else 0)
            tglog(f"[PAY] status used={used} ttl={ttl_sec} elapsed={elapsed:.1f}")
            if used:
                self._pay_flow_active = False
                cancel_open_flow("PAY")
                if self._pay_status_poll_event is not None:
                    try:
                        self._pay_status_poll_event.cancel()
                    except Exception:
                        pass
                    self._pay_status_poll_event = None
                return False
            if elapsed >= float(VERIFY_OPEN_TIMEOUT_SEC):
                self._pay_flow_active = False
                cancel_open_flow("PAY")
                if self._pay_status_poll_event is not None:
                    try:
                        self._pay_status_poll_event.cancel()
                    except Exception:
                        pass
                    self._pay_status_poll_event = None
                tglog("[PAY] timeout popup shown")
                self._show_info_popup(t("pay.open_timeout"))
                return False
            return True

        self._pay_status_poll_event = Clock.schedule_interval(_poll, float(TG_LINK_STATUS_POLL_SEC))

    def _show_session_expired_popup(self) -> None:
        """EN: Show session-expired popup, force logout, and route to Login.
        RU: Показать popup об истечении сессии, выполнить logout и перейти на Login.
        """

        def _go_login(_instance) -> None:
            auth_backend.force_logout(reason="PAYOUT_NO_SESSION")
            app = MDApp.get_running_app()
            if app is not None:
                app.change_screen(LOGIN)
            popup.dismiss()

        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        content.add_widget(Label(text=t("pay.session_expired")))
        btn = Button(text=t("common.ok"), size_hint_y=None, height=dp(40))
        content.add_widget(btn)
        popup = Popup(title="", content=content, size_hint=(0.8, 0.35), auto_dismiss=False)
        btn.bind(on_release=_go_login)
        popup.open()

    def _show_info_popup(self, message: str) -> None:
        """EN: Show compact informational popup for payout flow messages.
        RU: Показать компактный информационный popup для сообщений payout flow.
        """

        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        content.add_widget(Label(text=message))
        btn = Button(text=t("common.ok"), size_hint_y=None, height=dp(40))
        content.add_widget(btn)
        popup = Popup(title="", content=content, size_hint=(0.82, 0.35), auto_dismiss=False)
        btn.bind(on_release=lambda *_: popup.dismiss())
        popup.open()
