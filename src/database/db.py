"""Подключение к SQLite и управление сессиями."""

from sqlmodel import Session, SQLModel, create_engine

from src.config import DATA_DIR, settings

# Создаём папку data если не существует
DATA_DIR.mkdir(parents=True, exist_ok=True)

engine = create_engine(settings.database_url, echo=False)


def init_db():
    """Создать все таблицы в базе данных."""
    # Импортируем модели чтобы SQLModel знал о таблицах
    from src.database import models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    """Получить сессию для работы с БД."""
    return Session(engine)
