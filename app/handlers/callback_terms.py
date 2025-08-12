from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

async def cb_accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    
    logger.info("cb_accept triggered by user_id=%s", q.from_user.id)

    try:
        db = context.bot_data["db"]
        await db.execute("UPDATE users SET accepted_terms_at = now() WHERE user_id = $1", q.from_user.id)
        logger.info("Terms accepted recorded for user %s", q.from_user.id)
        await q.edit_message_text("Спасибо! Условия приняты ✅")

    except Exception as e:
        logger.exception("Ошибка при обновлении согласия для user_id=%s: %s", q.from_user.id, str(e))
        await q.edit_message_text("Ошибка при обработке. Попробуйте ещё раз позже.")
