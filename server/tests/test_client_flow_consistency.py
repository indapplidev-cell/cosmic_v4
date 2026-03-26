"""EN: Focused client-flow consistency tests for session restore, profile-change cache rules, and password reset transport.
RU: Точечные тесты консистентности client-flow для восстановления сессии, правил profile-change cache и транспорта password reset.
"""

from __future__ import annotations

from pathlib import Path

from manager import auth_backend
from manager.lang import lang_radio
from manager.lang.lang_manager import topbar_value_text, user_value_for_storage, user_value_text
from manager.profile_change.profile_change_manager import ProfileChangeManager
from manager.session_manager import has_valid_session, sync_user_snapshot, validate_cached_session
from uix.screens.profile.profile_controller import ProfileScreenController
from uix.screens.auth.login.login_view import _login_error_text
from uix.screens.profile_change.profile_change_controller import ProfileChangeController
from uix.screens.profile_change.profile_change_view import ProfileChangeView
from uix.screens.screen_manager import _TITLE_KEYS


def test_topbar_value_text_uses_dictionary_no_data_for_legacy_placeholder() -> None:
    """EN: Top-right user text must normalize legacy `No data` placeholders via language dictionaries.
    RU: Текст пользователя в правом верхнем баре должен нормализовать legacy-заглушку `No data` через словари языка.
    """

    assert topbar_value_text("no data") == topbar_value_text("")
    assert topbar_value_text("No data") == topbar_value_text("")
    assert topbar_value_text("new_login") == topbar_value_text("")
    assert topbar_value_text("demo_login") == "demo_login"


def test_user_value_helpers_treat_legacy_placeholders_as_missing() -> None:
    """EN: Unified user-value helpers must collapse legacy placeholders to the single localized fallback.
    RU: Единые helper-функции пользовательских значений должны схлопывать legacy placeholder в единый локализованный fallback.
    """

    assert user_value_for_storage("new_login") == ""
    assert user_value_for_storage("None") == ""
    assert user_value_text("Нет данных") == user_value_text("")
    assert user_value_text("real_user") == "real_user"


def test_has_valid_session_allows_refresh_only_bootstrap() -> None:
    """EN: Session bootstrap must stay valid when refresh token exists even if local user_id is absent.
    RU: Bootstrap сессии должен считаться валидным при наличии refresh token даже если локальный user_id отсутствует.
    """

    assert has_valid_session({"user_id": 0, "refresh_token": "refresh-token"}) is True


def test_profile_change_never_restores_or_persists_password(monkeypatch) -> None:
    """EN: Profile-change cache flow must not preload password and must not write password back to local cache.
    RU: Cache-flow экрана редактирования профиля не должен предзаполнять пароль и не должен сохранять пароль обратно в локальный кэш.
    """

    writes: list[dict] = []

    monkeypatch.setattr(
        "manager.profile_change.profile_change_manager.get_user_cache",
        lambda: {
            "login": "demo",
            "email": "demo@test.com",
            "phone": "79990000000",
            "tg": "@demo",
            "password": "secret-from-cache",
        },
    )
    monkeypatch.setattr(
        "manager.profile_change.profile_change_manager.update_user_cache_fields",
        lambda patch: writes.append(dict(patch)),
    )
    monkeypatch.setattr(
        "manager.profile_change.profile_change_manager.validate_profile_user",
        lambda login, phone, tg: (True, "", ""),
    )
    monkeypatch.setattr(
        "manager.profile_change.profile_change_manager.auth_backend.get_current_user_id",
        lambda timeout=8: (True, 7),
    )
    monkeypatch.setattr(
        "manager.profile_change.profile_change_manager.auth_backend.save_profile_user",
        lambda user_id, **kwargs: True,
    )

    manager = ProfileChangeManager()
    loaded = manager.load_current_user_data()

    assert loaded["password"] != "secret-from-cache"

    result = manager.apply_patch({"login": "new_login", "password": "new-secret"})

    assert result["ok"] is True
    assert writes == [{"user_id": 7}, {"login": "new_login"}]


