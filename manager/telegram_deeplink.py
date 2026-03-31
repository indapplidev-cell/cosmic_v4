from __future__ import annotations

"""EN: Telegram deep-link helpers for opening bot chat with code.
RU: Хелперы Telegram deep-link для открытия чата бота с code.
"""

import logging
import os
import subprocess
import sys
import webbrowser
from dataclasses import dataclass
from time import time
from urllib.parse import parse_qs, quote_plus, urlsplit, urlunsplit, urlencode

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import platform as kivy_platform

from manager import app_focus_tracker
from manager.config import DELAY_RETRY_MS, TG_DEBUG_FLOW, TELEGRAM_BOT_USERNAME, TG_OPEN_TIMEOUT_SEC
from manager.trace import TraceManager, trace_exception, trace_log
from manager.tg_debug_log import tglog

_LOG = logging.getLogger("cosmic.telegram_deeplink")
_OPEN_FLOW_EVENTS: dict[str, dict[str, object]] = {}
_TG_ANDROID_PACKAGE = "org.telegram.messenger"


@dataclass(frozen=True)
class MiniAppLaunchStrategy:
    """EN: One strict Telegram-app launch strategy for a Mini App target.
    RU: Одна strict-стратегия запуска Mini App target через приложение Telegram.
    """

    name: str
    target: str


def _mask_url(url: str) -> str:
    """EN: Mask `start` query value when debug is disabled.
    RU: Маскировать значение `start` в query, если debug выключен.
    """

    if TG_DEBUG_FLOW:
        return str(url)
    try:
        parts = urlsplit(str(url))
        query = parse_qs(parts.query, keep_blank_values=True)
        if "start" in query and query["start"]:
            query["start"] = ["****"]
        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query, doseq=True), parts.fragment))
    except Exception:
        return str(url)


def _masked_code(code: str) -> str:
    """EN: Return masked deep-link code for logs/traces.
    RU: Вернуть маскированный deep-link code для логов/трейсов.
    """

    return TraceManager.instance().mask_code(str(code or ""))


def build_urls(bot: str | None, code: str) -> tuple[str, str]:
    """EN: Build tg:// and https://t.me URLs from bot username and code.
    RU: Собрать tg:// и https://t.me URL из username бота и code.
    """

    bot_name = str((bot or TELEGRAM_BOT_USERNAME or "").strip().lstrip("@"))
    code_value = str((code or "").strip())
    tg_url = f"tg://resolve?domain={quote_plus(bot_name)}&start={quote_plus(code_value)}"
    web_url = f"https://t.me/{quote_plus(bot_name)}?start={quote_plus(code_value)}"
    trace_log(
        "OPEN",
        "OPEN.URLS_BUILT",
        bot_username=bot_name,
        code=_masked_code(code_value),
        tg_url=_mask_url(tg_url),
        web_url=_mask_url(web_url),
    )
    return tg_url, web_url


def cancel_open_flow(flow_tag: str) -> None:
    """EN: Cancel scheduled open/retry/fallback events for given flow tag.
    RU: Отменить запланированные события открытия/retry/fallback для указанного flow tag.
    """

    state = _OPEN_FLOW_EVENTS.pop(str(flow_tag), {})
    for event in state.get("events", []):
        try:
            event.cancel()
        except Exception:
            continue


def _build_chat_url(bot: str | None) -> str:
    """EN: Build tg:// URL without payload for Telegram warm-up stage.
    RU: Собрать tg:// URL без payload для warm-up этапа Telegram.
    """

    bot_name = str((bot or TELEGRAM_BOT_USERNAME or "").strip().lstrip("@"))
    return f"tg://resolve?domain={quote_plus(bot_name)}"


