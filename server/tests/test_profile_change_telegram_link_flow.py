"""EN: Tests proving that profile-change UI uses the canonical telegram_link Mini App flow.
RU: Тесты, доказывающие, что UI экрана profile-change использует канонический telegram_link Mini App flow.
"""

from __future__ import annotations

from types import SimpleNamespace

import uix.screens.profile_change.profile_change_controller as controller_module
from uix.screens.profile_change.profile_change_controller import ProfileChangeController


def test_profile_change_starts_shared_hub_request(monkeypatch) -> None:
    """EN: Profile-change controller must start Telegram linking through the shared hub Mini App request.
    RU: Контроллер profile-change должен запускать привязку Telegram через общий hub Mini App request.
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
        "telegram_hub_session_request",
        lambda entry_action, user_id=None: calls.append((f"telegram_hub_session_request:{entry_action}", int(user_id or 0))) or (True, {"ok": True, "miniapp_url": "https://t.me/escape2mars_bot/escape2mars?startapp=abc", "ttl_sec": 600}),
    )

    ProfileChangeController._start_tg_verify_flow(dummy, {"tg": "@demo_user"})

    assert calls == [
        ("telegram_hub_session_request:verify", 7),
        ("open", 0),
    ]


def test_profile_change_stops_polling_on_terminal_miniapp_status(monkeypatch) -> None:
    """EN: Profile-change polling must stop and show fail popup when Mini App session reaches terminal non-verified status.
    RU: Polling экрана profile-change должен остановиться и показать fail-popup, когда Mini App session переходит в terminal non-verified status.
    """

    calls: list[tuple[str, str]] = []

    class _DummyEvent:
        def cancel(self):
            return None

    class _ImmediateClock:
        @staticmethod
        def schedule_interval(callback, _dt=0):
            callback(0)
            return _DummyEvent()

        @staticmethod
        def schedule_once(callback, _dt=0):
            callback(0)

    dummy = SimpleNamespace(
        _tg_verify_active=True,
        _tg_verify_poll_event=None,
        _cancel_tg_events=lambda: calls.append(("cancel", "-")),
        _show_tg_fail_popup=lambda message=None: calls.append(("fail", str(message or ""))),
        _on_tg_verify_success=lambda: calls.append(("success", "-")),
        _apply_tg_snapshot_to_current_view=lambda payload: calls.append(("snapshot", "-")),
        _dbg=lambda message: calls.append(("dbg", str(message))),
    )

    monkeypatch.setattr(controller_module, "Clock", _ImmediateClock)
    monkeypatch.setattr(controller_module, "t", lambda key: key)
    monkeypatch.setattr(
        controller_module.auth_backend,
        "telegram_link_miniapp_session_status",
        lambda user_id: (True, {"ok": True, "verified": False, "status": "rejected", "expired": False, "purpose": "telegram_link"}),
    )

    ProfileChangeController._start_tg_polling(dummy, 7)

    assert ("cancel", "-") in calls
    assert ("fail", "tg.confirm_unavailable") in calls
    assert ("success", "-") not in calls
