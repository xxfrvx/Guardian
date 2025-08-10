from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, ConversationHandler, filters
from app.keyboards import report_kb, praise_kb
from app.services import reputation

TARGET, REASON, EVIDENCE = range(3)
PTARGET, PMESSAGE = range(2)

async def report_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await reputation.accepted_terms(update.effective_user.id):
        await update.effective_message.reply_text("Сначала согласитесь с условиями: /start")
        return ConversationHandler.END
    await update.effective_message.reply_text("Кого хотите пожаловаться? Перешлите сообщение пользователя или ответьте в чате его сообщению командой /report.", reply_markup=report_kb())
    return TARGET

async def report_pick_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = None
    if update.message.forward_from:
        user = update.message.forward_from
    elif update.message.reply_to_message and update.message.reply_to_message.from_user:
        user = update.message.reply_to_message.from_user
    if not user:
        await update.message.reply_text("Перешлите сообщение пользователя или ответьте на его сообщение /report.")
        return TARGET
    context.user_data["report_target_id"] = user.id
    await update.message.reply_text("Кратко опишите причину или выберите кнопку.", reply_markup=report_kb())
    return REASON

async def report_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["report_reason"] = update.message.text or "Без описания"
    await update.message.reply_text("Добавьте доказательства (ссылки/скриншоты) или напишите «нет».")
    return EVIDENCE

async def report_evidence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    evidence = update.message.text if update.message.text and update.message.text.lower() != "нет" else None
    target_id = context.user_data.get("report_target_id")
    reason = context.user_data.get("report_reason", "Без описания")
    case_id = await reputation.create_case("report", update.effective_user.id, target_id, reason, evidence)
    await update.message.reply_text(f"Жалоба №{case_id} отправлена на модерацию. Спасибо.")
    return ConversationHandler.END

async def praise_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await reputation.accepted_terms(update.effective_user.id):
        await update.effective_message.reply_text("Сначала согласитесь с условиями: /start")
        return ConversationHandler.END
    await update.effective_message.reply_text("Кого хотите похвалить? Перешлите сообщение пользователя или ответьте в чате его сообщению командой /praise.", reply_markup=praise_kb())
    return PTARGET

async def praise_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = None
    if update.message.forward_from:
        user = update.message.forward_from
    elif update.message.reply_to_message and update.message.reply_to_message.from_user:
        user = update.message.reply_to_message.from_user
    if not user:
        await update.message.reply_text("Перешлите сообщение пользователя или ответьте на его сообщение /praise.")
        return PTARGET
    context.user_data["praise_target_id"] = user.id
    await update.message.reply_text("За что хотите похвалить? Коротко опишите.")
    return PMESSAGE

async def praise_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_id = context.user_data.get("praise_target_id")
    reason = update.message.text or "Без описания"
    case_id = await reputation.create_case("praise", update.effective_user.id, target_id, reason, None)
    await update.message.reply_text(f"Похвала №{case_id} отправлена на модерацию. Спасибо!")
    return ConversationHandler.END

def setup(application):
    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler("report", report_cmd)],
        states={
            TARGET: [MessageHandler(filters.ALL & (~filters.COMMAND), report_pick_target)],
            REASON: [MessageHandler(filters.TEXT & (~filters.COMMAND), report_reason)],
            EVIDENCE: [MessageHandler(filters.TEXT & (~filters.COMMAND), report_evidence)],
        },
        fallbacks=[]
    ))
    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler("praise", praise_cmd)],
        states={
            PTARGET: [MessageHandler(filters.ALL & (~filters.COMMAND), praise_target)],
            PMESSAGE: [MessageHandler(filters.TEXT & (~filters.COMMAND), praise_message)],
        },
        fallbacks=[]
    ))
    application.add_handler(CallbackQueryHandler(lambda u, c: u.callback_query.answer("Сначала выберите цель (перешлите сообщение)."), pattern="^(report:|praise:)"))
