"""Настройки приложения. Загружает переменные из .env файла."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = BASE_DIR / "templates"


class Settings(BaseSettings):
    # Claude API
    anthropic_api_key: str = Field(default="", alias="APP_ANTHROPIC_KEY")

    # Telegram Bot
    telegram_bot_token: str = ""
    telegram_admin_id: int = 0

    # Сканер заказов
    scan_interval_minutes: int = 5
    min_score_threshold: int = 50

    # Kwork
    kwork_request_delay_seconds: int = 10

    # База данных
    database_url: str = f"sqlite:///{DATA_DIR / 'freelancer.db'}"

    # Модели Claude
    analyzer_model: str = "claude-haiku-4-5-20251001"
    writer_model: str = "claude-sonnet-4-6"
    executor_model: str = "claude-sonnet-4-6"

    model_config = {
        "env_file": str(BASE_DIR / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "populate_by_name": True,
    }


settings = Settings()