def open_bot_two_stage(
    bot_username: str,
    code: str,
    flow_tag: str,
    warmup: bool = False,
    retry_always: bool = False,
) -> float:
    """EN: Open Telegram bot chat with optional warm-up, retry, and focus-aware web fallback.
    RU: Открыть чат Telegram-бота с опциональным warm-up, retry и web fallback с учётом фокуса.

    EN: `retry_always=True` is intended for payout cold-start only, where Stage1 retry
    must run even after a successful initial Stage1 attempt to force Telegram into the
    target bot chat after process startup.
    RU: `retry_always=True` предназначен только для payout cold-start, где Stage1 retry
    должен выполняться даже после успешной первой попытки Stage1, чтобы принудительно
    довести Telegram до чата нужного бота после запуска процесса.
    """

    cancel_open_flow(flow_tag)
    start_ts = float(time())
    stage0_url = _build_chat_url(bot_username)
    start_url, web_url = build_urls(bot_username, code)
    masked_code = _masked_code(code)
    state: dict[str, object] = {
        "events": [],
        "open_failed": False,
        "start_ts": start_ts,
        "web_fallback_attempted": False,
    }

    def _append_event(event) -> None:
        state.setdefault("events", []).append(event)

    def _schedule_retry_and_fallback() -> None:
        retry_ev = Clock.schedule_once(_run_retry, float(DELAY_RETRY_MS) / 1000.0)
        _append_event(retry_ev)
        tglog(f"[{flow_tag}] fallback scheduled reason=tg_open_failed timeout={float(TG_OPEN_TIMEOUT_SEC)}")
        fallback_ev = Clock.schedule_once(_run_web_fallback, float(TG_OPEN_TIMEOUT_SEC))
        _append_event(fallback_ev)

    def _run_stage0(_dt: float) -> None:
        tglog(f"[{flow_tag}] open Stage0 url={_mask_url(stage0_url)}")
        attempted, err = open_tg_scheme(stage0_url)
        tglog(f"[{flow_tag}] open Stage0 attempted={bool(attempted)} err={err or '-'}")
        trace_log("OPEN", "OPEN.RESULT", flow=flow_tag, stage="stage0", attempted=bool(attempted), error=err or "")
        stage1_ev = Clock.schedule_once(_run_stage1, 0.8)
        _append_event(stage1_ev)

    def _run_initial(_dt: float) -> None:
        tglog(f"[{flow_tag}] step10 open attempt url={_mask_url(start_url)} code={masked_code} ts={start_ts}")
        attempted, err = open_tg_scheme(start_url)
        state["open_failed"] = not bool(attempted)
        tglog(f"[{flow_tag}] open result attempted={bool(attempted)} err={err or '-'}")
        trace_log("OPEN", "OPEN.RESULT", flow=flow_tag, stage="initial", attempted=bool(attempted), error=err or "")
        if not bool(attempted):
            _schedule_retry_and_fallback()

    def _run_stage1(_dt: float) -> None:
        tglog(f"[{flow_tag}] open Stage1 url={_mask_url(start_url)} code={masked_code}")
        attempted, err = open_tg_scheme(start_url)
        state["open_failed"] = not bool(attempted)
        tglog(f"[{flow_tag}] open Stage1 attempted={bool(attempted)} err={err or '-'}")
        trace_log("OPEN", "OPEN.RESULT", flow=flow_tag, stage="stage1", attempted=bool(attempted), error=err or "")
        if bool(retry_always):
            retry_ev = Clock.schedule_once(_run_retry, float(DELAY_RETRY_MS) / 1000.0)
            _append_event(retry_ev)
        if not bool(attempted):
            _schedule_retry_and_fallback()

    def _run_retry(_dt: float) -> None:
        if not bool(state.get("open_failed")):
            return
        tglog(f"[{flow_tag}] open Stage1Retry url={_mask_url(start_url)} code={masked_code}")
        attempted, err = open_tg_scheme(start_url)
        tglog(f"[{flow_tag}] open Stage1Retry attempted={bool(attempted)} err={err or '-'}")
        trace_log("OPEN", "OPEN.RESULT", flow=flow_tag, stage="retry", attempted=bool(attempted), error=err or "")

    def _run_web_fallback(_dt: float) -> None:
        if not bool(state.get("open_failed")):
            return
        current_focus = getattr(Window, "focus", None)
        if current_focus is None:
            current_focus = app_focus_tracker.last_focus_value
        if current_focus is None:
            current_focus = True
        if not bool(current_focus):
            tglog(f"[{flow_tag}] fallback SKIP reason=app_not_focused")
            trace_log("OPEN", "OPEN.FALLBACK_SKIP", flow=flow_tag, reason="app_not_focused")
            return
        tglog(f"[{flow_tag}] fallback DO url={_mask_url(web_url)}")
        attempted, err = open_web(web_url)
        state["web_fallback_attempted"] = bool(attempted)
        tglog(f"[{flow_tag}] fallback result attempted={bool(attempted)} err={err or '-'}")
        trace_log("OPEN", "OPEN.RESULT", flow=flow_tag, stage="web_fallback", attempted=bool(attempted), error=err or "")

    first_ev = Clock.schedule_once(_run_stage0 if warmup else _run_initial, 0)
    _append_event(first_ev)
    _OPEN_FLOW_EVENTS[str(flow_tag)] = state
    return start_ts