def test_password_reset_request_forces_telegram_channel(monkeypatch) -> None:
    """EN: Client password-reset request must always use the Telegram backend channel.
    RU: Клиентский запрос password reset всегда должен использовать Telegram-канал backend.
    """

    sent: list[dict] = []

    monkeypatch.setattr(auth_backend, "_ensure_healthcheck_once", lambda: None)

    def _fake_request(method: str, path: str, **kwargs):
        sent.append({"method": method, "path": path, "json": dict(kwargs.get("json") or {})})
        return True, {"ok": True}

    monkeypatch.setattr(auth_backend.api_client, "request", _fake_request)

    ok, payload = auth_backend.password_reset_request("user@test.com", channel="email")

    assert ok is True
    assert payload == {"ok": True}
    assert sent == [
        {
            "method": "POST",
            "path": "/auth/password/reset/request",
            "json": {"email": "user@test.com", "channel": "telegram"},
        }
    ]


def test_sync_user_snapshot_updates_legacy_game_stores(monkeypatch) -> None:
    """EN: Server snapshot sync must update legacy record/rating/balance stores to avoid UI desync after finish-session.
    RU: Синхронизация серверного snapshot должна обновлять legacy store record/rating/balance, чтобы не было рассинхрона UI после finish-session.
    """

    state = {"record": None, "rating": None, "balance": None}

    class _RecordStore:
        def set_best_score(self, value: int) -> None:
            state["record"] = int(value)

    class _RatingStorage:
        def save_points(self, value: int) -> None:
            state["rating"] = int(value)

    class _BalanceStore:
        def set_balance(self, value: float) -> None:
            state["balance"] = float(value)

    monkeypatch.setattr("manager.session_manager.update_user_cache_fields", lambda patch: None)
    monkeypatch.setattr("manager.session_manager.RecordStore", _RecordStore)
    monkeypatch.setattr("manager.session_manager.RatingStorage", _RatingStorage)
    monkeypatch.setattr("manager.session_manager.BalanceStore", _BalanceStore)

    sync_user_snapshot(
        {
            "user_id": 5,
            "email": "sync@test.com",
            "login": "sync",
            "record": 120,
            "rating": 345,
            "balance": 7.125,
        }
    )

    assert state == {"record": 120, "rating": 345, "balance": 7.125}


def test_validate_cached_session_recovers_without_local_user_id(monkeypatch) -> None:
    """EN: Startup validation must still recover a valid session when local user_id is absent but refresh-token flow is valid.
    RU: Startup-валидация должна восстанавливать валидную сессию даже без локального user_id, если refresh-token flow валиден.
    """

    synced: list[dict] = []

    monkeypatch.setattr(
        "manager.session_manager.get_user_cache",
        lambda: {"user_id": 0, "email": "", "refresh_token": "refresh-token", "access_token": "expired"},
    )
    monkeypatch.setattr(
        "manager.session_manager.auth_backend.get_current_user_snapshot",
        lambda timeout=8: (True, {"ok": True, "user": {"user_id": 9, "email": "user9@test.com"}}),
    )
    monkeypatch.setattr("manager.session_manager.sync_user_snapshot", lambda user: synced.append(dict(user)))

    result = validate_cached_session(timeout=5, allow_offline=False)

    assert result["ok"] is True
    assert result["user"]["user_id"] == 9
    assert synced == [{"user_id": 9, "email": "user9@test.com"}]


def test_profile_change_manager_syncs_without_local_email(monkeypatch) -> None:
    """EN: Profile patch sync must still reach server when local email is empty but session-backed user_id recovery works.
    RU: Синхронизация profile patch должна доходить до сервера даже при пустом local email, если session-backed user_id recovery работает.
    """

    saved: list[dict] = []

    monkeypatch.setattr("manager.profile_change.profile_change_manager.get_user_cache", lambda: {"user_id": 0, "email": ""})
    monkeypatch.setattr(
        "manager.profile_change.profile_change_manager.validate_profile_user",
        lambda login, phone, tg: (True, "", ""),
    )
    monkeypatch.setattr(
        "manager.profile_change.profile_change_manager.auth_backend.get_current_user_id",
        lambda timeout=8: (True, 11),
    )
    monkeypatch.setattr(
        "manager.profile_change.profile_change_manager.auth_backend.save_profile_user",
        lambda user_id, **kwargs: saved.append({"user_id": int(user_id), **kwargs}) or True,
    )
    monkeypatch.setattr("manager.profile_change.profile_change_manager.update_user_cache_fields", lambda patch: None)

    manager = ProfileChangeManager()
    result = manager.apply_patch({"login": "server_sync"})

    assert result["ok"] is True
    assert saved == [{"user_id": 11, "login": "server_sync"}]


