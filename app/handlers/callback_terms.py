from telegram import Update
from telegram.ext import ContextTypes
import logging
from app.keyboards import main_menu
from app.policy_texts import TERMS, PRIVACY

logger = logging.getLogger(__name__)

async def cb_accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    data = q.data
    user_id = q.from_user.id
    logger.info("cb_accept triggered data=%s user_id=%s", data, user_id)

    try:
        if data == "accept_terms":
            db = context.bot_data["db"]
            await db.execute("UPDATE users SET accepted_terms_at = now() WHERE user_id = $1", user_id)
            logger.info("Terms accepted recorded for user %s", user_id)
            await q.edit_message_text("Спасибо! Условия приняты ✅")
            await q.message.reply_text("Главное меню:", reply_markup=main_menu())
            return

        if data == "show_terms":
            await context.bot.send_message(chat_id=user_id, text=TERMS)
            return

        if data == "show_privacy":
            await context.bot.send_message(chat_id=user_id, text=PRIVACY)
            return

        logger.warning("cb_accept received unexpected data=%s user_id=%s", data, user_id)

    except Exception as e:
        logger.exception("Ошибка при обработке callback data=%s для user_id=%s: %s", data, user_id, str(e))
        await q.edit_message_text("Ошибка при обработке. Попробуйте ещё раз позже.")
