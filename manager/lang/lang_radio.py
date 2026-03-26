from __future__ import annotations

from kivy.clock import Clock
from kivy.utils import platform as kivy_platform
from kivy.uix.textinput import TextInput
from kivymd.app import MDApp

from manager.lang.hint_text_refresh import (
    refresh_all_hint_texts,
    refresh_kivy_textinput_hint,
    refresh_md_textfield_hint,
)
from manager.lang.lang_manager import lang, t, topbar_value_text
from uix.screens import routes
from uix.screens.common.button_text_style import caps


_SHELL_TITLE_KEYS = {
    routes.LOGIN: "shell.title.login",
    routes.REGISTER: "shell.title.register",
    routes.START: "shell.title.start",
    routes.PROFILE: "shell.title.profile",
    routes.PROFILE_CHANGE: "shell.title.profile_change",
    routes.SETTINGS: "shell.title.settings",
    routes.GAME: "shell.title.game",
}


def bind_lang_radios(ru_radio, en_radio) -> None:
    """
    EN: Bind RU/EN radio checkboxes to language manager with immediate UI refresh.
    RU: Привязывает RU/EN радиобоксы к менеджеру языка с мгновенным обновлением UI.
    """
    if getattr(ru_radio, "_lang_bound", False):
        return
    ru_radio._lang_bound = True
    en_radio._lang_bound = True

    syncing = {"v": False}

    def sync_radios_from_lang() -> None:
        syncing["v"] = True
        try:
            code = (lang.code or "ru").lower()
            ru_radio.active = code == "ru"
            en_radio.active = code == "en"
        finally:
            syncing["v"] = False

    def apply_language(code: str) -> None:
        old_no_data = t("common.no_data")
        lang.set_lang(code, persist=True)
        _refresh_all_screens(old_no_data)
        sync_radios_from_lang()

    def on_ru(_inst, val: bool) -> None:
        if syncing["v"] or not val:
            return
        apply_language("ru")

    def on_en(_inst, val: bool) -> None:
        if syncing["v"] or not val:
            return
        apply_language("en")

    ru_radio.bind(active=on_ru)
    en_radio.bind(active=on_en)

    sync_radios_from_lang()