def open_bot_with_start(bot_username: str, code: str, purpose: str = "TGDBG") -> bool:
    """EN: Open Telegram bot chat for arbitrary bot username with one-shot fallback.
    RU: Открыть чат Telegram-бота для произвольного username с одношаговым fallback.

    EN: This helper preserves backward compatibility for existing verify/reset flows
    while allowing payout flow to pass a different bot username and purpose tag.
    RU: Этот helper сохраняет обратную совместимость для существующих verify/reset flow
    и позволяет payout flow передавать другой username бота и purpose tag.
    """

    tg_url, web_url = build_urls(bot_username, code)
    tglog(f"[{purpose}] open stage=tg url={_mask_url(tg_url)}")
    attempted, _err = open_tg_scheme(tg_url)
    if attempted:
        return True
    tglog(f"[{purpose}] open stage=web url={_mask_url(web_url)}")
    web_attempted, _web_err = open_web(web_url)
    return bool(web_attempted)


def open_tg_scheme(tg_url: str) -> tuple[bool, str | None]:
    """EN: Try to open tg:// URL and return (attempted, error).
    RU: Попытаться открыть tg:// URL и вернуть (attempted, error).
    """

    tglog(f"[TGDBG] open stage=tg url={_mask_url(tg_url)}")
    trace_log(
        "OPEN",
        "OPEN.ATTEMPT",
        stage="tg",
        platform=kivy_platform,
        url=_mask_url(tg_url),
    )

    if kivy_platform == "android":
        try:
            from jnius import autoclass  # type: ignore

            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Intent = autoclass("android.content.Intent")
            Uri = autoclass("android.net.Uri")
            ctx = PythonActivity.mActivity
            intent = Intent(Intent.ACTION_VIEW, Uri.parse(tg_url))
            intent.addFlags(int(Intent.FLAG_ACTIVITY_NEW_TASK))
            ctx.startActivity(intent)
            trace_log("OPEN", "OPEN.RESULT", stage="tg", platform=kivy_platform, attempted=True, result=True)
            return True, None
        except Exception as exc:
            _LOG.exception("[TGDBG] android tg open failed")
            trace_exception("OPEN", "OPEN.EXCEPTION", exc, stage="tg", platform=kivy_platform, url=_mask_url(tg_url))
            return False, str(exc)

    try:
        if sys.platform.startswith("win"):
            os.startfile(tg_url)  # type: ignore[attr-defined]
            trace_log("OPEN", "OPEN.RESULT", stage="tg", platform=sys.platform, attempted=True, result=True)
            return True, None
        if sys.platform == "darwin":
            subprocess.run(["open", tg_url], capture_output=True, text=True, check=False)
            trace_log("OPEN", "OPEN.RESULT", stage="tg", platform=sys.platform, attempted=True, result=True)
            return True, None
        subprocess.run(["xdg-open", tg_url], capture_output=True, text=True, check=False)
        trace_log("OPEN", "OPEN.RESULT", stage="tg", platform=sys.platform, attempted=True, result=True)
        return True, None
    except Exception as exc:
        _LOG.exception("[TGDBG] desktop tg open failed")
        trace_exception("OPEN", "OPEN.EXCEPTION", exc, stage="tg", platform=sys.platform, url=_mask_url(tg_url))
        return False, str(exc)


