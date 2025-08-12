from telegram.ext import ApplicationBuilder, Application, CallbackQueryHandler
from app import config
from app.handlers import start, menu, profile, check, reports, moderation, appeals, coins, groups
from handlers.callback_terms import cb_accept

import asyncio
import logging

# Обёртка для PostgreSQL
from services.database import Database

logger = logging.getLogger(__name__)

# Инициализируем объект базы как глобальный
db = Database(dsn=config.POSTGRES_DSN)

async def main():
    await db.connect()  # Подключаемся к базе перед запуском бота

    app = ApplicationBuilder().token(config.BOT_TOKEN).concurrent_updates(True).build()

    # Подключаем хендлер согласия
    app.add_handler(CallbackQueryHandler(cb_accept, pattern="accept_terms"))

    # Устанавливаем другие хендлеры
    start.setup(app)
    menu.setup(app)
    profile.setup(app)
    check.setup(app)
    reports.setup(app)
    moderation.setup(app)
    appeals.setup(app)
    coins.setup(app)
    groups.setup(app)

    logger.info(f"{config.BOT_NAME} запущен.")
    await app.run_polling(close_loop=False)

if __name__ == "__main__":
    asyncio.run(main())