def _refresh_all_screens(old_no_data: str) -> None:
    """
    EN: Refreshes translatable UI labels on registered screens without touching user input text.
    RU: Обновляет переводимые UI-тексты на зарегистрированных экранах, не меняя введённые данные.
    """
    app = MDApp.get_running_app()
    manager = getattr(app, "_manager", None)
    if not manager:
        return

    def get_screen_safe(name: str):
        try:
            return manager.get_screen(name)
        except Exception:
            return None

    start = get_screen_safe(routes.START)
    settings = get_screen_safe(routes.SETTINGS)
    profile = get_screen_safe(routes.PROFILE)
    profile_change = get_screen_safe(routes.PROFILE_CHANGE)
    game = get_screen_safe(routes.GAME)
    login = get_screen_safe(routes.LOGIN)
    register = get_screen_safe(routes.REGISTER)
    # --- START ---
    if start and hasattr(start, "ids"):
        if "title_lbl" in start.ids:
            start.ids.title_lbl.text = t("app.title")
        if "game_btn_text" in start.ids:
            start.ids.game_btn_text.text = caps(t("start.btn_game"))
        if "profile_btn_text" in start.ids:
            start.ids.profile_btn_text.text = caps(t("start.btn_profile"))
        if "settings_btn_text" in start.ids:
            start.ids.settings_btn_text.text = caps(t("start.btn_settings"))
        _refresh_banner_slot(start)

    # --- SETTINGS ---
    if settings and hasattr(settings, "ids"):
        if "left_text" in settings.ids:
            settings.ids.left_text.text = t("settings.title")
        if "login_btn_text" in settings.ids:
            settings.ids.login_btn_text.text = caps(t("settings.btn_logout"))
        if "action_btn_text" in settings.ids:
            settings.ids.action_btn_text.text = caps(t("settings.btn_action"))
        if "back_btn_text" in settings.ids:
            settings.ids.back_btn_text.text = caps(t("common.back"))

        if "doc_rules" in settings.ids:
            settings.ids.doc_rules.text = t("settings.docs.rules")
        if "doc_policy" in settings.ids:
            settings.ids.doc_policy.text = t("settings.docs.policy")
        if "doc_about" in settings.ids:
            settings.ids.doc_about.text = t("settings.docs.about")

        if "settings_top_right_login" in settings.ids:
            if settings.ids.settings_top_right_login.text == old_no_data:
                settings.ids.settings_top_right_login.text = t("common.no_data")

        if "lang_ru_lbl" in settings.ids:
            settings.ids.lang_ru_lbl.text = t("settings.lang.ru")
        if "lang_en_lbl" in settings.ids:
            settings.ids.lang_en_lbl.text = t("settings.lang.en")
        if "delete_account_lbl" in settings.ids:
            settings.ids.delete_account_lbl.text = t("settings.delete_account")

        _refresh_banner_slot(settings)

    # --- LOGIN ---
    if login and hasattr(login, "ids"):
        if "title_lbl" in login.ids:
            login.ids.title_lbl.text = t("login.title")
        if "email_hint" in login.ids:
            login.ids.email_hint.text = t("login.hint_email")
            if "email_field" in login.ids:
                _sync_hint_to_textinput(login.ids.email_field, login.ids.email_hint)
        if "password_hint" in login.ids:
            login.ids.password_hint.text = t("login.hint_password")
            if "password_field" in login.ids:
                _sync_hint_to_textinput(login.ids.password_field, login.ids.password_hint)
        if "forgot_btn_text" in login.ids:
            login.ids.forgot_btn_text.text = caps(t("login.btn_forgot"))
        if "login_btn_text" in login.ids:
            login.ids.login_btn_text.text = caps(t("login.btn_login"))
        if "register_btn_text" in login.ids:
            login.ids.register_btn_text.text = caps(t("login.btn_register"))
        _force_refresh_screen_hints(login)

    # --- REGISTER ---
    if register and hasattr(register, "ids"):
        if "title_lbl" in register.ids:
            register.ids.title_lbl.text = t("register.title")
        if "email_hint" in register.ids:
            register.ids.email_hint.text = t("register.hint_email")
            if "register_email_field" in register.ids:
                _sync_hint_to_textinput(register.ids.register_email_field, register.ids.email_hint)
        if "password_hint" in register.ids:
            register.ids.password_hint.text = t("register.hint_password")
            if "register_password_field" in register.ids:
                _sync_hint_to_textinput(register.ids.register_password_field, register.ids.password_hint)
        if "password2_hint" in register.ids:
            register.ids.password2_hint.text = t("register.hint_password2")
            if "register_password2_field" in register.ids:
                _sync_hint_to_textinput(register.ids.register_password2_field, register.ids.password2_hint)
        if "create_btn_text" in register.ids:
            register.ids.create_btn_text.text = caps(t("register.btn_create"))
        if "to_login_btn_text" in register.ids:
            register.ids.to_login_btn_text.text = caps(t("register.btn_to_login"))
        _force_refresh_screen_hints(register)

    # --- PROFILE ---
    if profile and hasattr(profile, "ids"):
        if hasattr(profile, "vm") and profile.vm:
            try:
                profile.vm.title = t("profile.title")
                profile.vm.back_text = t("common.back")
                profile.vm.payout_text = t("profile.btn_payout")
                profile.vm.login_text = t("profile.btn_edit")
            except Exception:
                pass

        if "profile_top_left_title" in profile.ids:
            profile.ids.profile_top_left_title.text = t("profile.title")
        if "back_label" in profile.ids:
            profile.ids.back_label.text = caps(t("common.back"))
        if "payout_label" in profile.ids:
            profile.ids.payout_label.text = caps(t("profile.btn_payout"))
        if "login_label" in profile.ids:
            profile.ids.login_label.text = caps(t("profile.btn_edit"))

        if hasattr(profile, "controller") and profile.controller:
            profile.controller.refresh_profile_cards(profile)

        _refresh_banner_slot(profile)

    # --- PROFILE_CHANGE ---
    if profile_change and hasattr(profile_change, "vm") and profile_change.vm:
        profile_change.vm.title = t("profile_change.title")
        profile_change.vm.field_login = t("profile_change.field.login")
        profile_change.vm.field_email = t("profile_change.field.email")
        profile_change.vm.field_phone = t("profile_change.field.phone")
        profile_change.vm.field_tg = t("profile_change.field.tg")
        profile_change.vm.field_password = t("profile_change.field.password")
        profile_change.vm.btn_ok = t("profile_change.btn_ok")
        profile_change.vm.btn_delete = t("profile_change.btn_delete")
        profile_change.vm.btn_back = t("profile_change.btn_back")

        if hasattr(profile_change, "ids"):
            ids = profile_change.ids
            if "title_lbl" in ids:
                ids.title_lbl.text = t("profile_change.title")
            if "hint_login" in ids:
                ids.hint_login.text = t("profile_change.field.login")
                if "inp_login" in ids:
                    _sync_hint_to_textinput(ids.inp_login, ids.hint_login)
            if "hint_email" in ids:
                ids.hint_email.text = t("profile_change.field.email")
                if "inp_email" in ids:
                    _sync_hint_to_textinput(ids.inp_email, ids.hint_email)
            if "hint_phone" in ids:
                ids.hint_phone.text = t("profile_change.field.phone")
                if "inp_phone" in ids:
                    _sync_hint_to_textinput(ids.inp_phone, ids.hint_phone)
            if "hint_tg" in ids:
                ids.hint_tg.text = t("profile_change.field.tg")
                if "inp_tg" in ids:
                    _sync_hint_to_textinput(ids.inp_tg, ids.hint_tg)
            if "ok_label" in ids:
                ids.ok_label.text = caps(t("profile_change.btn_ok"))
            if "delete_label" in ids:
                ids.delete_label.text = caps(t("profile_change.btn_delete"))
            if "back_label" in ids:
                ids.back_label.text = caps(t("profile_change.btn_back"))

            if "profile_change_right" in ids and ids.profile_change_right.text == old_no_data:
                ids.profile_change_right.text = t("common.no_data")

        _refresh_banner_slot(profile_change)
        _force_refresh_screen_hints(profile_change)

    # --- GAME ---
    if game and hasattr(game, "ids"):
        if getattr(game, "_game_over_flag", False):
            if "title_lbl" in game.ids:
                game.ids.title_lbl.text = t("game.reward_prompt")
            if "game_btn_text" in game.ids:
                game.ids.game_btn_text.text = caps(t("game.btn_receive"))
        else:
            if "title_lbl" in game.ids:
                game.ids.title_lbl.text = t("game.title")
            if "game_btn_text" in game.ids:
                game.ids.game_btn_text.text = caps(t("game.btn_start"))

        if "back_btn_text" in game.ids:
            game.ids.back_btn_text.text = caps(t("common.back"))

        _refresh_banner_slot(game)

    _refresh_current_shell_title(manager)

    # --- FORCE HINT REFRESH VIA FOCUS-WALK ---
    try:
        screens = [start, settings, profile, profile_change, game, login, register]
        _force_focus_walk_mdtextfields(screens)
        _force_focus_walk_all_inputs(screens)
    except Exception:
        pass


