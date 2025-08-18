from db.crud import get_user_by_telegram_id
from utils.constants import ROLE_ADMIN, ROLE_STAFF, ROLE_CLIENT
from config import ADMIN_TELEGRAM_IDS

async def resolve_role(session, telegram_id: int):
    user = await get_user_by_telegram_id(session, telegram_id)
    if user:
        return user.role, user
    # اگر در DB نیست ولی در لیست ADMIN_TELEGRAM_IDS باشد، به عنوان مدیر موقت اجازه ورود بده
    if telegram_id in ADMIN_TELEGRAM_IDS:
        return ROLE_ADMIN, None
    return None, None