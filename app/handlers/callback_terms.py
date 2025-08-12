from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

async def cb_accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query

    try:
        await q.answer()  # Сигнал Telegram: клик принят

        logger.info("Callback received: %s from user %s", q.data, q.from_user.id)

        # Обновление репутации или согласия
        await reputation.mark_accept_terms(user_id=q.from_user.id)

        logger.info("mark_accept_terms completed for user %s", q.from_user.id)

        # Можно отправить подтверждение или обновить интерфейс
        await q.edit_message_text("Спасибо! Условия приняты ✅")

    except Exception as e:
        logger.error("Error in cb_accept for user %s: %s", q.from_user.id, str(e))
        await q.edit_message_text("Произошла ошибка при обработке. Попробуйте ещё раз.")
