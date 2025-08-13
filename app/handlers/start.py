from app import db
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler
from app.keyboards import consent_kb, main_menu
from app.policy_texts import TERMS, PRIVACY
from app.services import reputation
from app import config
import logging
import time

logger = logging.getLogger(__name__)

WELCOME = (
    f"Привет! Я {config.BOT_NAME} — твой защитник в мире телеграм.\n"
    "Я обладаю механикой публичной репутации, реестром скаммеров и модерацией жалоб.\n\n"
    "Чтобы продолжить, согласитесь с условиями политики."
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info("START /start user_id=%s username=%s", user.id, user.username)

    try:
        t0 = time.perf_counter()
        await reputation.ensure_user(user)
        logger.info("ensure_user OK (%.1f ms) user_id=%s", (time.perf_counter() - t0) * 1000, user.id)
    except Exception:
        logger.exception("ensure_user FAILED user_id=%s", user.id)
        await update.effective_message.reply_text("Техническая ошибка. Попробуйте позже.")
        return

    try:
        t0 = time.perf_counter()
        accepted = await reputation.accepted_terms(user.id)
        logger.info("accepted_terms=%s (%.1f ms) user_id=%s", accepted, (time.perf_counter() - t0) * 1000, user.id)
    except Exception:
        logger.exception("accepted_terms FAILED user_id=%s", user.id)
        await update.effective_message.reply_text("Техническая ошибка. Попробуйте позже.")
        return

    if accepted:
        await update.effective_message.reply_text("Главное меню:", reply_markup=main_menu())
    else:
        await update.effective_message.reply_text(WELCOME, reply_markup=consent_kb())

async def cb_accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    logger.warning("cb_accept CALLED — data=%s user_id=%s", q.data, q.from_user.id)

    data = q.data
    logger.info("CALLBACK data=%s user_id=%s", data, q.from_user.id)
   

    if data == "accept_terms":
        t0 = time.perf_counter()
        try:
            await reputation.mark_accept_terms(q.from_user.id, config.TERMS_VERSION)
            logger.info("mark_accept_terms OK (%.1f ms) user_id=%s", (time.perf_counter() - t0) * 1000, q.from_user.id)
        except Exception:
            logger.exception("mark_accept_terms FAILED user_id=%s", q.from_user.id)
            await q.message.reply_text("Ошибка при записи согласия. Попробуйте ещё раз позже.")
            return
        await q.edit_message_text("Спасибо! Доступ открыт.")
        await q.message.reply_text("Главное меню:", reply_markup=main_menu())
    elif data == "show_terms":
        logger.info("SHOW_TERMS user_id=%s", q.from_user.id)
        await context.bot.send_message(chat_id=q.from_user.id, text=TERMS)
    elif data == "show_privacy":
        logger.info("SHOW_PRIVACY user_id=%s", q.from_user.id)
        await context.bot.send_message(chat_id=q.from_user.id, text=PRIVACY)

def setup(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(cb_accept, pattern="^(accept_terms|show_terms|show_privacy)$"))
