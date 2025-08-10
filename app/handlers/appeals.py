from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, ConversationHandler, MessageHandler, filters
from app.services import reputation
from app.services.moderation import is_admin

CASE, MESSAGE = range(2)

async def appeal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("Укажите номер дела (ID), по которому хотите подать апелляцию.")
    return CASE

async def appeal_case(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        cid = int(update.message.text.strip().lstrip("#"))
    except:
        await update.message.reply_text("Неверный формат. Пришлите число (ID дела).")
        return CASE
    context.user_data["appeal_case_id"] = cid
    await update.message.reply_text("Опишите, почему решение должно быть пересмотрено.")
    return MESSAGE

async def appeal_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = context.user_data["appeal_case_id"]
    msg = update.message.text
    aid = await reputation.create_appeal(cid, update.effective_user.id, msg)
    await update.message.reply_text(f"Апелляция №{aid} отправлена. Спасибо.")
    return ConversationHandler.END

async def review_appeal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.effective_message.reply_text("Доступ только для админов.")
    ap = await reputation.next_pending_appeal()
    if not ap:
        return await update.effective_message.reply_text("Апелляций нет.")
    text = (
        f"Апелляция #{ap['id']} по делу #{ap['case_id']}\n"
        f"Сообщение: {ap['message']}\n"
        f"Статус дела: {ap['case_status']}"
    )
    await update.effective_message.reply_text(text + "\nИспользуйте /approve_appeal <id> или /reject_appeal <id> <причина>.")

async def approve_appeal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.effective_message.reply_text("Нет доступа.")
    if not context.args:
        return await update.effective_message.reply_text("Формат: /approve_appeal <id>")
    await reputation.decide_appeal(int(context.args[0]), update.effective_user.id, True, None)
    await update.effective_message.reply_text("Апелляция одобрена.")

async def reject_appeal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.effective_message.reply_text("Нет доступа.")
    if not context.args:
        return await update.effective_message.reply_text("Формат: /reject_appeal <id> <причина>")
    aid = int(context.args[0])
    reason = " ".join(context.args[1:]) if len(context.args) > 1 else None
    await reputation.decide_appeal(aid, update.effective_user.id, False, reason)
    await update.effective_message.reply_text("Апелляция отклонена.")

def setup(application):
    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler("appeal", appeal_cmd)],
        states={
            CASE: [MessageHandler(filters.TEXT & (~filters.COMMAND), appeal_case)],
            MESSAGE: [MessageHandler(filters.TEXT & (~filters.COMMAND), appeal_message)],
        },
        fallbacks=[]
    ))
    application.add_handler(CommandHandler("review_appeals", review_appeal))
    application.add_handler(CommandHandler("approve_appeal", approve_appeal))
    application.add_handler(CommandHandler("reject_appeal", reject_appeal))
