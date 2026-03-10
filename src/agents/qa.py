"""Агент проверки качества (QA)."""

from loguru import logger

from src.agents.base import BaseAgent
from src.claude_api.prompts import QA_SYSTEM
from src.claude_api.schemas import QAResult
from src.config import settings
from src.utils.rate_limiter import claude_limiter


class QAAgent(BaseAgent):
    """Проверяет выполненную работу на соответствие ТЗ."""

    name = "qa"

    def _build_prompt(self, task_description: str, result_text: str) -> str:
        """Сформировать промпт для проверки качества."""
        return f"""Проверь выполненную работу на соответствие ТЗ.

ТЕХНИЧЕСКОЕ ЗАДАНИЕ:
{task_description}

ВЫПОЛНЕННАЯ РАБОТА:
{result_text}

Составь чек-лист по каждому пункту ТЗ и оцени качество."""

    async def run(self, task_description: str = "", result_text: str = "") -> QAResult | None:
        """Основной метод — проверить качество работы."""
        return await self.check_quality(task_description, result_text)

    async def check_quality(self, task_description: str, result_text: str) -> QAResult | None:
        """Проверить качество работы."""
        await claude_limiter.wait()

        prompt = self._build_prompt(task_description, result_text)

        try:
            result = await self.claude.ask_structured(
                prompt=prompt,
                response_model=QAResult,
                system=QA_SYSTEM,
                model=settings.writer_model,  # Sonnet — качественнее для QA
            )

            qa = QAResult(**result)
            status = "PASSED" if qa.passed else "FAILED"
            logger.info(f"QA проверка: {status} ({len(qa.checklist)} пунктов)")
            return qa

        except Exception as e:
            logger.error(f"Ошибка QA проверки: {e}")
            return None


# Синглтон
qa_agent = QAAgent()
