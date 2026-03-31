"""EN: Tests proving that payout Mini App UI path uses the strict Telegram Mini App launcher.
RU: Тесты, доказывающие, что payout Mini App UI-path использует strict launcher Telegram Mini App.
"""

from __future__ import annotations

from types import SimpleNamespace

import uix.screens.settings.settings_view as settings_module
from uix.screens.settings.settings_view import SettingsScreenView


def test_settings_payout_flow_uses_shared_hub_miniapp(monkeypatch) -> None:
    """EN: Settings payout flow must request shared hub session and open Telegram Mini App without legacy polling.
    RU: Payout-flow экрана настроек должен запросить общую hub session и открыть Telegram Mini App без legacy polling.
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
        _show_session_expired_popup=lambda: calls.append(("expired", 0)),
        _show_info_popup=lambda _message: calls.append(("info", 0)),
        _start_payout_status_polling=lambda user_id: calls.append(("poll", int(user_id))),
        _pay_flow_active=False,
        _pay_open_started_at=0.0,
    )

    monkeypatch.setattr(settings_module, "Thread", _ImmediateThread)
    monkeypatch.setattr(settings_module, "Clock", _ImmediateClock)
    monkeypatch.setattr(settings_module, "tglog", lambda *args, **kwargs: None)
    monkeypatch.setattr(settings_module, "trace_log", lambda *args, **kwargs: None)
    monkeypatch.setattr(settings_module, "t", lambda key: key)
    monkeypatch.setattr(settings_module, "get_user_cache", lambda: {"user_id": 7})
    monkeypatch.setattr(settings_module, "open_telegram_miniapp", lambda url: calls.append(("open", 0)) or (True, None))
    monkeypatch.setattr(settings_module.auth_backend, "get_refresh_token", lambda: "refresh-token")
    monkeypatch.setattr(
        settings_module.auth_backend,
        "telegram_hub_session_request",
        lambda entry_action, user_id=None: calls.append((f"telegram_hub_session_request:{entry_action}", int(user_id or 0))) or (True, {"ok": True, "miniapp_url": "https://t.me/escape2mars_bot/escape2mars?startapp=abc", "ttl_sec": 300}),
    )

    SettingsScreenView.start_payout_flow(dummy)

    assert calls == [
        ("telegram_hub_session_request:payout", 7),
        ("open", 0),
    ]


def test_settings_payout_polling_stops_on_terminal_status(monkeypatch) -> None:
    """EN: Settings payout polling must stop and show an info popup when Mini App session becomes terminal non-verified.
    RU: Payout-polling экрана настроек должен остановиться и показать info-popup, когда Mini App session становится terminal non-verified.
    """

    calls: list[tuple[str, str]] = []

    class _DummyEvent:
        def cancel(self):
            calls.append(("cancel", "-"))

    class _ImmediateClock:
        @staticmethod
        def schedule_interval(callback, _dt=0):
            callback(0)
            return _DummyEvent()

    dummy = SimpleNamespace(
        _pay_flow_active=True,
        _pay_open_started_at=0.0,
        _pay_status_poll_event=None,
        _show_info_popup=lambda message: calls.append(("info", str(message))),
    )

    monkeypatch.setattr(settings_module, "Clock", _ImmediateClock)
    monkeypatch.setattr(settings_module, "tglog", lambda *args, **kwargs: None)
    monkeypatch.setattr(settings_module, "t", lambda key: key)
    monkeypatch.setattr(settings_module.auth_backend, "payout_miniapp_session_status", lambda user_id: (True, {"ok": True, "verified": False, "status": "rejected", "expired": False, "ttl_sec": 120}))

    SettingsScreenView._start_payout_status_polling(dummy, 7)

    assert ("info", "pay.open_fail") in calls


def test_settings_payout_flow_does_not_poll_when_launcher_result_is_uncertain(monkeypatch) -> None:
    """EN: Settings payout flow must not start polling when launcher cannot prove usable Mini App opening.
    RU: Settings payout flow не должен запускать polling, если launcher не может доказать usable-открытие Mini App.
    """

    calls: list[tuple[str, int | str]] = []

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
        _show_session_expired_popup=lambda: calls.append(("expired", 0)),
        _show_info_popup=lambda message: calls.append(("info", str(message))),
        _start_payout_status_polling=lambda user_id: calls.append(("poll", int(user_id))),
        _pay_flow_active=False,
        _pay_open_started_at=0.0,
    )

    monkeypatch.setattr(settings_module, "Thread", _ImmediateThread)
    monkeypatch.setattr(settings_module, "Clock", _ImmediateClock)
    monkeypatch.setattr(settings_module, "tglog", lambda *args, **kwargs: None)
    monkeypatch.setattr(settings_module, "trace_log", lambda *args, **kwargs: None)
    monkeypatch.setattr(settings_module, "t", lambda key: key)
    monkeypatch.setattr(settings_module, "get_user_cache", lambda: {"user_id": 7})
    monkeypatch.setattr(settings_module, "open_telegram_miniapp", lambda url: (False, "MINIAPP_OPEN_UNCERTAIN"))
    monkeypatch.setattr(settings_module.auth_backend, "get_refresh_token", lambda: "refresh-token")
    monkeypatch.setattr(
        settings_module.auth_backend,
        "telegram_hub_session_request",
        lambda entry_action, user_id=None: (True, {"ok": True, "miniapp_url": "https://t.me/escape2mars_bot/escape2mars?startapp=abc", "ttl_sec": 300}),
    )

    SettingsScreenView.start_payout_flow(dummy)

    assert ("poll", 7) not in calls
    assert ("info", "pay.open_fail") in calls
