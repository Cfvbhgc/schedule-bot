import os
import asyncio
import logging

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

import db
from scheduler import setup_scheduler, scheduler

# загружаем переменные окружения из .env
load_dotenv()

# логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    """Инициализация при запуске: подключаемся к БД, создаём таблицы, запускаем scheduler."""
    logger.info("Starting up...")
    await db.create_pool()
    await db.init_db()
    logger.info("Database initialized")

    # запуск планировщика напоминаний
    setup_scheduler(bot)
    logger.info("Bot is ready")


async def on_shutdown(bot: Bot):
    """Graceful shutdown: закрываем пул и scheduler."""
    logger.info("Shutting down...")
    scheduler.shutdown(wait=False)
    await db.close_pool()
    logger.info("Cleanup done")


async def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN not found in environment variables!")

    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode="HTML")
    )
    dp = Dispatcher(storage=MemoryStorage())

    # подключаем роутеры
    from handlers.start import router as start_router
    from handlers.booking import router as booking_router
    from handlers.schedule import router as schedule_router
    from handlers.admin import router as admin_router

    dp.include_router(start_router)
    dp.include_router(booking_router)
    dp.include_router(schedule_router)
    dp.include_router(admin_router)

    # lifecycle hooks
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # start polling
    logger.info("Starting polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
