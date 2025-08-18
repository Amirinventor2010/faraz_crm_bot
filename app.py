import asyncio
import logging
from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from handlers import common, admin, staff

# ساخت جدول‌ها
from db.base import engine
from db.models import Base

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# روترها
dp.include_router(common.router)
dp.include_router(admin.router)
dp.include_router(staff.router)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logging.info("✅ Database schema ensured (tables created if missing).")

async def main():
    logging.info("✅ Bot is starting...")
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