def open_web(web_url: str) -> tuple[bool, str | None]:
    """EN: Try to open web URL and return (attempted, error).
    RU: Попытаться открыть web URL и вернуть (attempted, error).
    """

    tglog(f"[TGDBG] open stage=web url={_mask_url(web_url)}")
    trace_log(
        "OPEN",
        "OPEN.ATTEMPT",
        stage="web",
        platform=kivy_platform,
        url=_mask_url(web_url),
    )

    if kivy_platform == "android":
        try:
            from jnius import autoclass  # type: ignore

            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Intent = autoclass("android.content.Intent")
            Uri = autoclass("android.net.Uri")
            ctx = PythonActivity.mActivity
            intent = Intent(Intent.ACTION_VIEW, Uri.parse(web_url))
            intent.addFlags(int(Intent.FLAG_ACTIVITY_NEW_TASK))
            ctx.startActivity(intent)
            trace_log("OPEN", "OPEN.RESULT", stage="web", platform=kivy_platform, attempted=True, result=True)
            return True, None
        except Exception as exc:
            _LOG.exception("[TGDBG] android web open failed")
            trace_exception("OPEN", "OPEN.EXCEPTION", exc, stage="web", platform=kivy_platform, url=_mask_url(web_url))
            return False, str(exc)

    try:
        webbrowser.open(web_url)
        trace_log("OPEN", "OPEN.RESULT", stage="web", platform=sys.platform, attempted=True, result=True)
        return True, None
    except Exception as exc:
        _LOG.exception("[TGDBG] desktop web open failed")
        trace_exception("OPEN", "OPEN.EXCEPTION", exc, stage="web", platform=sys.platform, url=_mask_url(web_url))
        return False, str(exc)


def _extract_miniapp_launch_params(miniapp_url: str) -> tuple[str, str, str] | None:
    """EN: Parse Mini App HTTPS URL into `(bot_username, short_name, start_param)` tuple.
    RU: Разобрать HTTPS URL Mini App в кортеж `(bot_username, short_name, start_param)`.

    EN: Only the canonical Telegram Mini App URL shape is accepted:
    `https://t.me/<bot_username>/<short_name>?startapp=<token>`.
    RU: Принимается только каноническая форма Telegram Mini App URL:
    `https://t.me/<bot_username>/<short_name>?startapp=<token>`.
    """

    try:
        parts = urlsplit(str((miniapp_url or "").strip()))
    except Exception:
        return None
    if parts.scheme != "https" or parts.netloc not in {"t.me", "www.t.me"}:
        return None
    path_parts = [part for part in str(parts.path or "").split("/") if part]
    if len(path_parts) < 2:
        return None
    query = parse_qs(parts.query, keep_blank_values=True)
    start_param = str((query.get("startapp") or [""])[0]).strip()
    bot_username = str(path_parts[0]).strip().lstrip("@")
    short_name = str(path_parts[1]).strip()
    if not bot_username or not short_name or not start_param:
        return None
    return bot_username, short_name, start_param


def _build_direct_miniapp_tg_url(bot_username: str, short_name: str, start_param: str, *, scheme: str = "tg") -> str:
    """EN: Build direct Mini App target for Telegram URI handlers using bot username, app short name and startapp.
    RU: Собрать direct Mini App target для Telegram URI-handler-ов по username бота, short name приложения и startapp.
    """

    return (
        f"{str(scheme)}://resolve?domain={quote_plus(str(bot_username).lstrip('@'))}"
        f"&appname={quote_plus(str(short_name))}"
        f"&startapp={quote_plus(str(start_param))}"
    )


