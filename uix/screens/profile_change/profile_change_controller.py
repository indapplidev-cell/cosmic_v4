"""EN: Controller for profile change screen actions.
RU: Контроллер действий экрана редактирования профиля.
"""

from __future__ import annotations

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivymd.app import MDApp
from manager.lang.lang_manager import t

from data.format.phone import attach_phone_mask, format_phone, normalize_phone
from manager.profile_change.profile_change_manager import ProfileChangeManager
from uix.screens.common.password_eye import wire_password_eye
from uix.screens.common.bottom_bar_buttons import apply_bottom_buttons
from uix.screens.layouts.layout_constants import BTN_H, ZONE_SPACING
from uix.screens.routes import PROFILE


class ProfileChangeController:
    """EN: Handle profile change actions and navigation.
    RU: Обрабатывать действия редактирования профиля и навигацию.
    """

    def __init__(self) -> None:
        """EN: Initialize manager and app reference for data changes and routing.
        RU: Инициализировать менеджер и ссылку на приложение для изменений данных и роутинга.
        """
        self._manager = ProfileChangeManager()
        self._app = MDApp.get_running_app()

    def bind(self, view) -> None:
        """EN: Bind bottom buttons, styles, and handlers for edit/delete/back actions.
        RU: Привязать нижние кнопки, стили и обработчики для действий изменить/удалить/назад.
        """
        self._view = view
        ids = view.ids
        apply_bottom_buttons(
            bottombar=ids.bottombar,
            bottom_center=ids.bottom_center,
            btn_stack=ids.btn_stack,
            buttons=[ids.ok_btn, ids.delete_btn, ids.back_btn],
            btn_h_dp=dp(BTN_H),
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
        RU: Предзаполнить поля из кэша и показать email сессии в right top bar.
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
        RU: Применить выбранные непустые изменения, оставить пользователя на текущем экране и показать popup об успехе.
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
        self._manager.apply_patch(changes)
        self._refresh_right_login()
        self._show_changed_popup()

    def on_delete(self) -> None:
        """EN: Clear selected allowed fields (login/phone/tg), block email/password deletion, and show popups.
        RU: Очистить выбранные разрешенные поля (login/phone/tg), запретить удаление email/password и показать popup.
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
        RU: Очистить поля редактирования и вернуться на экран профиля без дополнительных форс-обновлений.
        """
        view = self._view
        view.ids.inp_login.text = ""
        view.ids.inp_email.text = ""
        view.ids.inp_phone.text = ""
        view.ids.inp_tg.text = ""
        view.ids.inp_password.text = ""
        self._app.change_screen(PROFILE)

    def _refresh_right_login(self) -> None:
        """EN: Reload current cache and update right top text with login or localized no-data fallback.
        RU: Перечитать текущий кэш и обновить right top текст логином или локализованным fallback no-data.
        """
        current = self._manager.load_current_user_data() or {}
        login_val = (current.get("login") or "").strip()
        self._view.right_text = login_val if login_val else t("common.no_data")

    def _show_popup(self, message: str) -> None:
        """EN: Show modal popup with a message and one OK button, matching register popup style.
        RU: Показать модальный popup с сообщением и одной кнопкой OK в стиле popup экрана регистрации.
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
        RU: Показать popup об изменении данных и сбросить все чекбоксы редактирования после нажатия OK.
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
        RU: Снять все чекбоксы редактирования на экране изменения профиля.
        """
        ids = self._view.ids
        for name in ("chk_login", "chk_email", "chk_phone", "chk_tg", "chk_password"):
            cb = ids.get(name)
            if cb is not None:
                cb.active = False

    def attach_view(self, view) -> None:
        """EN: Attach view reference for handlers and helper methods.
        RU: Подключить ссылку на view для обработчиков и вспомогательных методов.
        """
        self._view = view
