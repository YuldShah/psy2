import asyncio
import logging
from aiogram import Bot, Dispatcher
from bot.config import BOT_TOKEN
from bot.database.main import init_db
from bot.handlers import common, student, chat, appointment, dashboard, user_management

from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Initialize Database
    await init_db()
    
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    
    # Include routers (order matters - more specific first)
    dp.include_router(common.router)
    dp.include_router(appointment.router)  # Before user_management to handle specific callbacks
    dp.include_router(student.router)
    dp.include_router(chat.router)
    dp.include_router(dashboard.router)
    dp.include_router(user_management.router)  # More general, should be last
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
