"""EN: Tests proving that forgot-password UI enters the shared Telegram hub Mini App.
RU: Тесты, доказывающие, что UI восстановления пароля входит в общий Telegram hub Mini App.
"""

from __future__ import annotations

from types import SimpleNamespace

import uix.screens.auth.login.login_view as login_module
from uix.screens.auth.login.login_view import LoginScreenView


def test_login_forgot_password_uses_shared_hub(monkeypatch) -> None:
    """EN: Forgot-password button must request hub session and open Telegram Mini App instead of bot chat.
    RU: Кнопка восстановления пароля должна запрашивать hub session и открывать Telegram Mini App вместо bot chat.
    """

    calls: list[tuple[str, str]] = []
    dummy = SimpleNamespace(
        ids=SimpleNamespace(email_field=SimpleNamespace(text="u@test.com")),
        set_error=lambda message: calls.append(("error", str(message))),
        _show_simple_popup=lambda message: calls.append(("popup", str(message))),
    )

    monkeypatch.setattr(login_module, "t", lambda key: key)
    monkeypatch.setattr(
        login_module.auth_backend,
        "telegram_hub_session_request",
        lambda entry_action, email=None: calls.append((f"telegram_hub_session_request:{entry_action}", str(email or "")))
        or (True, {"ok": True, "miniapp_url": "https://t.me/escape2mars_bot/escape2mars?startapp=opaque"}),
    )
    monkeypatch.setattr(
        login_module,
        "open_telegram_miniapp",
        lambda url: calls.append(("open_telegram_miniapp", str(url))) or (True, None),
    )

    LoginScreenView._on_forgot_pressed(dummy)

    assert calls == [
        ("telegram_hub_session_request:reset", "u@test.com"),
        ("open_telegram_miniapp", "https://t.me/escape2mars_bot/escape2mars?startapp=opaque"),
    ]


def test_login_forgot_password_shows_popup_when_launcher_uncertain(monkeypatch) -> None:
    """EN: Forgot-password UI must not pretend success when Telegram Mini App open is uncertain.
    RU: UI восстановления пароля не должен притворяться успешным, когда открытие Telegram Mini App uncertain.
    """

    calls: list[tuple[str, str]] = []
    dummy = SimpleNamespace(
        ids=SimpleNamespace(email_field=SimpleNamespace(text="u@test.com")),
        set_error=lambda message: calls.append(("error", str(message))),
        _show_simple_popup=lambda message: calls.append(("popup", str(message))),
    )

    monkeypatch.setattr(login_module, "t", lambda key: key)
    monkeypatch.setattr(
        login_module.auth_backend,
        "telegram_hub_session_request",
        lambda entry_action, email=None: (True, {"ok": True, "miniapp_url": "https://t.me/escape2mars_bot/escape2mars?startapp=opaque"}),
    )
    monkeypatch.setattr(login_module, "open_telegram_miniapp", lambda url: (False, "MINIAPP_OPEN_UNCERTAIN"))

    LoginScreenView._on_forgot_pressed(dummy)

    assert calls == [("popup", "pay.open_fail")]
