"""EN: View for the settings screen.
RU: Р СџРЎР‚Р ВµР Т‘РЎРѓРЎвЂљР В°Р Р†Р В»Р ВµР Р…Р С‘Р Вµ РЎРЊР С”РЎР‚Р В°Р Р…Р В° Р Р…Р В°РЎРѓРЎвЂљРЎР‚Р С•Р ВµР С”.
"""

from pathlib import Path
from threading import Thread
from time import monotonic

import requests
from data.user_cache.user_cache_profile import get_user_setting, set_user_setting
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
from manager.lang.lang_manager import t, topbar_value_text
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
    RU: Р С™Р Р…Р С•Р С—Р С”Р В°-Р С‘Р С”Р С•Р Р…Р С”Р В°, Р С—Р ВµРЎР‚Р ВµР С”Р В»РЎР‹РЎвЂЎР В°РЎР‹РЎвЂ°Р В°РЎРЏРЎРѓРЎРЏ Р СР ВµР В¶Р Т‘РЎС“ Р Т‘Р Р†РЎС“Р СРЎРЏ Р С‘Р СР ВµР Р…Р В°Р СР С‘ Р С‘Р С”Р С•Р Р…Р С•Р С” Р С—РЎР‚Р С‘ Р С•РЎвЂљР С—РЎС“РЎРѓР С”Р В°Р Р…Р С‘Р С‘.
    """

    toggled = BooleanProperty(False)
    icon_on = StringProperty("music")
    icon_off = StringProperty("music-off")

    def on_kv_post(self, base_widget) -> None:
        """EN: Initialize visible icon from current toggle state after KV binding.
        RU: Р ВР Р…Р С‘РЎвЂ Р С‘Р В°Р В»Р С‘Р В·Р С‘РЎР‚Р С•Р Р†Р В°РЎвЂљРЎРЉ Р С•РЎвЂљР С•Р В±РЎР‚Р В°Р В¶Р В°Р ВµР СРЎС“РЎР‹ Р С‘Р С”Р С•Р Р…Р С”РЎС“ Р С‘Р В· РЎвЂљР ВµР С”РЎС“РЎвЂ°Р ВµР С–Р С• РЎРѓР С•РЎРѓРЎвЂљР С•РЎРЏР Р…Р С‘РЎРЏ Р С—Р С•РЎРѓР В»Р Вµ KV.
        """
        super().on_kv_post(base_widget)
        self._apply_icon()

    def on_release(self, *args) -> None:
        """EN: Toggle local icon state only; external callbacks may be added later.
        RU: Р СџР ВµРЎР‚Р ВµР С”Р В»РЎР‹РЎвЂЎР С‘РЎвЂљРЎРЉ РЎвЂљР С•Р В»РЎРЉР С”Р С• Р В»Р С•Р С”Р В°Р В»РЎРЉР Р…Р С•Р Вµ РЎРѓР С•РЎРѓРЎвЂљР С•РЎРЏР Р…Р С‘Р Вµ Р С‘Р С”Р С•Р Р…Р С”Р С‘; Р Р†Р Р…Р ВµРЎв‚¬Р Р…Р С‘Р Вµ callback Р СР С•Р В¶Р Р…Р С• Р Т‘Р С•Р В±Р В°Р Р†Р С‘РЎвЂљРЎРЉ Р С—Р С•Р В·Р В¶Р Вµ.
        """
        self.toggled = not self.toggled
        self._apply_icon()
        return super().on_release(*args)

    def set_toggled(self, value: bool) -> None:
        """EN: Explicitly synchronize toggle state without a user click.
        RU: Явно синхронизировать состояние toggle без пользовательского клика.
        """
        self.toggled = bool(value)
        self._apply_icon()

    def _apply_icon(self) -> None:
        """EN: Apply icon name according to the current toggle state.
        RU: Р СџРЎР‚Р С‘Р СР ВµР Р…Р С‘РЎвЂљРЎРЉ Р С‘Р СРЎРЏ Р С‘Р С”Р С•Р Р…Р С”Р С‘ РЎРѓР С•Р С–Р В»Р В°РЎРѓР Р…Р С• РЎвЂљР ВµР С”РЎС“РЎвЂ°Р ВµР СРЎС“ РЎРѓР С•РЎРѓРЎвЂљР С•РЎРЏР Р…Р С‘РЎР‹ Р С—Р ВµРЎР‚Р ВµР С”Р В»РЎР‹РЎвЂЎР В°РЎвЂљР ВµР В»РЎРЏ.
        """
        self.icon = self.icon_off if self.toggled else self.icon_on


class MirrorToggleIconButton(MDIconButton):
    """EN: Icon button that toggles horizontal mirroring using a canvas transform.
    RU: Р С™Р Р…Р С•Р С—Р С”Р В°-Р С‘Р С”Р С•Р Р…Р С”Р В°, Р С—Р ВµРЎР‚Р ВµР С”Р В»РЎР‹РЎвЂЎР В°РЎР‹РЎвЂ°Р В°РЎРЏ Р С–Р С•РЎР‚Р С‘Р В·Р С•Р Р…РЎвЂљР В°Р В»РЎРЉР Р…Р С•Р Вµ Р В·Р ВµРЎР‚Р С”Р В°Р В»Р С• РЎвЂЎР ВµРЎР‚Р ВµР В· canvas-РЎвЂљРЎР‚Р В°Р Р…РЎРѓРЎвЂћР С•РЎР‚Р СР В°РЎвЂ Р С‘РЎР‹.
    """

    mirrored = BooleanProperty(False)

    def on_kv_post(self, base_widget) -> None:
        """EN: Enforce the fixed icon used for keyboard-side placeholder toggle.
        RU: Р вЂ”Р В°РЎвЂћР С‘Р С”РЎРѓР С‘РЎР‚Р С•Р Р†Р В°РЎвЂљРЎРЉ Р С‘Р С”Р С•Р Р…Р С”РЎС“ Р В·Р В°Р С–Р В»РЎС“РЎв‚¬Р С”Р С‘ Р Т‘Р В»РЎРЏ Р С—Р ВµРЎР‚Р ВµР С”Р В»РЎР‹РЎвЂЎР ВµР Р…Р С‘РЎРЏ РЎРѓРЎвЂљР С•РЎР‚Р С•Р Р…РЎвЂ№ РЎС“Р С—РЎР‚Р В°Р Р†Р В»Р ВµР Р…Р С‘РЎРЏ.
        """
        super().on_kv_post(base_widget)
        self.icon = "gamepad-square-outline"

    def on_release(self, *args) -> None:
        """EN: Dispatch release event; mirrored state is synced by settings view handler.
        RU: Р СџРЎР‚Р С•Р В±РЎР‚Р С•РЎРѓР С‘РЎвЂљРЎРЉ РЎРѓР С•Р В±РЎвЂ№РЎвЂљР С‘Р Вµ release; Р В·Р ВµРЎР‚Р С”Р В°Р В»РЎРЉР Р…Р С•РЎРѓРЎвЂљРЎРЉ РЎРѓР С‘Р Р…РЎвЂ¦РЎР‚Р С•Р Р…Р С‘Р В·Р С‘РЎР‚РЎС“Р ВµРЎвЂљРЎРѓРЎРЏ Р Р† settings view.
        """
        return super().on_release(*args)


Builder.load_file(str(KV_PATH))


class SettingsScreenView(MDScreen):
    """EN: Settings screen view that wires layout, VM, and controller.
    RU: Р СџРЎР‚Р ВµР Т‘РЎРѓРЎвЂљР В°Р Р†Р В»Р ВµР Р…Р С‘Р Вµ Р Р…Р В°РЎРѓРЎвЂљРЎР‚Р С•Р ВµР С”, РЎРѓР Р†РЎРЏР В·РЎвЂ№Р Р†Р В°РЎР‹РЎвЂ°Р ВµР Вµ РЎР‚Р В°РЎРѓР С”Р В»Р В°Р Т‘Р С”РЎС“, VM Р С‘ Р С”Р С•Р Р…РЎвЂљРЎР‚Р С•Р В»Р В»Р ВµРЎР‚.
    """

    def on_kv_post(self, base_widget) -> None:
        """EN: Apply layout after KV is ready.
        RU: Р СџРЎР‚Р С‘Р СР ВµР Р…Р С‘РЎвЂљРЎРЉ РЎР‚Р В°РЎРѓР С”Р В»Р В°Р Т‘Р С”РЎС“ Р С—Р С•РЎРѓР В»Р Вµ Р В·Р В°Р С–РЎР‚РЎС“Р В·Р С”Р С‘ KV.
        """
        apply_settings_layout(self)
        from manager.lang.lang_radio import bind_lang_radios

        bind_lang_radios(self.ids.lang_ru_radio, self.ids.lang_en_radio)
        self._sync_hud_layout_icon()
        self._bind_sound_toggle()
        self._sync_sound_icon()
        apply_button_text_style(
            self,
            [
                self.ids.login_btn_text,
                self.ids.action_btn_text,
                self.ids.back_btn_text,
            ],
        )
        apply_debug_borders_to_ids(self, SETTINGS_DEBUG_IDS)
        self._ids_keepalive = dict(self.ids)
        for _key, _widget in self._ids_keepalive.items():
            self.ids[_key] = _widget
        self._contentbar_widget = getattr(self.ids.contentbar, "__self__", self.ids.contentbar)
        self._bottombar_widget = getattr(self.ids.bottombar, "__self__", self.ids.bottombar)
        self._pay_open_started_at = 0.0
        self._pay_status_poll_event = None
        self._pay_flow_active = False

    def on_pre_enter(self, *args) -> None:
        """EN: Update login button text based on auth state.
        RU: Р С›Р В±Р Р…Р С•Р Р†Р С‘РЎвЂљРЎРЉ РЎвЂљР ВµР С”РЎРѓРЎвЂљ/Р В»Р С•Р С–Р С‘Р Р… Р Р† Р Р†Р ВµРЎР‚РЎвЂ¦Р Р…Р ВµР в„– Р С—Р В°Р Р…Р ВµР В»Р С‘ Р С—Р С• РЎРѓР С•РЎРѓРЎвЂљР С•РЎРЏР Р…Р С‘РЎР‹ Р В°Р Р†РЎвЂљР С•РЎР‚Р С‘Р В·Р В°РЎвЂ Р С‘Р С‘.
        """
        super().on_pre_enter(*args)
        app = MDApp.get_running_app()
        if hasattr(app, "is_logged_in"):
            app.is_logged_in = UserSession().is_logged_in()
        if getattr(app, "is_logged_in", False):
            cache = get_user_cache() or {}
            self.ids.settings_top_right_login.text = topbar_value_text(cache.get("login"))
        else:
            self.ids.settings_top_right_login.text = t("common.no_data")
        self._sync_hud_layout_icon()
        self._sync_sound_icon()

    def _bind_sound_toggle(self) -> None:
        """EN: Bind the settings sound icon to unified profile settings persistence.
        RU: Привязать иконку звука в настройках к сохранению в единый профиль настроек.
        """
        sound_icon = self.ids.get("middle_card_sound_icon")
        if sound_icon is None or getattr(sound_icon, "_sound_bound", False):
            return
        sound_icon._sound_bound = True
        sound_icon.bind(on_release=self._on_sound_toggle)

    def _sync_sound_icon(self) -> None:
        """EN: Synchronize sound icon state from unified profile settings.
        RU: Синхронизировать состояние иконки звука из единого профиля настроек.
        """
        sound_icon = self.ids.get("middle_card_sound_icon")
        if sound_icon is not None:
            sound_icon.set_toggled(bool(get_user_setting("sound_enabled", True)))

    def _on_sound_toggle(self, *_args) -> None:
        """EN: Persist sound toggle state after the icon changes locally.
        RU: Сохранить состояние звука после локального переключения иконки.
        """
        sound_icon = self.ids.get("middle_card_sound_icon")
        if sound_icon is None:
            return
        set_user_setting("sound_enabled", bool(sound_icon.toggled))

    def _sync_hud_layout_icon(self) -> None:
        """EN: Sync settings gamepad icon mirror state with persisted HUD layout flag.
        RU: Р РЋР С‘Р Р…РЎвЂ¦РЎР‚Р С•Р Р…Р С‘Р В·Р С‘РЎР‚Р С•Р Р†Р В°РЎвЂљРЎРЉ Р В·Р ВµРЎР‚Р С”Р В°Р В»РЎРЉР Р…Р С•РЎРѓРЎвЂљРЎРЉ Р С‘Р С”Р С•Р Р…Р С”Р С‘ gamepad РЎРѓ РЎРѓР С•РЎвЂ¦РЎР‚Р В°Р Р…РЎвЂР Р…Р Р…РЎвЂ№Р С РЎвЂћР В»Р В°Р С–Р С•Р С РЎР‚Р В°РЎРѓР С”Р В»Р В°Р Т‘Р С”Р С‘ HUD.
        """
        gamepad_icon = self.ids.get("middle_card_keyboard_side_icon")
        if gamepad_icon is not None:
            gamepad_icon.mirrored = bool(get_swapped())

    def toggle_hud_layout(self) -> None:
        """EN: Toggle persisted HUD touch-layout swap flag and refresh gamepad icon state.
        RU: Р СџР ВµРЎР‚Р ВµР С”Р В»РЎР‹РЎвЂЎР С‘РЎвЂљРЎРЉ РЎвЂћР В»Р В°Р С– Р С—Р ВµРЎР‚Р ВµРЎРѓРЎвЂљР В°Р Р…Р С•Р Р†Р С”Р С‘ РЎвЂљР В°РЎвЂЎ-РЎР‚Р В°РЎРѓР С”Р В»Р В°Р Т‘Р С”Р С‘ HUD Р С‘ Р С•Р В±Р Р…Р С•Р Р†Р С‘РЎвЂљРЎРЉ Р С‘Р С”Р С•Р Р…Р С”РЎС“ gamepad.
        """
        new_val = toggle_swapped()
        gamepad_icon = self.ids.get("middle_card_keyboard_side_icon")
        if gamepad_icon is not None:
            gamepad_icon.mirrored = bool(new_val)

    def open_doc_popup(self, text: str) -> None:
        """EN: Open "About" document loaded from backend API.
        RU: Р С›РЎвЂљР С”РЎР‚РЎвЂ№РЎвЂљРЎРЉ Р Т‘Р С•Р С”РЎС“Р СР ВµР Р…РЎвЂљ "Р С› Р Р…Р В°РЎРѓ", Р В·Р В°Р С–РЎР‚РЎС“Р В¶Р ВµР Р…Р Р…РЎвЂ№Р в„– Р С‘Р В· backend API.

        EN: `text` argument is kept only for KV backward compatibility.
        RU: Р С’РЎР‚Р С–РЎС“Р СР ВµР Р…РЎвЂљ `text` РЎРѓР С•РЎвЂ¦РЎР‚Р В°Р Р…РЎвЂР Р… РЎвЂљР С•Р В»РЎРЉР С”Р С• Р Т‘Р В»РЎРЏ Р С•Р В±РЎР‚Р В°РЎвЂљР Р…Р С•Р в„– РЎРѓР С•Р Р†Р СР ВµРЎРѓРЎвЂљР С‘Р СР С•РЎРѓРЎвЂљР С‘ РЎРѓ KV.
        """
        _ = text
        self.open_text_doc(
            t("settings.docs.about"),
            DOC_KEY_ABOUT,
            t("common.file_not_found"),
        )

    def _read_text_doc(self, doc_key: str, missing_message: str) -> str:
        """EN: Read localized markdown document text from backend API.
        RU: Р РЋРЎвЂЎР С‘РЎвЂљР В°РЎвЂљРЎРЉ Р В»Р С•Р С”Р В°Р В»Р С‘Р В·Р С•Р Р†Р В°Р Р…Р Р…РЎвЂ№Р в„– markdown-РЎвЂљР ВµР С”РЎРѓРЎвЂљ Р Т‘Р С•Р С”РЎС“Р СР ВµР Р…РЎвЂљР В° Р С‘Р В· backend API.

        EN: Network timeout is limited to keep UI responsive.
        RU: Р СћР В°Р в„–Р СР В°РЎС“РЎвЂљ РЎРѓР ВµРЎвЂљР С‘ Р С•Р С–РЎР‚Р В°Р Р…Р С‘РЎвЂЎР ВµР Р…, РЎвЂЎРЎвЂљР С•Р В±РЎвЂ№ Р Р…Р Вµ Р В±Р В»Р С•Р С”Р С‘РЎР‚Р С•Р Р†Р В°РЎвЂљРЎРЉ UI Р Р…Р В°Р Т‘Р С•Р В»Р С–Р С•.
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
        RU: Р С›РЎвЂљР С”РЎР‚РЎвЂ№РЎвЂљРЎРЉ Р С—РЎР‚Р С•Р С”РЎР‚РЎС“РЎвЂЎР С‘Р Р†Р В°Р ВµР СРЎвЂ№Р в„– popup РЎРѓ РЎвЂљР ВµР С”РЎРѓРЎвЂљР С•Р С, Р С—Р С•Р В»РЎС“РЎвЂЎР ВµР Р…Р Р…РЎвЂ№Р С Р С‘Р В· backend API.
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
        close_btn = Button(text=t("common.close"), size_hint_y=None, height=dp(40))
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
        RU: Р С›РЎвЂљР С”РЎР‚РЎвЂ№РЎвЂљРЎРЉ Р В»Р С•Р С”Р В°Р В»Р С‘Р В·Р С•Р Р†Р В°Р Р…Р Р…РЎвЂ№Р в„– Р Т‘Р С•Р С”РЎС“Р СР ВµР Р…РЎвЂљ Р С—Р С•Р В»Р С‘РЎвЂљР С‘Р С”Р С‘ Р С‘Р В· backend API.
        """
        self.open_text_doc(
            t("settings.docs.policy"),
            DOC_KEY_POLICY,
            t("common.file_not_found"),
        )

    def open_game_rules(self) -> None:
        """EN: Open localized rules document fetched from backend API.
        RU: Р С›РЎвЂљР С”РЎР‚РЎвЂ№РЎвЂљРЎРЉ Р В»Р С•Р С”Р В°Р В»Р С‘Р В·Р С•Р Р†Р В°Р Р…Р Р…РЎвЂ№Р в„– Р Т‘Р С•Р С”РЎС“Р СР ВµР Р…РЎвЂљ Р С—РЎР‚Р В°Р Р†Р С‘Р В» Р С‘Р В· backend API.
        """
        self.open_text_doc(
            t("settings.docs.rules"),
            DOC_KEY_RULES,
            t("common.file_not_found"),
        )

    def on_delete_account_pressed(self) -> None:
        """EN: Ask for delete-account confirmation and delegate to controller on success.
        RU: Р СџР С•Р С—РЎР‚Р С•РЎРѓР С‘РЎвЂљРЎРЉ Р С—Р С•Р Т‘РЎвЂљР Р†Р ВµРЎР‚Р В¶Р Т‘Р ВµР Р…Р С‘Р Вµ РЎС“Р Т‘Р В°Р В»Р ВµР Р…Р С‘РЎРЏ Р В°Р С”Р С”Р В°РЎС“Р Р…РЎвЂљР В° Р С‘ Р Т‘Р ВµР В»Р ВµР С–Р С‘РЎР‚Р С•Р Р†Р В°РЎвЂљРЎРЉ Р С”Р С•Р Р…РЎвЂљРЎР‚Р С•Р В»Р В»Р ВµРЎР‚РЎС“ Р С—РЎР‚Р С‘ РЎС“РЎРѓР С—Р ВµРЎвЂ¦Р Вµ.
        """
        confirm_delete_account(
            on_deleted=lambda: self._controller.logout(),
            on_cancel=lambda: None,
        )

    def configure(self, vm: SettingsScreenVM, controller: SettingsScreenController) -> None:
        """EN: Configure texts and bind callbacks.
        RU: Р СњР В°РЎРѓРЎвЂљРЎР‚Р С•Р С‘РЎвЂљРЎРЉ РЎвЂљР ВµР С”РЎРѓРЎвЂљРЎвЂ№ Р С‘ Р С—РЎР‚Р С‘Р Р†РЎРЏР В·Р В°РЎвЂљРЎРЉ callback-Р С‘.
        """
        self._controller = controller
        self.ids.left_text.text = vm.title
        self.ids.login_btn_text.text = ""
        self.ids.action_btn_text.text = caps(vm.action_text)
        self.ids.back_btn_text.text = caps(vm.back_text)

        self._payout_callback = lambda *_: controller.payout()
        self._logout_callback = lambda *_: controller.logout()
        self._back_callback = lambda *_: controller.back()
        self.ids.login_btn.unbind(on_release=self._payout_callback)
        self.ids.login_btn.disabled = True
        self.ids.payout_card_icon.unbind(on_release=self._payout_callback)
        self.ids.payout_card_icon.bind(on_release=self._payout_callback)
        self.ids.action_btn.unbind(on_release=self._logout_callback)
        self.ids.action_btn.bind(on_release=self._logout_callback)
        self.ids.back_btn.unbind(on_release=self._back_callback)
        self.ids.back_btn.bind(on_release=self._back_callback)

    def start_payout_flow(self) -> None:
        """EN: Start payout bot open flow from Settings button.
        RU: Р вЂ”Р В°Р С—РЎС“РЎРѓРЎвЂљР С‘РЎвЂљРЎРЉ flow Р С•РЎвЂљР С”РЎР‚РЎвЂ№РЎвЂљР С‘РЎРЏ payout-Р В±Р С•РЎвЂљР В° Р С—Р С• Р С”Р Р…Р С•Р С—Р С”Р Вµ Р С‘Р В· Р СњР В°РЎРѓРЎвЂљРЎР‚Р С•Р ВµР С”.
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
        RU: Р С›Р С—РЎР‚Р В°РЎв‚¬Р С‘Р Р†Р В°РЎвЂљРЎРЉ `/payout/link/status`, Р С—Р С•Р С”Р В° bot ack Р Р…Р Вµ Р С—Р С•Р СР ВµРЎвЂљР С‘РЎвЂљ Р С”Р С•Р Т‘ used Р С‘Р В»Р С‘ Р Р…Р Вµ Р Р†РЎвЂ№Р в„–Р Т‘Р ВµРЎвЂљ timeout.
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
        RU: Р СџР С•Р С”Р В°Р В·Р В°РЎвЂљРЎРЉ popup Р С•Р В± Р С‘РЎРѓРЎвЂљР ВµРЎвЂЎР ВµР Р…Р С‘Р С‘ РЎРѓР ВµРЎРѓРЎРѓР С‘Р С‘, Р Р†РЎвЂ№Р С—Р С•Р В»Р Р…Р С‘РЎвЂљРЎРЉ logout Р С‘ Р С—Р ВµРЎР‚Р ВµР в„–РЎвЂљР С‘ Р Р…Р В° Login.
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
        RU: Р СџР С•Р С”Р В°Р В·Р В°РЎвЂљРЎРЉ Р С”Р С•Р СР С—Р В°Р С”РЎвЂљР Р…РЎвЂ№Р в„– Р С‘Р Р…РЎвЂћР С•РЎР‚Р СР В°РЎвЂ Р С‘Р С•Р Р…Р Р…РЎвЂ№Р в„– popup Р Т‘Р В»РЎРЏ РЎРѓР С•Р С•Р В±РЎвЂ°Р ВµР Р…Р С‘Р в„– payout flow.
        """

        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        content.add_widget(Label(text=message))
        btn = Button(text=t("common.ok"), size_hint_y=None, height=dp(40))
        content.add_widget(btn)
        popup = Popup(title="", content=content, size_hint=(0.82, 0.35), auto_dismiss=False)
        btn.bind(on_release=lambda *_: popup.dismiss())
        popup.open()

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
