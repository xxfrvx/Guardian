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

# Создаём объект базы без аргументов — DSN берётся из переменной окружения
db = Database()

async def main():
    # Проверка переменной окружения
    if not os.getenv("DATABASE_URL"):
        logging.error("DATABASE_URL is not set. Please configure it in Railway Variables.")
        return

    await db.connect()

    app = ApplicationBuilder().token(config.BOT_TOKEN).concurrent_updates(True).build()

    # Делаем базу доступной из любого хендлера через context.bot_data
    app.bot_data["db"] = db

    # Хендлеры
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
    await app.run_polling(close_loop=False)

if __name__ == "__main__":
    asyncio.run(main())
