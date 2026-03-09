"""EN: Telegram deep-link builders and opener with platform-aware fallback.
RU: Построение Telegram deep-link и открытие чата с fallback по платформам.
"""

from __future__ import annotations

import webbrowser
import os
from urllib.parse import quote_plus

from kivy.utils import platform as kivy_platform

from manager.config import TELEGRAM_DEEPLINK_SCHEME, TELEGRAM_WEB_LINK


def build_tg_url(bot_username: str, token: str) -> str:
    """EN: Build tg:// deep-link URL for opening bot chat with start token.
    RU: Сформировать tg:// deep-link для открытия чата бота с start-токеном.
    """

    bot = str((bot_username or "").strip().lstrip("@"))
    start_token = quote_plus(str((token or "").strip()))
    return TELEGRAM_DEEPLINK_SCHEME.format(bot=bot, token=start_token)


def build_web_url(bot_username: str, token: str) -> str:
    """EN: Build HTTPS fallback URL for opening bot chat with start token.
    RU: Сформировать HTTPS fallback-ссылку для открытия чата бота с start-токеном.
    """

    bot = str((bot_username or "").strip().lstrip("@"))
    start_token = quote_plus(str((token or "").strip()))
    return TELEGRAM_WEB_LINK.format(bot=bot, token=start_token)


def open_telegram_chat(bot_username: str, token: str) -> bool:
    """EN: Open Telegram app via deep-link, fallback to web link when app open fails.
    RU: Открыть Telegram через deep-link, при неуспехе перейти на web-ссылку.
    """

    tg_url = build_tg_url(bot_username=bot_username, token=token)
    web_url = build_web_url(bot_username=bot_username, token=token)

    if kivy_platform == "android":
        try:
            from jnius import autoclass  # type: ignore

            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Intent = autoclass("android.content.Intent")
            Uri = autoclass("android.net.Uri")
            intent = Intent(Intent.ACTION_VIEW, Uri.parse(tg_url))
            PythonActivity.mActivity.startActivity(intent)
            return True
        except Exception:
            try:
                return bool(webbrowser.open(web_url))
            except Exception:
                return False

    if os.name == "nt":
        try:
            os.startfile(tg_url)  # type: ignore[attr-defined]
            return True
        except Exception:
            pass

    try:
        if webbrowser.open(tg_url):
            return True
    except Exception:
        pass
    try:
        return bool(webbrowser.open(web_url))
    except Exception:
        return False
