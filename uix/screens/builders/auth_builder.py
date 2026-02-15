"""EN: Builder for the authentication flow screens.
RU: Сборщик экранов потока аутентификации.
"""

from manager.lang.lang_manager import t
from uix.screens import routes
from uix.screens.auth.login.login_controller import LoginController
from uix.screens.auth.login.login_vm import LoginVM
from uix.screens.auth.login.login_view import LoginScreenView
from uix.screens.auth.register.register_controller import RegisterController
from uix.screens.auth.register.register_vm import RegisterVM
from uix.screens.auth.register.register_view import RegisterScreenView
from uix.screens.game.game_controller import GameScreenController
from uix.screens.game.game_vm import GameScreenVM
from uix.screens.game.game_view import GameScreenView
from uix.screens.profile.profile_controller import ProfileScreenController
from uix.screens.profile.profile_vm import ProfileScreenVM
from uix.screens.profile.profile_view import ProfileScreenView
from uix.screens.profile_change.profile_change_controller import ProfileChangeController
from uix.screens.profile_change.profile_change_vm import ProfileChangeVM
from uix.screens.profile_change.profile_change_view import ProfileChangeView
from uix.screens.load_app.load_app_view import LoadAppScreenView
from uix.screens.routes import GAME, LOAD_APP, LOGIN, PROFILE, PROFILE_CHANGE, REGISTER, SETTINGS, START
from uix.screens.screen_manager import AppScreenManager
from uix.screens.settings.settings_controller import SettingsScreenController
from uix.screens.settings.settings_vm import SettingsScreenVM
from uix.screens.settings.settings_view import SettingsScreenView
from uix.screens.start.start_controller import StartScreenController
from uix.screens.start.start_vm import StartScreenVM
from uix.screens.start.start_view import StartScreenView


def build_auth_flow(manager: AppScreenManager) -> None:
    """EN: Build login/register screens and wire navigation callbacks.
    RU: Построить экраны входа/регистрации и связать навигацию.
    """
    load_view = LoadAppScreenView(manager, name=LOAD_APP)
    manager.register(load_view)

    start_vm = StartScreenVM(
        title=t("app.title"),
        game_text=t("start.btn_game"),
        profile_text=t("start.btn_profile"),
        settings_text=t("start.btn_settings"),
    )
    start_controller = StartScreenController(
        on_game=lambda: manager.go(GAME),
        on_profile=lambda: manager.go(PROFILE),
        on_settings=lambda: manager.go(SETTINGS),
    )
    start_view = StartScreenView(name=START)
    start_view.configure(start_vm, start_controller)

    profile_vm = ProfileScreenVM(
        title=t("profile.title"),
        back_text=t("common.back"),
        payout_text=t("profile.btn_payout"),
        login_text=t("profile.btn_edit"),
    )
    profile_controller = ProfileScreenController(on_back=lambda: manager.go(START))
    profile_view = ProfileScreenView(name=PROFILE)
    profile_view.configure(profile_vm, profile_controller)

    profile_change_vm = ProfileChangeVM()
    profile_change_vm.title = t("profile_change.title")
    profile_change_vm.field_login = t("profile_change.field.login")
    profile_change_vm.field_email = t("profile_change.field.email")
    profile_change_vm.field_phone = t("profile_change.field.phone")
    profile_change_vm.field_tg = t("profile_change.field.tg")
    profile_change_vm.field_password = t("profile_change.field.password")
    profile_change_vm.btn_ok = t("profile_change.btn_ok")
    profile_change_vm.btn_delete = t("profile_change.btn_delete")
    profile_change_vm.btn_back = t("profile_change.btn_back")
    profile_change_controller = ProfileChangeController()
    profile_change_view = ProfileChangeView(name=PROFILE_CHANGE)
    profile_change_view.configure(profile_change_vm, profile_change_controller)

    settings_vm = SettingsScreenVM(
        title=t("settings.title"),
        back_text=t("common.back"),
        login_text=t("settings.btn_logout"),
        action_text=t("settings.btn_action"),
    )
    settings_controller = SettingsScreenController(
        on_back=manager.back,
        on_payout=lambda: None,
        on_logout=lambda: manager.go(LOGIN),
    )
    settings_view = SettingsScreenView(name=SETTINGS)
    settings_view.configure(settings_vm, settings_controller)

    login_vm = LoginVM(
        title=t("login.title"),
        email_hint=t("login.hint_email"),
        password_hint=t("login.hint_password"),
        login_text=t("login.btn_login"),
        register_text=t("login.btn_register"),
        forgot_text=t("login.btn_forgot"),
    )
    login_controller = LoginController(
        on_login=lambda: manager.go(routes.START),
        on_forgot=lambda: None,
        on_register=lambda: manager.go(REGISTER),
    )
    login_view = LoginScreenView(name=LOGIN)
    login_view.configure(login_vm, login_controller)

    register_vm = RegisterVM(
        title_text=t("register.title"),
        email_hint=t("register.hint_email"),
        password_hint=t("register.hint_password"),
        password2_hint=t("register.hint_password2"),
        create_text=t("register.btn_create"),
        login_text=t("register.btn_to_login"),
    )
    register_controller = RegisterController(
        on_create=lambda: manager.go(LOGIN),
        on_to_login=lambda: manager.go(LOGIN),
    )
    register_view = RegisterScreenView(name=REGISTER)
    register_view.configure(register_vm, register_controller)

    game_vm = GameScreenVM(
        title=t("game.title"),
        game_text=t("game.btn_start"),
        back_text=t("common.back"),
    )
    game_controller = GameScreenController(
        on_show_hud=lambda: None,
        on_hide_hud=lambda: None,
        on_back=manager.back,
    )
    game_view = GameScreenView(name=GAME)
    game_view.configure(game_vm, game_controller)
    manager.register(start_view)
    manager.register(login_view)
    manager.register(register_view)
    manager.register(settings_view)
    manager.register(profile_view)
    manager.register(profile_change_view)
    manager.register(game_view)