def _build_main_miniapp_tg_url(bot_username: str, start_param: str, *, scheme: str = "tg") -> str:
    """EN: Build main Mini App target for Telegram URI handlers using bot username and startapp only.
    RU: Собрать target main Mini App для Telegram URI-handler-ов по username бота и startapp без short name.
    """

    return (
        f"{str(scheme)}://resolve?domain={quote_plus(str(bot_username).lstrip('@'))}"
        f"&startapp={quote_plus(str(start_param))}"
    )


def _is_valid_miniapp_target(target: str) -> bool:
    """EN: Validate that a launcher target is a strict Telegram URI for a bot dialog or Mini App target.
    RU: Проверить, что launcher-target является strict Telegram URI для bot dialog или Mini App target.
    """

    try:
        parts = urlsplit(str((target or "").strip()))
    except Exception:
        return False
    if parts.scheme not in {"tg", "telegram"} or parts.netloc != "resolve":
        return False
    query = parse_qs(parts.query, keep_blank_values=True)
    domain = str((query.get("domain") or [""])[0]).strip().lstrip("@")
    start_param = str((query.get("startapp") or [""])[0]).strip()
    appname = str((query.get("appname") or [""])[0]).strip()
    if not domain or not start_param:
        return False
    if "appname" in query and not appname:
        return False
    return True


def _build_miniapp_launch_strategies(bot_username: str, short_name: str, start_param: str) -> list[MiniAppLaunchStrategy]:
    """EN: Build ordered strict launch strategies for desktop/mobile Telegram Mini App opening.
    RU: Собрать упорядоченные strict-стратегии запуска Telegram Mini App для desktop/mobile.

    EN: Direct Mini App targets are tried first; main Mini App targets are attempted after them
    as a compatibility fallback for Telegram clients that may ignore `appname`.
    RU: Сначала пробуются direct Mini App targets; затем идут main Mini App targets как
    совместимый fallback для клиентов Telegram, которые могут игнорировать `appname`.
    """

    bot_value = str(bot_username).lstrip("@")
    short_value = str(short_name)
    start_value = str(start_param)
    return [
        MiniAppLaunchStrategy(
            name="tg-scheme-direct",
            target=_build_direct_miniapp_tg_url(bot_value, short_value, start_value, scheme="tg"),
        ),
        MiniAppLaunchStrategy(
            name="telegram-uri-direct",
            target=_build_direct_miniapp_tg_url(bot_value, short_value, start_value, scheme="telegram"),
        ),
        MiniAppLaunchStrategy(
            name="tg-scheme-main",
            target=_build_main_miniapp_tg_url(bot_value, start_value, scheme="tg"),
        ),
        MiniAppLaunchStrategy(
            name="telegram-uri-main",
            target=_build_main_miniapp_tg_url(bot_value, start_value, scheme="telegram"),
        ),
    ]


def _open_android_telegram_uri(tg_url: str) -> tuple[bool, str | None]:
    """EN: Launch Telegram Mini App on Android only through Telegram app package.
    RU: Запустить Telegram Mini App на Android только через пакет приложения Telegram.
    """

    try:
        from jnius import autoclass  # type: ignore

        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Intent = autoclass("android.content.Intent")
        Uri = autoclass("android.net.Uri")
        ctx = PythonActivity.mActivity
        package_manager = ctx.getPackageManager()
        intent = Intent(Intent.ACTION_VIEW, Uri.parse(tg_url))
        intent.setPackage(_TG_ANDROID_PACKAGE)
        intent.addFlags(int(Intent.FLAG_ACTIVITY_NEW_TASK))
        if intent.resolveActivity(package_manager) is None:
            return False, "TG_APP_NOT_AVAILABLE"
        ctx.startActivity(intent)
        return True, None
    except Exception as exc:
        _LOG.exception("[MINIAPP] android tg app open failed")
        trace_exception("OPEN", "OPEN.EXCEPTION", exc, stage="miniapp", platform=kivy_platform, url=_mask_url(tg_url))
        return False, "MINIAPP_OPEN_FAILED"


