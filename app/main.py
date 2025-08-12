import asyncio
import logging
import os

from telegram.ext import ApplicationBuilder, CallbackQueryHandler

from app import config
from app.handlers import start, menu, profile, check, reports, moderation, appeals, coins, groups
from handlers.callback_terms import cb_accept
from services.database import Database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s - %(message)s"
)

db = Database()

async def setup_bot():
    await db.connect()

    app = ApplicationBuilder().token(config.BOT_TOKEN).concurrent_updates(True).build()
    app.bot_data["db"] = db

    app.add_handler(CallbackQueryHandler(cb_accept, pattern="accept_terms"))

    start.setup(app)
    menu.setup(app)
    profile.setup(app)
    check.setup(app)
    reports.setup(app)
    moderation.setup(app)
    appeals.setup(app)
    coins.setup(app)
    groups.setup(app)

    logging.info(f"{config.BOT_NAME} запущен.")
    return app

# 🚀 Запускаем без asyncio.run()
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(setup_bot())
    app.run_polling()
