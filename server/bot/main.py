"""EN: Telegram bot entrypoint for deep-link `/start <token>` flow and outbox worker.
RU: Точка входа Telegram-бота для deep-link потока `/start <token>` и воркера outbox.
"""

from __future__ import annotations

import asyncio
import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from server.bot.i18n import t_bot
from server.services.telegram_service import (
    confirm_link_token,
    fetch_outbox_batch,
    mark_outbox_failed,
    mark_outbox_sent,
    open_link_token,
    send_reset_code_for_link_token,
)


logger = logging.getLogger("cosmic.telegram_bot")


def _env_int(name: str, default: int) -> int:
    """EN: Read integer env value safely with fallback.
    RU: Безопасно прочитать целочисленное env-значение с резервным значением.
    """

    raw = os.getenv(name, str(default)).strip()
    try:
        return int(raw)
    except Exception:
        return int(default)


async def _cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """EN: Handle deep-link start token and show inline action buttons.
    RU: Обработать deep-link start токен и показать inline-кнопки действий.
    """

    if update.message is None or update.effective_user is None:
        return
    lang_code = getattr(update.effective_user, "language_code", "ru")
    args = list(context.args or [])
    if len(args) != 1:
        await update.message.reply_text(t_bot(lang_code, "bot.msg_link_expired"))
        return

    start_token = str(args[0]).strip()
    result = await asyncio.to_thread(
        open_link_token,
        start_token,
        int(update.effective_user.id),
    )
    if not result.get("ok"):
        await update.message.reply_text(t_bot(lang_code, "bot.msg_link_expired"))
        return

    token_id = int(result.get("token_id") or 0)
    if token_id <= 0:
        await update.message.reply_text(t_bot(lang_code, "bot.msg_link_expired"))
        return

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(text=t_bot(lang_code, "bot.btn_confirm"), callback_data=f"confirm:{token_id}")],
            [InlineKeyboardButton(text=t_bot(lang_code, "bot.btn_reset"), callback_data=f"reset:{token_id}")],
        ]
    )
    await update.message.reply_text(t_bot(lang_code, "tg_verify.opening_telegram"), reply_markup=keyboard)


async def _on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """EN: Handle inline callbacks for account confirmation and reset-code sending.
    RU: Обработать inline-callback для подтверждения аккаунта и отправки reset-кода.
    """

    del context
    query = update.callback_query
    if query is None or update.effective_user is None:
        return

    data = str(query.data or "")
    lang_code = getattr(update.effective_user, "language_code", "ru")
    if ":" not in data:
        await query.answer()
        return
    action, raw_id = data.split(":", 1)
    try:
        token_id = int(raw_id)
    except Exception:
        await query.answer()
        return
    tg_user_id = int(update.effective_user.id)

    if action == "confirm":
        result = await asyncio.to_thread(confirm_link_token, token_id, tg_user_id)
        if result.get("ok"):
            await query.edit_message_text(t_bot(lang_code, "bot.msg_verified_ok"))
        elif str(result.get("error")) == "ALREADY_LINKED":
            await query.edit_message_text(t_bot(lang_code, "bot.msg_already_verified"))
        else:
            await query.edit_message_text(t_bot(lang_code, "bot.msg_link_expired"))
        await query.answer()
        return

    if action == "reset":
        result = await asyncio.to_thread(send_reset_code_for_link_token, token_id, tg_user_id)
        if result.get("ok"):
            await query.edit_message_text(t_bot(lang_code, "reset.info.request_sent"))
        elif str(result.get("error")) == "NEED_CONFIRM_FIRST":
            await query.edit_message_text(t_bot(lang_code, "bot.msg_need_confirm_first"))
        else:
            await query.edit_message_text(t_bot(lang_code, "bot.msg_link_expired"))
        await query.answer()
        return

    await query.answer()


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
    RU: Запустить фоновой таск outbox-воркера после инициализации бота.
    """

    app.bot_data["outbox_task"] = asyncio.create_task(_outbox_loop(app))


async def _on_post_shutdown(app: Application) -> None:
    """EN: Stop background outbox worker task on bot shutdown.
    RU: Остановить фоновый таск outbox-воркера при завершении бота.
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
    """EN: Run long-polling bot with deep-link `/start` + inline actions and outbox worker.
    RU: Запустить бота в long-polling режиме с deep-link `/start`, inline-действиями и воркером outbox.
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
    app.add_handler(CallbackQueryHandler(_on_callback))

    logger.info("telegram bot started")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
