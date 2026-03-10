from __future__ import annotations

"""EN: Telegram deep-link helpers for opening bot chat with code.
RU: Хелперы Telegram deep-link для открытия чата бота с code.
"""

import logging
import os
import subprocess
import sys
import webbrowser
from urllib.parse import parse_qs, quote_plus, urlsplit, urlunsplit, urlencode

from kivy.utils import platform as kivy_platform

from manager.config import TG_DEBUG_FLOW, TELEGRAM_BOT_USERNAME
from manager.trace import TraceManager, trace_exception, trace_log
from manager.tg_debug_log import tglog

_LOG = logging.getLogger("cosmic.telegram_deeplink")


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

    tg_url, web_url = build_urls(bot_username, code)
    attempted, _ = open_tg_scheme(tg_url)
    if attempted:
        return True
    web_attempted, _ = open_web(web_url)
    return web_attempted


def open_telegram_chat(bot_username: str, token: str = "") -> bool:
    """EN: Backward-compatible alias.
    RU: Обратносовместимый алиас.
    """

    return open_telegram_bot_chat(bot_username=bot_username, code=token)
