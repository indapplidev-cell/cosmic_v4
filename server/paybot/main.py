"""EN: Telegram payout bot entrypoint with two-button payout menu.
RU: Точка входа payout Telegram-бота с меню из двух кнопок.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request

from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters


logger = logging.getLogger("cosmic.paybot")


def _menu_keyboard() -> ReplyKeyboardMarkup:
    """EN: Build static payout keyboard with only two actions.
    RU: Построить статичную payout-клавиатуру только с двумя действиями.
    """

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("ПОЛУЧИТЬ")],
            [KeyboardButton("ВЕРНУТЬСЯ")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def _api_base_url() -> str:
    """EN: Resolve paybot internal API base URL.
    RU: Получить внутренний base URL API для paybot.
    """

    return str((os.getenv("PAY_BOT_API_BASE_URL", "http://api:8000") or "").rstrip("/"))


def _shared_secret() -> str:
    """EN: Return bot-only shared secret for payout ack endpoint.
    RU: Вернуть bot-only shared secret для payout ack endpoint.
    """

    return str((os.getenv("PAY_BOT_SHARED_SECRET", "") or "").strip())


def _return_link() -> str:
    """EN: Return app deep-link used by payout bot "return" action.
    RU: Вернуть deep-link приложения, используемый кнопкой «вернуться» в payout bot.
    """

    return str((os.getenv("APP_RETURN_DEEPLINK", "cosmic://return?screen=settings") or "").strip())


def _mask_code(value: str) -> str:
    """EN: Mask payout code for logs.
    RU: Замаскировать payout-код для логов.
    """

    code = str((value or "").strip())
    if not code:
        return "-"
    if len(code) <= 8:
        return f"{code[:1]}...{code[-1:]}(len={len(code)})"
    return f"{code[:4]}...{code[-4:]}(len={len(code)})"


def _pending_codes(context: ContextTypes.DEFAULT_TYPE) -> dict[int, str]:
    """EN: Return mutable mapping of pending payout start-codes by Telegram user id.
    RU: Вернуть изменяемое отображение pending payout start-кодов по Telegram user id.
    """

    pending = context.application.bot_data.get("pending_payout_codes")
    if not isinstance(pending, dict):
        pending = {}
        context.application.bot_data["pending_payout_codes"] = pending
    return pending


def _post_json(url: str, payload: dict, headers: dict[str, str]) -> tuple[int, dict]:
    """EN: Execute JSON POST and normalize `(status, payload)` result.
    RU: Выполнить JSON POST и нормализовать результат `(status, payload)`.
    """

    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url=url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            raw = response.read().decode("utf-8", errors="replace")
            data = json.loads(raw) if raw else {}
            if isinstance(data, dict):
                return int(getattr(response, "status", 200) or 200), data
            return int(getattr(response, "status", 200) or 200), {"ok": False, "error": "API_ERROR"}
    except urllib.error.HTTPError as exc:
        try:
            raw = exc.read().decode("utf-8", errors="replace")
            data = json.loads(raw) if raw else {}
            if isinstance(data, dict):
                return int(exc.code or 0), data
        except Exception:
            pass
        return int(exc.code or 0), {"ok": False, "error": "API_ERROR"}
    except Exception as exc:
        logger.exception("event=PAYBOT_POST_JSON_EXCEPTION error=%s url=%s", exc.__class__.__name__, url)
        return 0, {"ok": False, "error": "API_ERROR"}


def _ack_payout_code(code: str, telegram_user_id: int, telegram_username: str | None) -> tuple[int, dict]:
    """EN: Call payout ack API to prove app-issued code was received by paybot.
    RU: Вызвать payout ack API, чтобы подтвердить получение app-issued кода в paybot.
    """

    return _post_json(
        url=f"{_api_base_url()}/payout/link/ack",
        payload={
            "code": str((code or "").strip()),
            "telegram_user_id": int(telegram_user_id),
            "telegram_username": str((telegram_username or "").strip()) or None,
        },
        headers={
            "Content-Type": "application/json",
            "X-Bot-Secret": _shared_secret(),
        },
    )


async def _cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """EN: Handle `/start <code>` and acknowledge payout link code if present.
    RU: Обработать `/start <code>` и подтвердить payout link-код, если он передан.
    """

    if update.message is None or update.effective_user is None:
        return

    tg_user_id = int(update.effective_user.id)
    tg_username = str((update.effective_user.username or "").strip() or "-")
    payload = str(" ".join(getattr(context, "args", []) or [])).strip()
    start_has_code = bool(payload)
    logger.info(
        "event=PAYBOT_START tg_uid=%s tg_username=%s start_has_code=%s code=%s",
        tg_user_id,
        tg_username,
        str(start_has_code).lower(),
        _mask_code(payload),
    )

    if not payload:
        await update.message.reply_text("Выберите действие.", reply_markup=_menu_keyboard())
        return

    status, result = _ack_payout_code(payload, tg_user_id, tg_username)
    logger.info(
        "event=PAYBOT_ACK_RESULT tg_uid=%s tg_username=%s http_status=%s ok=%s error=%s code=%s",
        tg_user_id,
        tg_username,
        int(status or 0),
        str(bool(result.get("ok"))).lower(),
        str(result.get("error") or "-"),
        _mask_code(payload),
    )
    if bool(result.get("ok")):
        _pending_codes(context)[tg_user_id] = payload
        await update.message.reply_text("Готово. Выберите действие.", reply_markup=_menu_keyboard())
        return

    error = str(result.get("error") or "API_ERROR")
    if error in {"CODE_USED", "CODE_EXPIRED", "CODE_INVALID"}:
        text = "Запрос не совпал. Откройте бота из приложения заново."
    else:
        text = "Ошибка. Попробуйте позже."
    await update.message.reply_text(text, reply_markup=_menu_keyboard())


async def _on_menu_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """EN: Handle payout bot reply keyboard actions.
    RU: Обработать действия reply-клавиатуры payout-бота.
    """

    if update.message is None or update.effective_user is None:
        return

    text = str((update.message.text or "").strip())
    text_norm = text.casefold()
    tg_user_id = int(update.effective_user.id)
    tg_username = str((update.effective_user.username or "").strip() or "-")
    logger.info("event=PAYBOT_RECV_TEXT text=%s tg_uid=%s tg_username=%s", text, tg_user_id, tg_username)

    if text_norm == "получить":
        await update.message.reply_text("Функция будет добавлена позже.", reply_markup=_menu_keyboard())
        return

    if text_norm == "вернуться":
        deeplink = _return_link()
        logger.info("event=PAYBOT_RETURN tg_uid=%s tg_username=%s deeplink=%s", tg_user_id, tg_username, deeplink)
        await update.message.reply_text(
            "\n".join(
                [
                    f"Нажмите, чтобы вернуться: {deeplink}",
                    "Если ссылка не открылась, переключитесь обратно в приложение Cosmic.",
                ]
            ),
            reply_markup=_menu_keyboard(),
        )
        return

    await update.message.reply_text("Используйте кнопки.", reply_markup=_menu_keyboard())


def main() -> None:
    """EN: Start paybot long-polling loop.
    RU: Запустить long-polling цикл paybot.
    """

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    token = str((os.getenv("PAY_BOT_TOKEN", "") or "").strip())
    if not token:
        raise RuntimeError("PAY_BOT_TOKEN is missing")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", _cmd_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _on_menu_text))
    logger.info("event=PAYBOT_STARTED")
    app.run_polling(drop_pending_updates=False)


if __name__ == "__main__":
    main()