def _open_desktop_telegram_uri(tg_url: str) -> tuple[bool, str | None]:
    """EN: Launch Telegram Mini App on desktop only through Telegram URI scheme handlers.
    RU: Запустить Telegram Mini App на desktop только через обработчики URI-схем Telegram.
    """

    try:
        if sys.platform.startswith("win"):
            os.startfile(tg_url)  # type: ignore[attr-defined]
            return False, "MINIAPP_OPEN_UNCERTAIN"
        if sys.platform == "darwin":
            result = subprocess.run(["open", tg_url], capture_output=True, text=True, check=False)
            return (False, "MINIAPP_OPEN_UNCERTAIN") if int(result.returncode) == 0 else (False, "TG_SCHEME_UNSUPPORTED")
        result = subprocess.run(["xdg-open", tg_url], capture_output=True, text=True, check=False)
        return (False, "MINIAPP_OPEN_UNCERTAIN") if int(result.returncode) == 0 else (False, "TG_SCHEME_UNSUPPORTED")
    except Exception as exc:
        _LOG.exception("[MINIAPP] desktop tg app open failed")
        trace_exception("OPEN", "OPEN.EXCEPTION", exc, stage="miniapp", platform=sys.platform, url=_mask_url(tg_url))
        return False, "MINIAPP_OPEN_FAILED"


def _open_miniapp_tg_target(tg_url: str) -> tuple[bool, str | None]:
    """EN: Open strict Telegram Mini App target using platform-specific Telegram app path only.
    RU: Открыть strict target Telegram Mini App только через platform-specific путь приложения Telegram.
    """

    if kivy_platform == "android":
        return _open_android_telegram_uri(tg_url)
    return _open_desktop_telegram_uri(tg_url)


