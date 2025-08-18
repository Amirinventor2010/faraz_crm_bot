import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DB_URL = os.getenv("DB_URL", "sqlite+aiosqlite:///./faraz.sqlite3")

# به صورت "5010464861,114917704"
_raw_admin_ids = os.getenv("ADMIN_TELEGRAM_IDS", "")
ADMIN_TELEGRAM_IDS = [s.strip() for s in _raw_admin_ids.split(",") if s.strip()]
