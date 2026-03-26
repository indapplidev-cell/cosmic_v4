"""EN: Tests proving that profile-change UI uses the canonical telegram link flow.
RU: Тесты, доказывающие, что UI экрана profile-change использует канонический telegram link flow.
"""

from __future__ import annotations

from types import SimpleNamespace

import uix.screens.profile_change.profile_change_controller as controller_module
from uix.screens.profile_change.profile_change_controller import ProfileChangeController


def test_profile_change_starts_telegram_link_request(monkeypatch) -> None:
    """EN: Profile-change controller must request Telegram linking through telegram_link_request only.
    RU: Контроллер profile-change должен запускать привязку Telegram только через telegram_link_request.
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
        _show_tg_enter_code_popup=lambda user_id: None,
        _show_session_expired_popup=lambda: None,
        _mask_token=lambda token: token,
    )

    monkeypatch.setattr(controller_module, "Thread", _ImmediateThread)
    monkeypatch.setattr(controller_module, "Clock", _ImmediateClock)
    monkeypatch.setattr(controller_module, "open_bot_two_stage", lambda *args, **kwargs: None)
    monkeypatch.setattr(controller_module, "trace_log", lambda *args, **kwargs: None)
    monkeypatch.setattr(controller_module, "trace_exception", lambda *args, **kwargs: None)
    monkeypatch.setattr(controller_module, "tglog", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        controller_module.auth_backend,
        "telegram_link_request",
        lambda user_id: calls.append(("telegram_link_request", int(user_id))) or (True, {"ok": True, "code": "ABC123", "ttl_sec": 600}),
    )

    ProfileChangeController._start_tg_verify_flow(dummy, {"tg": "@demo_user"})

    assert calls == [("telegram_link_request", 7)]
