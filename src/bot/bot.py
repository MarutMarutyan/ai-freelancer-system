"""Telegram-бот AI Freelancer System."""

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from loguru import logger

from src.bot.handlers import router
from src.bot.scheduler import auto_scan_and_analyze
from src.config import settings
from src.database.db import init_db


async def set_bot_commands(bot: Bot):
    """Установить меню команд бота (видно в Telegram)."""
    commands = [
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="scan", description="Сканировать заказы"),
        BotCommand(command="analyze", description="Анализировать новые"),
        BotCommand(command="orders", description="Лучшие заказы"),
        BotCommand(command="execute", description="Выполнить заказ"),
        BotCommand(command="finance", description="Финансы"),
        BotCommand(command="strategy", description="Рекомендации AI"),
        BotCommand(command="status", description="Статус системы"),
    ]
    await bot.set_my_commands(commands)


async def scheduler_loop(bot: Bot):
    """Фоновый цикл автосканирования."""
    interval = settings.scan_interval_minutes * 60  # в секунды
    logger.info(f"Автосканирование каждые {settings.scan_interval_minutes} мин.")

    # Первый запуск через 30 секунд после старта
    await asyncio.sleep(30)

    while True:
        try:
            await auto_scan_and_analyze(bot)
        except Exception as e:
            logger.error(f"Ошибка в scheduler_loop: {e}")
        await asyncio.sleep(interval)


async def start_bot():
    """Запустить Telegram-бота."""
    if not settings.telegram_bot_token:
        logger.error("TELEGRAM_BOT_TOKEN не настроен в .env")
        return

    init_db()

    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher()
    dp.include_router(router)

    # Устанавливаем меню команд
    await set_bot_commands(bot)

    logger.info("Telegram-бот запущен. Нажми Ctrl+C для остановки.")

    # Уведомляем админа о запуске
    if settings.telegram_admin_id:
        try:
            from src.bot.handlers import main_menu_kb
            await bot.send_message(
                settings.telegram_admin_id,
                f"Bot запущен!\n"
                f"Автосканирование каждые {settings.scan_interval_minutes} мин.\n"
                f"Порог оценки: {settings.min_score_threshold}",
                reply_markup=main_menu_kb(),
            )
        except Exception as e:
            logger.warning(f"Не удалось отправить приветствие: {e}")

    # Запускаем планировщик параллельно с polling
    scheduler_task = asyncio.create_task(scheduler_loop(bot))

    try:
        await dp.start_polling(bot)
    finally:
        scheduler_task.cancel()
        await bot.session.close()


async def start_api():
    """Запустить FastAPI сервер."""
    import uvicorn
    from src.api import app as fastapi_app
    config = uvicorn.Config(fastapi_app, host="0.0.0.0", port=8000, log_level="warning")
    server = uvicorn.Server(config)
    await server.serve()


async def start_all():
    """Запустить бота и API одновременно."""
    await asyncio.gather(
        start_bot(),
        start_api(),
    )
