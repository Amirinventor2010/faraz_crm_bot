import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramNetworkError, TelegramUnauthorizedError

from config import BOT_TOKEN
from handlers import common, admin, staff, customer  # ← مشتری هم اضافه شد

# ساخت جدول‌ها
from db.base import engine
from db.models import Base

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

# Bot/Dispatcher
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()

# اتصال روترها
dp.include_router(common.router)
dp.include_router(admin.router)
dp.include_router(staff.router)
dp.include_router(customer.router)  # ← اضافه شد

async def init_db():
    """ایجاد اسکیمای دیتابیس در صورت نبود جداول"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logging.info("✅ Database schema ensured (tables created if missing).")

async def main():
    logging.info("✅ Bot is starting...")
    # آماده‌سازی دیتابیس
    await init_db()

    # امتحان گرفتن اطلاعات ربات برای لاگ بهتر
    try:
        me = await bot.get_me()
        logging.info("🤖 Running for bot @%s id=%s — %r",
                     me.username, me.id, me.first_name)
    except TelegramUnauthorizedError:
        logging.error("❌ BOT_TOKEN نادرست است یا دسترسی باطل شده.")
        return
    except TelegramNetworkError as e:
        logging.error("❌ خطای شبکه هنگام ارتباط با تلگرام: %s", e)

    # شروع polling
    # drop_pending_updates=True => پیام‌های قدیمی مصرف نشوند
    await dp.start_polling(bot, allowed_updates=None, drop_pending_updates=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("🛑 Bot stopped by user")
