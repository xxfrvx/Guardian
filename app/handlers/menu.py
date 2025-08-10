from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler
from app.keyboards import main_menu
from app.services import reputation

async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await reputation.accepted_terms(update.effective_user.id):
        return await update.effective_message.reply_text("Сначала согласитесь с условиями: /start")
    await update.effective_message.reply_text("Главное меню:", reply_markup=main_menu())

async def menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data
    await q.answer()
    if data == "menu:check":
        await q.message.reply_text("Пришлите сообщение пользователя (forward) или ответьте командой /rep на его сообщение в чате.")
    elif data == "menu:report":
        await q.message.reply_text("Откройте жалобу командой /report")
    elif data == "menu:praise":
        await q.message.reply_text("Откройте похвалу командой /praise")
    elif data == "menu:coin_check":
        await q.message.reply_text("Команда /coin_check <контракт|символ|имя>")
    elif data == "menu:coin_report":
        await q.message.reply_text("Откройте репорт монеты: /coin_report")
    elif data == "menu:moderation":
        await q.message.reply_text("Очередь модерации: /moderation\nАпелляции: /review_appeals\nМонеты: /coin_queue")
    elif data == "menu:profile":
        await q.message.reply_text("Ваш профиль: /profile")

def setup(application):
    application.add_handler(CommandHandler("menu", menu_cmd))
    application.add_handler(CallbackQueryHandler(menu_router, pattern="^menu:"))
