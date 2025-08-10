from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from app.services.moderation import is_admin
from app.services import reputation
from app.keyboards import moderation_case_kb

async def moderation_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.effective_message.reply_text("Доступ только для админов.")
    case = await reputation.next_pending_case()
    if not case:
        return await update.effective_message.reply_text("Очередь пустая. Отличная работа!")
    text = (
        f"Дело #{case['id']} [{case['type']} | {case['status']}]\n"
        f"Цель: @{case['target_username'] or case['target_user_id']}\n"
        f"Автор: @{case['author_username'] or case['author_user_id']}\n"
        f"Причина: {case['reason']}\n"
        f"Доказательства: {case['evidence'] or '—'}"
    )
    await update.effective_message.reply_text(text, reply_markup=moderation_case_kb(case["id"]))

async def mod_decide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not is_admin(q.from_user.id):
        return await q.answer("Нет доступа.")
    _, action, sid = q.data.split(":")
    case_id = int(sid)
    approve = (action == "approve")
    await reputation.decide_case(case_id, q.from_user.id, approve, decision_reason=None)
    await q.edit_message_text(f"Дело #{case_id} {'одобрено' if approve else 'отклонено'}.")
    await moderation_home(update, context)

def setup(application):
    application.add_handler(CommandHandler("moderation", moderation_home))
    application.add_handler(CallbackQueryHandler(mod_decide, pattern="^mod:(approve|reject):\\d+$"))
    application.add_handler(CallbackQueryHandler(lambda u, c: u.callback_query.answer("Ок."), pattern="^mod:later$"))