def _refresh_current_shell_title(manager) -> None:
    """
    EN: Refresh the currently visible shell title after a language switch.
    RU: Обновить заголовок shell для текущего экрана после смены языка.
    """
    shell = getattr(manager, "_shell", None)
    if shell is None:
        return

    route_name = str(getattr(manager, "current", "") or "").strip().lower()
    title_key = _SHELL_TITLE_KEYS.get(route_name, "")
    if not title_key:
        return

    shell.set_title(t(title_key))
    try:
        if "top_right_user" in shell.ids:
            shell.ids.top_right_user.text = topbar_value_text(shell.ids.top_right_user.text)
    except Exception:
        pass


def _refresh_banner_slot(screen) -> None:
    """
    EN: Refresh AdsBannerSlot placeholder text in both screen-local and shared shell top-bar banner slots.
    RU: ????????? ????? ???????????? AdsBannerSlot ? ? ????????? ??????, ? ? ????? banner slot ?????? shell.
    """
    try:
        app = MDApp.get_running_app()
        manager = getattr(app, "_manager", None)
        shell = getattr(manager, "_shell", None) if manager is not None else None
        if shell is not None:
            slot = shell.ids.get("ads_banner_slot")
            if slot is not None and hasattr(slot, "ids") and "banner_text" in slot.ids:
                slot.ids.banner_text.text = t("ads.banner.placeholder")

        mid = screen.ids.get("midltopbar") if hasattr(screen, "ids") else None
        if not mid:
            return
        for child in mid.children:
            if hasattr(child, "ids") and "banner_text" in child.ids:
                child.ids.banner_text.text = t("ads.banner.placeholder")
    except Exception:
        return


def _sync_hint_to_textinput(textfield, hint_widget) -> None:
    """
    EN: Sync hint text into inner TextInput before redraw.
    RU: Синхронизирует текст хинта во внутренний TextInput перед перерисовкой.
    """

    def _do(_dt):
        # EN: Keep MDTextField and inner TextInput hint values in sync.
        # RU: Держим синхронизированными hint в MDTextField и внутреннем TextInput.
        try:
            textfield.hint_text = hint_widget.text
        except Exception:
            pass

        ti = getattr(textfield, "_text_input", None) or getattr(textfield, "text_input", None)
        if not isinstance(ti, TextInput):
            for w in textfield.walk(restrict=True):
                if isinstance(w, TextInput):
                    ti = w
                    break
        if ti:
            try:
                ti.hint_text = hint_widget.text
            except Exception:
                pass
            try:
                ti.canvas.ask_update()
            except Exception:
                pass
        refresh_md_textfield_hint(textfield)
        refresh_kivy_textinput_hint(textfield, hint_widget.text)

    Clock.schedule_once(_do, 0)


