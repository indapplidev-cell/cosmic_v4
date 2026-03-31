"""EN: Tests for strict Telegram Mini App launcher without browser fallback.
RU: Тесты strict launcher-а Telegram Mini App без browser fallback.
"""

from __future__ import annotations

import manager.telegram_deeplink as deeplink


def test_open_telegram_miniapp_uses_strict_tg_target_without_browser(monkeypatch) -> None:
    """EN: Mini App launcher must resolve a Telegram-app scheme target and never call web fallback.
    RU: Launcher Mini App должен собирать target схемы Telegram-app и никогда не вызывать web fallback.
    """

    captured: dict[str, str] = {}

    monkeypatch.setattr(deeplink, "tglog", lambda *args, **kwargs: None)
    monkeypatch.setattr(deeplink, "trace_log", lambda *args, **kwargs: None)
    monkeypatch.setattr(deeplink, "trace_exception", lambda *args, **kwargs: None)
    monkeypatch.setattr(deeplink, "open_web", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("web fallback forbidden")))

    def _fake_open_tg_target(tg_url: str) -> tuple[bool, str | None]:
        captured["tg_url"] = tg_url
        return True, None

    monkeypatch.setattr(deeplink, "_open_miniapp_tg_target", _fake_open_tg_target)

    attempted, error = deeplink.open_telegram_miniapp("https://t.me/escape2mars_bot/escape2mars?startapp=opaque-token")

    assert attempted is True
    assert error is None
    assert captured["tg_url"] == "tg://resolve?domain=escape2mars_bot&appname=escape2mars&startapp=opaque-token"


def test_open_telegram_miniapp_returns_launch_error_without_browser_fallback(monkeypatch) -> None:
    """EN: Mini App launcher must return honest launch failure and not open a browser when Telegram app launch fails.
    RU: Launcher Mini App должен честно возвращать ошибку запуска и не открывать браузер, если запуск Telegram app не удался.
    """

    monkeypatch.setattr(deeplink, "tglog", lambda *args, **kwargs: None)
    monkeypatch.setattr(deeplink, "trace_log", lambda *args, **kwargs: None)
    monkeypatch.setattr(deeplink, "trace_exception", lambda *args, **kwargs: None)
    monkeypatch.setattr(deeplink, "open_web", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("web fallback forbidden")))
    monkeypatch.setattr(deeplink, "_open_miniapp_tg_target", lambda _tg_url: (False, "TG_APP_NOT_AVAILABLE"))

    attempted, error = deeplink.open_telegram_miniapp("https://t.me/escape2mars_bot/escape2mars?startapp=opaque-token")

    assert attempted is False
    assert error == "TG_APP_NOT_AVAILABLE"


def test_open_telegram_miniapp_tries_multiple_strict_desktop_targets(monkeypatch) -> None:
    """EN: Mini App launcher must try strict Telegram-app targets in order before failing.
    RU: Launcher Mini App должен по порядку пробовать strict-target-ы Telegram app перед финальным fail.
    """

    attempted_targets: list[str] = []

    monkeypatch.setattr(deeplink, "tglog", lambda *args, **kwargs: None)
    monkeypatch.setattr(deeplink, "trace_log", lambda *args, **kwargs: None)
    monkeypatch.setattr(deeplink, "trace_exception", lambda *args, **kwargs: None)
    monkeypatch.setattr(deeplink, "open_web", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("web fallback forbidden")))

    def _fake_open_tg_target(tg_url: str) -> tuple[bool, str | None]:
        attempted_targets.append(tg_url)
        if len(attempted_targets) == 1:
            return False, "TG_SCHEME_UNSUPPORTED"
        return True, None

    monkeypatch.setattr(deeplink, "_open_miniapp_tg_target", _fake_open_tg_target)

    attempted, error = deeplink.open_telegram_miniapp("https://t.me/escape2mars_bot/escape2mars?startapp=opaque-token")

    assert attempted is True
    assert error is None
    assert attempted_targets == [
        "tg://resolve?domain=escape2mars_bot&appname=escape2mars&startapp=opaque-token",
        "telegram://resolve?domain=escape2mars_bot&appname=escape2mars&startapp=opaque-token",
    ]


def test_open_telegram_miniapp_rejects_invalid_strategy_target(monkeypatch) -> None:
    """EN: Mini App launcher must not report success for an invalid bot/Mini App target even if a strategy list is provided.
    RU: Launcher Mini App не должен считать запуск успешным для невалидного bot/Mini App target, даже если strategy list построен.
    """

    monkeypatch.setattr(deeplink, "tglog", lambda *args, **kwargs: None)
    monkeypatch.setattr(deeplink, "trace_log", lambda *args, **kwargs: None)
    monkeypatch.setattr(deeplink, "trace_exception", lambda *args, **kwargs: None)
    monkeypatch.setattr(deeplink, "open_web", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("web fallback forbidden")))
    monkeypatch.setattr(
        deeplink,
        "_build_miniapp_launch_strategies",
        lambda bot_username, short_name, start_param: [deeplink.MiniAppLaunchStrategy(name="invalid", target="tg://resolve?domain=escape2mars_bot")],
    )
    monkeypatch.setattr(
        deeplink,
        "_open_miniapp_tg_target",
        lambda _tg_url: (_ for _ in ()).throw(AssertionError("invalid target must not be opened")),
    )

    attempted, error = deeplink.open_telegram_miniapp("https://t.me/escape2mars_bot/escape2mars?startapp=opaque-token")

    assert attempted is False
    assert error == "TG_TARGET_INVALID"


def test_open_telegram_miniapp_returns_uncertain_when_os_opener_only_succeeds(monkeypatch) -> None:
    """EN: Desktop OS opener success alone must not count as proven Mini App success.
    RU: Сам по себе успех desktop OS opener не должен считаться доказанным успехом Mini App.
    """

    monkeypatch.setattr(deeplink, "tglog", lambda *args, **kwargs: None)
    monkeypatch.setattr(deeplink, "trace_log", lambda *args, **kwargs: None)
    monkeypatch.setattr(deeplink, "trace_exception", lambda *args, **kwargs: None)
    monkeypatch.setattr(deeplink, "_open_miniapp_tg_target", lambda _tg_url: (False, "MINIAPP_OPEN_UNCERTAIN"))

    attempted, error = deeplink.open_telegram_miniapp("https://t.me/escape2mars_bot/escape2mars?startapp=opaque-token")

    assert attempted is False
    assert error == "MINIAPP_OPEN_UNCERTAIN"
