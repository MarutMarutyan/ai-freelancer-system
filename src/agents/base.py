"""Базовый класс для всех AI-агентов."""

from abc import ABC, abstractmethod

from loguru import logger

from src.claude_api.client import claude_client


class BaseAgent(ABC):
    """Базовый класс агента. Все агенты наследуются от него."""

    name: str = "base"

    def __init__(self):
        self.claude = claude_client
        logger.info(f"Агент [{self.name}] инициализирован")

    @abstractmethod
    async def run(self, *args, **kwargs):
        """Основной метод агента. Каждый агент реализует свою логику."""
        pass

    def __repr__(self):
        return f"<Agent: {self.name}>"
