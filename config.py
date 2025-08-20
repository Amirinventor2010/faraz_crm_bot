import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DB_URL = os.getenv("DB_URL", "sqlite+aiosqlite:///./faraz.sqlite3")

# لیست مدیرها: "5010464861,114917704"
_raw_admin_ids = os.getenv("ADMIN_TELEGRAM_IDS", "")
ADMIN_TELEGRAM_IDS = [s.strip() for s in _raw_admin_ids.split(",") if s.strip()]

# گروه گزارش و تاپیک‌ها (اختیاری)
def _to_int_or_none(val: str):
    try:
        return int(val)
    except Exception:
        return None

REPORTS_GROUP_ID = _to_int_or_none(os.getenv("REPORTS_GROUP_ID", ""))  # مثلا: -1002222333444
STAFF_TOPIC_ID   = _to_int_or_none(os.getenv("STAFF_TOPIC_ID", ""))    # مثلا: 12
CLIENT_TOPIC_ID  = _to_int_or_none(os.getenv("CLIENT_TOPIC_ID", ""))   # مثلا: 34