def test_profile_change_controller_recovers_user_id_without_local_cache(monkeypatch) -> None:
    """EN: Telegram verify controller must recover current user id from the auth-backed snapshot when local cache id is absent.
    RU: Контроллер Telegram verify должен восстанавливать current user id через auth-backed snapshot, даже если local cache id отсутствует.
    """

    monkeypatch.setattr("uix.screens.profile_change.profile_change_controller.MDApp.get_running_app", lambda: object())
    monkeypatch.setattr(
        "uix.screens.profile_change.profile_change_controller.auth_backend.get_current_user_id",
        lambda timeout=8: (True, 14),
    )

    controller = ProfileChangeController()

    assert controller._resolve_current_user_id() == 14


def test_profile_refresh_requests_server_without_local_user_id(monkeypatch) -> None:
    """EN: Profile refresh must still call protected /auth/me even when local snapshot has no user_id.
    RU: Обновление профиля должно всё равно вызывать защищённый /auth/me, даже если в local snapshot нет user_id.
    """

    calls = {"count": 0}

    class _ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self._target = target

        def start(self):
            if self._target is not None:
                self._target()

    class _View:
        pass

    monkeypatch.setattr("uix.screens.profile.profile_controller.MDApp.get_running_app", lambda: type("A", (), {"is_logged_in": True})())
    monkeypatch.setattr("uix.screens.profile.profile_controller.Thread", _ImmediateThread)
    monkeypatch.setattr("uix.screens.profile.profile_controller.Clock.schedule_once", lambda cb, dt=0: cb())
    monkeypatch.setattr(
        "uix.screens.profile.profile_controller.auth_backend.get_current_user_snapshot",
        lambda timeout=6: calls.__setitem__("count", calls["count"] + 1) or (False, {"ok": False, "error": "NETWORK"}),
    )

    controller = ProfileScreenController()
    controller._snapshot_store = type("S", (), {"load": lambda self: {}, "save": lambda self, user: None, "get_game": lambda self: (0, 0, 0.0)})()
    view = _View()

    controller._refresh_profile_from_server_async(view)

    assert calls["count"] == 1
    assert getattr(view, "is_offline_profile", False) is True


def test_profile_change_view_disables_password_widgets() -> None:
    """EN: Profile-change view must hide and disable unsupported password-edit widgets.
    RU: View profile-change должен скрывать и отключать неподдерживаемые виджеты редактирования пароля.
    """

    class _Widget:
        def __init__(self):
            self.size_hint_y = 1
            self.height = 100
            self.opacity = 1
            self.disabled = False
            self.text = "x"
            self.active = True

    class _Ids(dict):
        def __getattr__(self, item):
            return self[item]

    view = type("DummyView", (), {})()
    view.ids = _Ids({
        "card_password": _Widget(),
        "inp_password": _Widget(),
        "chk_password": _Widget(),
        "edit_password_eye_btn": _Widget(),
    })

    ProfileChangeView._disable_password_edit_ui(view)

    assert view.ids["card_password"].height == 0
    assert view.ids["card_password"].disabled is True
    assert view.ids["inp_password"].text == ""
    assert view.ids["inp_password"].disabled is True
    assert view.ids["chk_password"].active is False
    assert view.ids["chk_password"].disabled is True
    assert view.ids["edit_password_eye_btn"].disabled is True


def test_password_reset_screen_branch_is_removed() -> None:
    """EN: Dead standalone password-reset screen branch must be removed from the runtime auth flow.
    RU: Мёртвая отдельная ветка password-reset screen должна быть удалена из runtime auth flow.
    """

    builder_source = Path("uix/screens/builders/auth_builder.py").read_text(encoding="utf-8")
    routes_source = Path("uix/screens/routes.py").read_text(encoding="utf-8")

    assert "PasswordResetScreenView" not in builder_source
    assert "manager.register(password_reset_view)" not in builder_source
    assert "PASSWORD_RESET" not in routes_source
    assert Path("uix/screens/auth/password_reset/password_reset_view.py").exists() is False


