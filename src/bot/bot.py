"""Telegram-бот AI Freelancer System."""

from aiogram import Bot, Dispatcher
from loguru import logger

from src.bot.handlers import router
from src.config import settings
from src.database.db import init_db


async def start_bot():
    """Запустить Telegram-бота."""
    if not settings.telegram_bot_token:
        logger.error("TELEGRAM_BOT_TOKEN не настроен в .env")
        return

    init_db()

    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher()
    dp.include_router(router)

    logger.info("Telegram-бот запущен. Нажми Ctrl+C для остановки.")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
