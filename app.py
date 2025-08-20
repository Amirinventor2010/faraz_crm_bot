import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramNetworkError, TelegramUnauthorizedError

from config import BOT_TOKEN
from handlers import common, admin, staff, customer
from db.base import engine
from db.models import Base

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

dp.include_router(common.router)
dp.include_router(admin.router)
dp.include_router(staff.router)
dp.include_router(customer.router)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logging.info("✅ Database schema ensured (tables created if missing).")

async def main():
    logging.info("✅ Bot is starting...")
    await init_db()

    try:
        me = await bot.get_me()
        logging.info("🤖 Running for bot @%s id=%s — %r", me.username, me.id, me.first_name)
    except TelegramUnauthorizedError:
        logging.error("❌ BOT_TOKEN نادرست است یا دسترسی باطل شده.")
        return
    except TelegramNetworkError as e:
        logging.error("❌ خطای شبکه هنگام ارتباط با تلگرام: %s", e)

    await dp.start_polling(bot, allowed_updates=None, drop_pending_updates=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("🛑 Bot stopped by user")
