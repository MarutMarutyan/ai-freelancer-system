"""Настройка логирования через loguru."""

import sys

from loguru import logger

from src.config import BASE_DIR

# Убираем стандартный handler
logger.remove()

# Консольный вывод — INFO и выше
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    colorize=True,
)

# Файловый лог — DEBUG и выше, ротация 10 MB
logger.add(
    BASE_DIR / "data" / "app.log",
    level="DEBUG",
    rotation="10 MB",
    retention="7 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} | {message}",
    encoding="utf-8",
)