def test_lang_refresh_does_not_require_password_reset_screen(monkeypatch) -> None:
    """EN: Language refresh must work without a password-reset screen in the manager.
    RU: Обновление языка должно работать без password-reset screen в manager.
    """

    class _Ids(dict):
        def __getattr__(self, item):
            return self[item]

    class _Screen:
        def __init__(self):
            self.ids = _Ids({})
            self.vm = None

    class _Manager:
        current = "login"

        def __init__(self):
            self._shell = None
            self._screens = {
                "start": _Screen(),
                "settings": _Screen(),
                "profile": _Screen(),
                "profile_change": _Screen(),
                "game": _Screen(),
                "login": _Screen(),
                "register": _Screen(),
            }

        def get_screen(self, name):
            if name not in self._screens:
                raise KeyError(name)
            return self._screens[name]

    class _App:
        def __init__(self):
            self._manager = _Manager()

    monkeypatch.setattr(lang_radio.MDApp, "get_running_app", staticmethod(lambda: _App()))
    monkeypatch.setattr(lang_radio, "_force_focus_walk_mdtextfields", lambda screens: None)
    monkeypatch.setattr(lang_radio, "_force_focus_walk_all_inputs", lambda screens: None)

    lang_radio._refresh_all_screens("NO_DATA")


def test_screen_manager_title_map_excludes_password_reset() -> None:
    """EN: Screen manager title map must not contain the removed password-reset route.
    RU: Карта заголовков screen manager не должна содержать удалённый маршрут password-reset.
    """

    assert "password_reset" not in _TITLE_KEYS


def test_profile_change_controller_works_without_password_widgets() -> None:
    """EN: Profile-change controller must not require removed password widgets in active flows.
    RU: Контроллер profile-change не должен требовать удалённые password widgets в активных сценариях.
    """

    class _Field:
        def __init__(self, text="", active=False):
            self.text = text
            self.active = active

    class _Ids(dict):
        def __getattr__(self, item):
            return self[item]

    controller = ProfileChangeController()
    controller._manager = type(
        "StubManager",
        (),
        {
            "load_current_user_data": lambda self: {
                "login": "demo",
                "email": "demo@test.com",
                "phone": "79990000000",
                "tg": "@demo",
                "password": "secret-from-cache",
            }
        },
    )()
    controller._app = type("StubApp", (), {"change_screen": lambda self, name: None})()

    view = type("DummyView", (), {})()
    view.ids = _Ids(
        {
            "inp_login": _Field(),
            "inp_email": _Field(),
            "inp_phone": _Field(),
            "inp_tg": _Field(),
            "chk_login": _Field(active=True),
            "chk_email": _Field(active=True),
            "chk_phone": _Field(active=True),
            "chk_tg": _Field(active=True),
        }
    )
    view.right_text = ""

    controller.attach_view(view)
    controller.on_enter(view)
    controller.on_back()
    controller._reset_edit_checkboxes()

    assert view.right_text == "demo"
    assert view.ids["inp_login"].text == ""
    assert view.ids["inp_email"].text == ""
    assert view.ids["inp_phone"].text == ""
    assert view.ids["inp_tg"].text == ""
    assert view.ids["chk_login"].active is False
    assert view.ids["chk_email"].active is False
    assert view.ids["chk_phone"].active is False
    assert view.ids["chk_tg"].active is False


def test_login_error_text_preserves_server_failures() -> None:
    """EN: Login UI must not mask backend/network failures as invalid credentials.
    RU: UI входа не должен маскировать backend/network failures под неверные credentials.
    """

    invalid_credentials = _login_error_text("BAD_PASSWORD")

    assert _login_error_text("NOT_FOUND") == invalid_credentials
    assert _login_error_text("NETWORK") == "Server unavailable. Check connection / Сервер недоступен. Проверьте соединение"
    assert _login_error_text("DB_ERROR") == "Server error. Try again later / Ошибка сервера. Попробуйте позже"
    assert _login_error_text("DB_ERROR") != invalid_credentials
