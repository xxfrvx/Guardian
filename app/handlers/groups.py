from telegram import Update, ChatMemberUpdated
from telegram.ext import ContextTypes, ChatMemberHandler, MessageHandler, filters
from app.services import reputation
from app.utils import risk_label

async def member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmu: ChatMemberUpdated = update.chat_member
    if cmu.new_chat_member.status in ("member", "restricted") and cmu.old_chat_member.status in ("left", "kicked"):
        user = cmu.new_chat_member.user
        await reputation.ensure_user(user)
        rep = await reputation.get_rep(user.id)
        label = risk_label(rep["score"])
        await context.bot.send_message(
            chat_id=cmu.chat.id,
            text=f"Добро пожаловать, @{user.username or user.id}! Репутация: {rep['score']} ({label}) | 👍{rep['praises']} | ⚠️{rep['reports']}"
        )

SUSPICIOUS = ("http://", "https://", "t.me/", "tg://", "discord.gg", "bit.ly")

async def link_guard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    if not msg or not msg.text:
        return
    text = msg.text.lower()
    if any(x in text for x in SUSPICIOUS):
        rep = await reputation.get_rep(user.id)
        if rep["score"] < 0:
            try:
                await msg.delete()
            except:
                pass
            await update.effective_chat.send_message(
                f"Ссылка от @{user.username or user.id} удалена: низкая репутация ({rep['score']})."
            )

def setup(application):
    application.add_handler(ChatMemberHandler(member_update, ChatMemberHandler.MY_CHAT_MEMBER | ChatMemberHandler.CHAT_MEMBER))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), link_guard))
