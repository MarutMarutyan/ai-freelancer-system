"""Агент-исполнитель заказов."""

import json

from loguru import logger

from src.agents.base import BaseAgent
from src.claude_api.prompts import EXECUTOR_SYSTEM
from src.config import settings
from src.database.db import get_session
from src.database.models import Execution, Order
from src.database.queries import get_order_by_id
from src.utils.rate_limiter import claude_limiter


class ExecutorAgent(BaseAgent):
    """Выполняет заказы: пишет тексты, код, переводы."""

    name = "executor"

    def _build_prompt(self, order: Order, feedback: str = "") -> str:
        """Сформировать промпт для выполнения заказа."""
        budget_info = f"до {order.budget_max} руб." if order.budget_max else "не указан"

        # Извлекаем тип работы из анализа
        work_type = "text"
        if order.analysis:
            try:
                analysis = json.loads(order.analysis)
                work_type = analysis.get("work_type", "text")
            except json.JSONDecodeError:
                pass

        prompt = f"""Выполни этот заказ с Kwork:

Заголовок: {order.title}
Категория: {order.category}
Бюджет: {budget_info}
Тип работы: {work_type}

Техническое задание (ТЗ):
{order.description}

Выполни работу ТОЧНО по ТЗ. Результат должен быть готов к отправке заказчику."""

        if feedback:
            prompt += f"""

ВАЖНО: Предыдущая версия не прошла проверку качества.
Замечания QA-инспектора:
{feedback}

Исправь все указанные проблемы."""

        return prompt

    async def execute_order(self, order: Order, feedback: str = "") -> str | None:
        """Выполнить заказ."""
        await claude_limiter.wait()

        prompt = self._build_prompt(order, feedback)

        try:
            result = await self.claude.ask(
                prompt=prompt,
                system=EXECUTOR_SYSTEM,
                model=settings.executor_model,
                max_tokens=8192,
            )

            logger.info(f"Заказ #{order.id} выполнен ({len(result)} символов)")
            return result

        except Exception as e:
            logger.error(f"Ошибка выполнения заказа #{order.id}: {e}")
            return None

    async def run(self, order_id: int) -> dict | None:
        """Выполнить заказ и сохранить результат.

        Args:
            order_id: ID заказа в БД

        Returns:
            Словарь с результатом или None
        """
        session = get_session()
        try:
            order = get_order_by_id(order_id, session)
            if not order:
                logger.error(f"Заказ #{order_id} не найден")
                return None

            result_text = await self.execute_order(order)
            if not result_text:
                return None

            # Сохраняем в БД
            execution = Execution(
                order_id=order.id,
                task_description=order.description,
                result_text=result_text,
                status="review",
            )
            session.add(execution)
            session.commit()
            session.refresh(execution)

            return {
                "order_id": order.id,
                "order_title": order.title,
                "execution_id": execution.id,
                "result_text": result_text,
                "status": "review",
            }

        finally:
            session.close()


# Синглтон
executor_agent = ExecutorAgent()
