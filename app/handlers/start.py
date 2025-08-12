from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler
from app.keyboards import consent_kb, main_menu
from app.policy_texts import TERMS, PRIVACY
from app.services import reputation
from app import config

WELCOME = (
    f"Привет! Я {config.BOT_NAME} — защита крипто/NFT-комьюнити.\n"
    "Публичная репутация, модерация жалоб и апелляции.\n\n"
    "Чтобы продолжить, согласитесь с условиями."
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await reputation.ensure_user(user)
    if await reputation.accepted_terms(user.id):
        await update.effective_message.reply_text("Главное меню:", reply_markup=main_menu())
    else:
        await update.effective_message.reply_text(WELCOME, reply_markup=consent_kb())

async def cb_accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    if data == "accept_terms":
        await reputation.mark_accept_terms(q.from_user.id, config.TERMS_VERSION)
        await q.edit_message_text("Спасибо! Доступ открыт.")
        await q.message.reply_text("Главное меню:", reply_markup=main_menu())
    elif data == "show_terms":
        await q.from_user.send_message(TERMS)
    elif data == "show_privacy":
        await q.from_user.send_message(PRIVACY)

def setup(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(cb_accept, pattern="^(accept_terms|show_terms|show_privacy)$"))
def setup(app):
    app.add_handler(CallbackQueryHandler(handle_terms_accept, pattern="terms_accept"))
    app.add_handler(CallbackQueryHandler(handle_terms_show, pattern="terms_show"))