def open_telegram_miniapp(miniapp_url: str) -> tuple[bool, str | None]:
    """EN: Open Telegram Mini App URL through a dedicated helper with explicit Mini App semantics.
    RU: Открыть URL Telegram Mini App через отдельный helper с явной Mini App-семантикой.

    EN: This helper keeps Mini App launch separate from generic web-opening logic so trusted
    Telegram identity flows can log and handle launch failures explicitly.
    RU: Этот helper отделяет запуск Mini App от generic web-opening, чтобы доверенные
    Telegram identity-flow могли явно логировать и обрабатывать ошибки запуска.
    """

    raw_url = str((miniapp_url or "").strip())
    masked_url = _mask_url(raw_url)
    parsed = _extract_miniapp_launch_params(raw_url)
    if parsed is None:
        tglog(f"[MINIAPP] open stage=miniapp target=- browser_fallback=False attempted=False result=False error=MINIAPP_OPEN_FAILED url={masked_url}")
        trace_log(
            "OPEN",
            "OPEN.RESULT",
            stage="miniapp",
            platform=kivy_platform,
            browser_fallback=False,
            attempted=False,
            result=False,
            error="MINIAPP_OPEN_FAILED",
            url=masked_url,
        )
        return False, "MINIAPP_OPEN_FAILED"

    bot_username, short_name, start_param = parsed
    tglog(
        f"[MINIAPP] parse stage=miniapp raw_url={masked_url} "
        f"bot_username={bot_username} short_name={short_name} start_param={_masked_code(start_param)}"
    )
    trace_log(
        "OPEN",
        "OPEN.PARSED",
        stage="miniapp",
        platform=kivy_platform,
        url=masked_url,
        bot_username=bot_username,
        short_name=short_name,
        start_param=_masked_code(start_param),
        browser_fallback=False,
    )
    strategies = _build_miniapp_launch_strategies(bot_username, short_name, start_param)
    last_error = "MINIAPP_OPEN_FAILED"
    attempted_any = False
    trace_log(
        "OPEN",
        "OPEN.ATTEMPT",
        stage="miniapp",
        platform=kivy_platform,
        url=masked_url,
        browser_fallback=False,
    )
    for strategy in strategies:
        masked_target = _mask_url(strategy.target)
        target_ok = _is_valid_miniapp_target(strategy.target)
        tglog(
            f"[MINIAPP] strategy stage=miniapp name={strategy.name} target={masked_target} "
            f"browser_fallback=False target_valid={target_ok}"
        )
        trace_log(
            "OPEN",
            "OPEN.STRATEGY",
            stage="miniapp",
            platform=kivy_platform,
            strategy=strategy.name,
            target=masked_target,
            target_valid=bool(target_ok),
            browser_fallback=False,
        )
        if not target_ok:
            last_error = "TG_TARGET_INVALID"
            continue
        attempted, error = _open_miniapp_tg_target(strategy.target)
        attempted_any = attempted_any or bool(attempted)
        error_code = str(error or "")
        tglog(
            f"[MINIAPP] strategy result stage=miniapp name={strategy.name} target={masked_target} "
            f"browser_fallback=False attempted={bool(attempted)} result={bool(attempted and not error_code)} "
            f"error={error_code or '-'}"
        )
        trace_log(
            "OPEN",
            "OPEN.STRATEGY_RESULT",
            stage="miniapp",
            platform=kivy_platform,
            strategy=strategy.name,
            target=masked_target,
            attempted=bool(attempted),
            result=bool(attempted and not error_code),
            error=error_code or "",
            browser_fallback=False,
        )
        if attempted and not error_code:
            trace_log(
                "OPEN",
                "OPEN.RESULT",
                stage="miniapp",
                platform=kivy_platform,
                strategy=strategy.name,
                target=masked_target,
                browser_fallback=False,
                attempted=True,
                result=True,
            )
            return True, None
        if error_code:
            last_error = error_code

    trace_log(
        "OPEN",
        "OPEN.RESULT",
        stage="miniapp",
        platform=kivy_platform,
        browser_fallback=False,
        attempted=bool(attempted_any),
        result=False,
        error=last_error,
    )
    tglog(
        f"[MINIAPP] open stage=miniapp browser_fallback=False attempted={bool(attempted_any)} "
        f"result=False error={last_error}"
    )
    return False, last_error


def open_tg(bot_username: str, token: str = "") -> bool:
    """EN: Backward-compatible boolean tg:// open helper.
    RU: Обратносовместимый bool-хелпер открытия tg://.
    """

    tg_url, _ = build_urls(bot_username, token)
    attempted, _ = open_tg_scheme(tg_url)
    return attempted


def open_telegram_stage_tg(bot_username: str, token: str = "") -> bool:
    """EN: Backward-compatible alias for tg stage.
    RU: Обратносовместимый алиас для этапа tg.
    """

    return open_tg(bot_username=bot_username, token=token)


def open_telegram_stage_web(bot_username: str, token: str = "") -> bool:
    """EN: Backward-compatible alias for web stage.
    RU: Обратносовместимый алиас для этапа web.
    """

    _, web_url = build_urls(bot_username, token)
    attempted, _ = open_web(web_url)
    return attempted


def open_telegram_bot_chat(bot_username: str, code: str = "") -> bool:
    """EN: Backward-compatible one-shot open helper.
    RU: Обратносовместимый one-shot хелпер открытия.
    """

    return open_bot_with_start(bot_username=bot_username, code=code, purpose="TGDBG")


def open_telegram_chat(bot_username: str, token: str = "") -> bool:
    """EN: Backward-compatible alias.
    RU: Обратносовместимый алиас.
    """

    return open_telegram_bot_chat(bot_username=bot_username, code=token)
