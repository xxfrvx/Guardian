from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from app.services import reputation
from app.utils import risk_label

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await reputation.ensure_user(user)
    rep = await reputation.get_rep(user.id)
    label = risk_label(rep['score'])
    text = (
        f"Профиль @{user.username or user.id}\n"
        f"Репутация: {rep['score']} ({label})\n"
        f"Похвал: {rep['praises']} | Жалоб: {rep['reports']}\n"
        "Команды: /report, /praise, /appeal, /menu"
    )
    await update.effective_message.reply_text(text)

def setup(application):
    application.add_handler(CommandHandler("profile", profile))
