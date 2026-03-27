"""EN: Tests proving that profile-change UI uses the canonical telegram_link Mini App flow.
RU: Тесты, доказывающие, что UI экрана profile-change использует канонический telegram_link Mini App flow.
"""

from __future__ import annotations

from types import SimpleNamespace

import uix.screens.profile_change.profile_change_controller as controller_module
from uix.screens.profile_change.profile_change_controller import ProfileChangeController


def test_profile_change_starts_telegram_link_miniapp_request(monkeypatch) -> None:
    """EN: Profile-change controller must start Telegram linking through telegram_link Mini App request only.
    RU: Контроллер profile-change должен запускать привязку Telegram только через telegram_link Mini App request.
    """

    calls: list[tuple[str, int]] = []

    class _ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self._target = target

        def start(self):
            if self._target is not None:
                self._target()

    class _ImmediateClock:
        @staticmethod
        def schedule_once(callback, _dt=0):
            callback(0)

    dummy = SimpleNamespace(
        _resolve_current_user_id=lambda: 7,
        _start_tg_verify_state=lambda user_id: None,
        _start_tg_polling=lambda user_id: calls.append(("poll", int(user_id))),
        _show_tg_fail_popup=lambda message=None: calls.append(("fail", 0)),
        _show_session_expired_popup=lambda: None,
    )

    monkeypatch.setattr(controller_module, "Thread", _ImmediateThread)
    monkeypatch.setattr(controller_module, "Clock", _ImmediateClock)
    monkeypatch.setattr(controller_module, "open_telegram_miniapp", lambda url: calls.append(("open", 0)) or (True, None))
    monkeypatch.setattr(controller_module, "trace_log", lambda *args, **kwargs: None)
    monkeypatch.setattr(controller_module, "trace_exception", lambda *args, **kwargs: None)
    monkeypatch.setattr(controller_module, "tglog", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        controller_module.auth_backend,
        "telegram_link_miniapp_session_request",
        lambda user_id: calls.append(("telegram_link_miniapp_session_request", int(user_id))) or (True, {"ok": True, "miniapp_url": "https://t.me/payprotect_bot/verify?startapp=abc", "ttl_sec": 600}),
    )

    ProfileChangeController._start_tg_verify_flow(dummy, {"tg": "@demo_user"})

    assert calls == [
        ("telegram_link_miniapp_session_request", 7),
        ("open", 0),
        ("poll", 7),
    ]
