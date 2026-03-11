"""EN: Telegram bot entrypoint with 2-button menu and server-side confirmation flow.
RU: Точка входа Telegram-бота с 2-кнопочным меню и серверным потоком подтверждения.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import urllib.error
import urllib.request

from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from server.services.telegram_service import fetch_outbox_batch, mark_outbox_failed, mark_outbox_sent


logger = logging.getLogger("cosmic.bot")


def _env_int(name: str, default: int) -> int:
    """EN: Read integer env value safely with fallback.
    RU: Безопасно прочитать целочисленное env-значение с запасным значением.
    """

    raw = os.getenv(name, str(default)).strip()
    try:
        return int(raw)
    except Exception:
        return int(default)


def _menu_keyboard() -> ReplyKeyboardMarkup:
    """EN: Build static 2-button reply keyboard.
    RU: Построить статичную reply-клавиатуру из 2 кнопок.
    """

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("ПОДТВЕРДИТЬ")],
            [KeyboardButton("СБРОСИТЬ")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def _api_base_url() -> str:
    """EN: Resolve internal API base URL for bot-to-api calls.
    RU: Получить внутренний base URL API для вызовов bot->api.
    """

    return os.getenv("API_INTERNAL_URL", "http://api:8000").rstrip("/")


def _mask_confirm_code(value: str) -> str:
    """EN: Mask confirm-code in logs without exposing full value.
    RU: Маскировать confirm-code в логах без раскрытия полного значения.
    """

    code = str((value or "").strip())
    if len(code) <= 4:
        return "*" * len(code)
    return f"{code[:2]}...{code[-2:]}"


def _confirm_latest_http(telegram_user_id: int, tg_username: str | None) -> tuple[int, dict]:
    """EN: Call API endpoint that confirms latest pending link and returns confirm_code.
    RU: Вызвать API-эндпоинт, который подтверждает последний pending link и возвращает confirm_code.
    """

    url = f"{_api_base_url()}/telegram/link/confirm_latest"
    payload = {
        "telegram_user_id": int(telegram_user_id),
        "tg_username": str((tg_username or "").strip()),
    }
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url=url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
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
        logger.exception(
            "event=TG_API_CALL_CONFIRM_LATEST_EXCEPTION tg_uid=%s tg_username=%s error=%s",
            int(telegram_user_id),
            str((tg_username or "-").strip() or "-"),
            exc.__class__.__name__,
        )
        return 0, {"ok": False, "error": "API_ERROR"}


async def _cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """EN: Show compact menu and do not depend on `/start <payload>` for confirmation.
    RU: Показать компактное меню и не зависеть от `/start <payload>` для подтверждения.
    """

    del context
    if update.message is None or update.effective_user is None:
        return
    tg_user_id = int(update.effective_user.id)
    tg_username = str((update.effective_user.username or "").strip() or "-")
    logger.info("event=TG_START tg_uid=%s tg_username=%s", tg_user_id, tg_username)
    await update.message.reply_text("Выберите действие.", reply_markup=_menu_keyboard())


async def _on_menu_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """EN: Handle 2-button menu texts: confirm flow and reset placeholder.
    RU: Обработать тексты 2-кнопочного меню: flow подтверждения и заглушку сброса.
    """

    del context
    if update.message is None or update.effective_user is None:
        return

    text = str(update.message.text or "").strip()
    text_norm = text.casefold()
    tg_user_id = int(update.effective_user.id)
    tg_username = str((update.effective_user.username or "").strip())

    logger.info("event=BOT_RECV_TEXT text=%s tg_uid=%s tg_username=%s", text, tg_user_id, tg_username or "-")

    if text_norm == "подтвердить":
        try:
            logger.info(
                "event=TG_BTN_CONFIRM_IN tg_uid=%s tg_username=%s pending_present=- pending_link_code=-",
                tg_user_id,
                tg_username or "-",
            )
            logger.info(
                "event=TG_API_CALL_CONFIRM_LATEST tg_uid=%s tg_username=%s",
                tg_user_id,
                tg_username or "-",
            )
            http_status, result = await asyncio.to_thread(_confirm_latest_http, tg_user_id, tg_username)
            confirm_code_for_log = str(result.get("confirm_code") or "")
            logger.info(
                "event=TG_API_RESP_CONFIRM_LATEST http_status=%s ok=%s error=%s user_id=%s confirm_code_present=%s confirm_code_masked=%s",
                int(http_status or 0),
                str(bool(result.get("ok"))).lower(),
                str(result.get("error") or "-"),
                int(result.get("user_id") or 0),
                str(bool(confirm_code_for_log)).lower(),
                _mask_confirm_code(confirm_code_for_log) if confirm_code_for_log else "-",
            )

            if bool(result.get("ok")):
                confirm_code = str(result.get("confirm_code") or "")
                returned_username = str(result.get("tg_username") or tg_username or "").strip() or "no_data"
                returned_tg_id = int(result.get("telegram_user_id") or tg_user_id)
                await update.message.reply_text(
                    "\n".join(
                        [
                            f"Код подтверждения: {confirm_code}",
                            f"Ваш Telegram ID: {returned_tg_id}",
                            f"Ваш username: {returned_username}",
                        ]
                    ),
                    reply_markup=_menu_keyboard(),
                )
                return

            error = str(result.get("error") or "API_ERROR")
            if error == "NO_PENDING":
                text_out = "Нет активного запроса. Откройте бота из приложения заново."
            elif error in {"MISMATCH", "CODE_NOT_FOUND", "EXPIRED", "USED"}:
                text_out = "Запрос не совпал. Откройте бота из приложения заново."
            elif error == "ALREADY_LINKED":
                text_out = "Аккаунт уже подтверждён."
            elif error == "ALREADY_USED":
                text_out = "Запрос уже использован. Откройте бота из приложения заново."
            else:
                text_out = "Ошибка. Попробуйте позже."
            await update.message.reply_text(text_out, reply_markup=_menu_keyboard())
            return
        except Exception:
            logger.exception("event=TG_BTN_CONFIRM_EXCEPTION tg_uid=%s tg_username=%s", tg_user_id, tg_username or "-")
            await update.message.reply_text("Ошибка. Попробуйте позже.", reply_markup=_menu_keyboard())
            return

    if text_norm == "сбросить":
        await update.message.reply_text("Функция сброса будет добавлена позже.", reply_markup=_menu_keyboard())
        return

    await update.message.reply_text("Выберите действие.", reply_markup=_menu_keyboard())


async def _outbox_tick(app: Application) -> None:
    """EN: Deliver one outbox batch and mark send status with retry metadata.
    RU: Отправить одну пачку outbox и отметить статус доставки с метаданными retry.
    """

    batch_limit = max(1, _env_int("TELEGRAM_OUTBOX_BATCH", 20))
    items = fetch_outbox_batch(limit=batch_limit)
    if not items:
        return

    for item in items:
        item_id = int(item.get("id") or 0)
        tg_user_id = int(item.get("telegram_user_id") or 0)
        message = str(item.get("message") or "")
        if item_id <= 0 or tg_user_id <= 0 or not message:
            continue
        try:
            await app.bot.send_message(chat_id=tg_user_id, text=message)
            mark_outbox_sent(item_id)
        except Exception as exc:
            mark_outbox_failed(item_id, exc.__class__.__name__)


async def _outbox_loop(app: Application) -> None:
    """EN: Run continuous outbox polling loop with fixed interval.
    RU: Запустить непрерывный цикл опроса outbox с фиксированным интервалом.
    """

    interval_sec = max(2, _env_int("TELEGRAM_OUTBOX_INTERVAL_SEC", 3))
    while True:
        try:
            await _outbox_tick(app)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("outbox_tick_failed type=%s", exc.__class__.__name__)
        await asyncio.sleep(interval_sec)


async def _on_post_init(app: Application) -> None:
    """EN: Start background outbox worker task after bot initialization.
    RU: Запустить фоновую задачу outbox-воркера после инициализации бота.
    """

    app.bot_data["outbox_task"] = asyncio.create_task(_outbox_loop(app))


async def _on_post_shutdown(app: Application) -> None:
    """EN: Stop background outbox worker task on bot shutdown.
    RU: Остановить фоновую задачу outbox-воркера при завершении бота.
    """

    task = app.bot_data.get("outbox_task")
    if task is None:
        return
    task.cancel()
    try:
        await task
    except Exception:
        return


def main() -> None:
    """EN: Run long-polling bot with compact 2-button menu.
    RU: Запустить бота в long-polling режиме с компактным меню из 2 кнопок.
    """

    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN is missing")
        raise SystemExit(2)

    app = (
        Application.builder()
        .token(token)
        .post_init(_on_post_init)
        .post_shutdown(_on_post_shutdown)
        .build()
    )
    app.add_handler(CommandHandler("start", _cmd_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _on_menu_text))

    logger.info("bot started bot_username=pswprotect_bot")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
