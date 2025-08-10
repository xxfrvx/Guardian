from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, ConversationHandler, MessageHandler, filters, CallbackQueryHandler
from app.services import coins
from app.services.moderation import is_admin
from app.keyboards import coin_case_kb

NAME, SYMBOL, CHAIN, CONTRACT, REASONS = range(5)

async def coin_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("Название монеты:")
    return NAME

async def coin_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["coin_name"] = update.message.text.strip()
    await update.message.reply_text("Символ (например, DOGE). Если нет — напишите «нет».")
    return SYMBOL

async def coin_symbol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sym = update.message.text.strip()
    context.user_data["coin_symbol"] = None if sym.lower() == "нет" else sym
    await update.message.reply_text("Сеть (ETH/BSC/SOL/TON и т.п.). Если нет — «нет».")
    return CHAIN

async def coin_chain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ch = update.message.text.strip()
    context.user_data["coin_chain"] = None if ch.lower() == "нет" else ch
    await update.message.reply_text("Контракт (если есть). Если нет — «нет».")
    return CONTRACT

async def coin_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    c = update.message.text.strip()
    context.user_data["coin_contract"] = None if c.lower() == "нет" else c
    await update.message.reply_text("Укажите признаки (через запятую): например, honeypot, mintable, заморозка, высокий налог.")
    return REASONS

async def coin_reasons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reasons = [x.strip() for x in update.message.text.split(",") if x.strip()]
    cid = await coins.report_coin(
        name=context.user_data["coin_name"],
        symbol=context.user_data.get("coin_symbol"),
        chain=context.user_data.get("coin_chain"),
        contract=context.user_data.get("coin_contract"),
        reasons=reasons or ["unspecified"],
        added_by=update.effective_user.id
    )
    await update.message.reply_text(f"Монета добавлена в очередь модерации (ID {cid}). Спасибо!")
    return ConversationHandler.END

async def coin_queue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.effective_message.reply_text("Доступ только для админов.")
    row = await coins.next_pending_coin()
    if not row:
        return await update.effective_message.reply_text("Очередь монет пуста.")
    text = (
        f"Монета #{row['id']}\n"
        f"Имя: {row['name']} | Символ: {row['symbol'] or '—'} | Сеть: {row['chain'] or '—'}\n"
        f"Контракт: {row['contract_address'] or '—'}\n"
        f"Признаки: {', '.join(row['reasons'] or [])}"
    )
    await update.effective_message.reply_text(text, reply_markup=coin_case_kb(row["id"]))

async def coin_decide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not is_admin(q.from_user.id):
        return await q.answer("Нет доступа.")
    _, action, sid = q.data.split(":")
    coin_id = int(sid)
    await coins.decide_coin(coin_id, q.from_user.id, approve=(action == "approve"))
    await q.edit_message_text(f"Монета #{coin_id} {'добавлена в список скамов' if action=='approve' else 'отклонена'}.")
    await coin_queue(update, context)

async def coin_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.effective_message.reply_text("Формат: /coin_check <контракт|символ|имя>")
    query = context.args[0]
    row = await coins.find_coin(query)
    if not row:
        return await update.effective_message.reply_text("Монета не найдена в базе. Это не гарантия безопасности.")
    status = row["status"]
    reasons = ", ".join(row["reasons"] or [])
    await update.effective_message.reply_text(
        f"Монета: {row['name']} ({row['symbol'] or '—'})\nСеть: {row['chain'] or '—'}\nКонтракт: {row['contract_address'] or '—'}\nСтатус: {status}\nПричины: {reasons}"
    )

def setup(application):
    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler("coin_report", coin_report)],
        states={
            NAME: [MessageHandler(filters.TEXT & (~filters.COMMAND), coin_name)],
            SYMBOL: [MessageHandler(filters.TEXT & (~filters.COMMAND), coin_symbol)],
            CHAIN: [MessageHandler(filters.TEXT & (~filters.COMMAND), coin_chain)],
            CONTRACT: [MessageHandler(filters.TEXT & (~filters.COMMAND), coin_contract)],
            REASONS: [MessageHandler(filters.TEXT & (~filters.COMMAND), coin_reasons)],
        },
        fallbacks=[]
    ))
    application.add_handler(CommandHandler("coin_queue", coin_queue))
    application.add_handler(CallbackQueryHandler(coin_decide, pattern="^coin:(approve|reject):\\d+$"))
    application.add_handler(CommandHandler("coin_check", coin_check))
