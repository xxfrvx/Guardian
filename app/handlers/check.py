from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from app.services import reputation
from app.utils import risk_label

async def rep_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # В группах: используй как ответ на сообщение пользователя
    if update.message.reply_to_message and update.message.reply_to_message.from_user:
        target = update.message.reply_to_message.from_user
        await reputation.ensure_user(target)
        rep = await reputation.get_rep(target.id)
        label = risk_label(rep['score'])
        return await update.effective_message.reply_text(
            f"Репутация @{target.username or target.id}: {rep['score']} ({label}) | 👍{rep['praises']} | ⚠️{rep['reports']}"
        )
    # В личке: по forward
    if update.message.forward_from:
        target = update.message.forward_from
        await reputation.ensure_user(target)
        rep = await reputation.get_rep(target.id)
        label = risk_label(rep['score'])
        return await update.effective_message.reply_text(
            f"Репутация @{target.username or target.id}: {rep['score']} ({label}) | 👍{rep['praises']} | ⚠️{rep['reports']}"
        )
    return await update.effective_message.reply_text("Ответьте командой на сообщение пользователя в чате или перешлите его сообщение в личку боту.")

def setup(application):
    application.add_handler(CommandHandler("rep", rep_cmd))
