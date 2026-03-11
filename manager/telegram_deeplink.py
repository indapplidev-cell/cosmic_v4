from __future__ import annotations

"""EN: Telegram deep-link helpers for opening bot chat with code.
RU: Хелперы Telegram deep-link для открытия чата бота с code.
"""

import logging
import os
import subprocess
import sys
import webbrowser
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


def open_bot_two_stage(bot_username: str, code: str, flow_tag: str) -> float:
    """EN: Open Telegram with `start=code`, retry once only on failed attempt, then optional web fallback.
    RU: Открыть Telegram с `start=code`, сделать один retry только при неудачной попытке и затем опциональный web fallback.
    """

    cancel_open_flow(flow_tag)
    start_ts = float(time())
    start_url, web_url = build_urls(bot_username, code)
    masked_code = _masked_code(code)
    state: dict[str, object] = {
        "events": [],
        "initial_failed": False,
        "start_ts": start_ts,
        "web_fallback_attempted": False,
    }

    def _append_event(event) -> None:
        state.setdefault("events", []).append(event)

    def _run_initial(_dt: float) -> None:
        tglog(f"[{flow_tag}] step10 open attempt url={_mask_url(start_url)} code={masked_code} ts={start_ts}")
        attempted, err = open_tg_scheme(start_url)
        state["initial_failed"] = not bool(attempted)
        tglog(f"[{flow_tag}] open result attempted={bool(attempted)} err={err or '-'}")
        trace_log("OPEN", "OPEN.RESULT", flow=flow_tag, stage="initial", attempted=bool(attempted), error=err or "")
        if bool(attempted):
            return
        retry_ev = Clock.schedule_once(_run_retry, float(DELAY_RETRY_MS) / 1000.0)
        _append_event(retry_ev)
        tglog(f"[{flow_tag}] fallback scheduled reason=tg_open_failed timeout={float(TG_OPEN_TIMEOUT_SEC)}")
        fallback_ev = Clock.schedule_once(_run_web_fallback, float(TG_OPEN_TIMEOUT_SEC))
        _append_event(fallback_ev)

    def _run_retry(_dt: float) -> None:
        if not bool(state.get("initial_failed")):
            return
        tglog(f"[{flow_tag}] retry attempt url={_mask_url(start_url)} code={masked_code}")
        attempted, err = open_tg_scheme(start_url)
        tglog(f"[{flow_tag}] retry result attempted={bool(attempted)} err={err or '-'}")
        trace_log("OPEN", "OPEN.RESULT", flow=flow_tag, stage="retry", attempted=bool(attempted), error=err or "")

    def _run_web_fallback(_dt: float) -> None:
        if not bool(state.get("initial_failed")):
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

    initial_ev = Clock.schedule_once(_run_initial, 0)
    _append_event(initial_ev)
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
