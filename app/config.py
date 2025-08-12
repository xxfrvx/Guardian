import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_NAME = os.getenv("BOT_NAME", "Guardian")
DATABASE_URL = os.getenv("DATABASE_URL")

def _parse_admins(value: str):
    if not value:
        return set()
    return {int(x.strip()) for x in value.split(",") if x.strip().isdigit()}

ADMIN_IDS = _parse_admins(os.getenv("ADMIN_IDS", "946924054"))
TERMS_VERSION = "2025-08-10"
