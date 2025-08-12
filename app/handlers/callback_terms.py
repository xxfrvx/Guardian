from telegram import Update
from telegram.ext import ContextTypes
import time
import asyncio
import logging
logger = logging.getLogger(__name__)

async def cb_accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()  # Обязательно, чтобы убрать крутилку
    logger.info("Callback received: %s from user %s", q.data, q.from_user.id)

    if q.data == "accept_terms":
        t0 = time.perf_counter()
        try:
            # Жёсткий timeout на всякий случай
            await asyncio.wait_for(
                reputation.mark_accept_terms(q.from_user.id, config.TERMS_VERSION),
                timeout=5.0
            )
            logger.info("mark_accept_terms completed for user %s", q.from_user.id)
        except asyncio.TimeoutError:
            logger.warning("mark_accept_terms TIMEOUT")
            await q.message.reply_text("Сервер занят, попробуйте позже.")
            return
        except Exception as e:
            logger.exception("mark_accept_terms FAILED")
            await q.message.reply_text("Ошибка при записи согласия. Попробуйте ещё раз позже.")
            return

        await q.edit_message_text("Спасибо! Доступ открыт.")
        await q.message.reply_text("Главное меню:", reply_markup=main_menu())
