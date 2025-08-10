from telegram.ext import ApplicationBuilder
from app import config
from app.handlers import start, menu, profile, check, reports, moderation, appeals, coins, groups

def main():
    app = ApplicationBuilder().token(config.BOT_TOKEN).concurrent_updates(True).build()

    start.setup(app)
    menu.setup(app)
    profile.setup(app)
    check.setup(app)
    reports.setup(app)
    moderation.setup(app)
    appeals.setup(app)
    coins.setup(app)
    groups.setup(app)

    print(f"{config.BOT_NAME} запущен.")
    app.run_polling(close_loop=False)

if __name__ == "__main__":
    main()