def _redraw_textfield(tf, delay: float = 0.0) -> None:
    def _do(_dt):
        if tf is None:
            return
        refresh_md_textfield_hint(tf)
        refresh_kivy_textinput_hint(tf)
        try:
            tf.do_layout()
            tf.canvas.ask_update()
        except Exception:
            pass

    Clock.schedule_once(_do, delay)


def _force_focus_walk_mdtextfields(screens) -> None:
    """
    EN: Force hint redraw by walking focus across all MDTextField widgets.
    RU: Принудительно перерисовывает hint, прогоняя фокус по всем MDTextField.

    EN: This reproduces the historically reliable workaround when MDTextField
    hint labels do not refresh after language switch.
    RU: Повторяет ранее рабочий обходной путь, когда hint-лейблы MDTextField
    не обновляются после смены языка.
    """
    fields = []
    focused_before = None
    for scr in screens:
        if not scr:
            continue
        for w in scr.walk(restrict=True):
            if w.__class__.__name__ != "MDTextField":
                continue
            fields.append(w)
            try:
                if focused_before is None and getattr(w, "focus", False):
                    focused_before = w
            except Exception:
                pass

    if not fields:
        return

    step = 0.03
    for i, tf in enumerate(fields):
        _focus_pulse_textfield(tf, delay=i * step)

    if focused_before is not None:
        def _restore_focus(_dt):
            try:
                focused_before.focus = True
            except Exception:
                pass

        Clock.schedule_once(_restore_focus, len(fields) * step + 0.03)


def _focus_pulse_textfield(tf, delay: float = 0.0) -> None:
    """
    EN: Briefly set focus on/off for one field to trigger hint layout refresh.
    RU: Кратко включает/выключает фокус поля, чтобы принудить refresh hint layout.
    """

    def _do(_dt):
        if tf is None:
            return
        try:
            tf.focus = True
            tf.focus = False
        except Exception:
            pass
        refresh_md_textfield_hint(tf)
        refresh_kivy_textinput_hint(tf)
        try:
            tf.do_layout()
            tf.canvas.ask_update()
        except Exception:
            pass

    Clock.schedule_once(_do, delay)


def _force_focus_walk_all_inputs(screens) -> None:
    """
    EN: Force a focus on/off pulse for every text input reachable from the provided screens after language switch.
    RU: ????????????? ????????? ????? ????? ??? ????????? ???? ?? ?????????? ??????? ????? ????? ?????.

    EN: This complements MDTextField-specific refresh and updates plain TextInput widgets that redraw their hint
    text only after focus transitions.
    RU: ??? ????????? refresh ??? MDTextField ? ????????? ??????? TextInput, ??????? ?????????????? hint
    ?????? ????? ????? ??????.
    """
    fields = []
    focused_before = None
    seen_ids = set()
    for scr in screens:
        if not scr:
            continue
        for widget in scr.walk(restrict=True):
            if not isinstance(widget, TextInput):
                continue
            widget_id = id(widget)
            if widget_id in seen_ids:
                continue
            seen_ids.add(widget_id)
            fields.append(widget)
            try:
                if focused_before is None and getattr(widget, "focus", False):
                    focused_before = widget
            except Exception:
                pass

    if not fields:
        return

    step = 0.03
    for i, field in enumerate(fields):
        _focus_pulse_any_textinput(field, delay=i * step)

    if focused_before is not None:
        def _restore_focus(_dt):
            try:
                focused_before.focus = True
            except Exception:
                pass

        Clock.schedule_once(_restore_focus, len(fields) * step + 0.03)



def _focus_pulse_any_textinput(field, delay: float = 0.0) -> None:
    """
    EN: Briefly set focus on/off for one generic text input to force hint redraw after a language switch.
    RU: ?????? ???????? ? ????????? ????? ? ???????? ?????????? ????, ????? ????????? ??????????? hint ????? ????? ?????.
    """

    def _do(_dt):
        if field is None:
            return
        try:
            field.focus = True
            field.focus = False
        except Exception:
            pass
        try:
            field.do_layout()
        except Exception:
            pass
        try:
            field.canvas.ask_update()
        except Exception:
            pass

    Clock.schedule_once(_do, delay)


def _force_refresh_screen_hints(screen) -> None:
    """
    EN: Force refresh of all MDTextField hint widgets on a screen after language switch.
    RU: Принудительно обновляет hint-виджеты всех MDTextField на экране после смены языка.
    """
    if not screen:
        return

    def _do(_dt):
        try:
            refresh_all_hint_texts(screen)
        except Exception:
            pass

    # EN: Do two delayed passes to catch post-layout rendering.
    # RU: Делаем два отложенных прохода, чтобы попасть в момент после layout.
    Clock.schedule_once(_do, 0)
    Clock.schedule_once(_do, 0.08)
