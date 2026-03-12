"""Агент-анализатор заказов через Claude API."""

import json

from loguru import logger

from src.agents.base import BaseAgent
from src.claude_api.prompts import ANALYZER_SYSTEM
from src.claude_api.schemas import OrderAnalysis
from src.config import settings
from src.database.db import get_session
from src.database.models import Order
from src.database.queries import get_new_orders, update_order_analysis
from src.utils.rate_limiter import claude_limiter


class AnalyzerAgent(BaseAgent):
    """Анализирует заказы и ставит оценку 0-100."""

    name = "analyzer"

    def _build_prompt(self, order: Order) -> str:
        """Сформировать промпт для анализа заказа."""
        budget_info = ""
        if order.budget_max:
            budget_info = f"Бюджет: до {order.budget_max} руб."
        else:
            budget_info = "Бюджет: не указан"

        return f"""Оцени этот заказ с фриланс-биржи Kwork:

Заголовок: {order.title}
Категория: {order.category}
{budget_info}
Срок выполнения: {order.deadline or "не указан"} дней
Количество откликов: {order.responses_count}
Заказчик: {order.client_name or "неизвестен"}
Заказов у клиента: {order.client_reviews_count}

Описание заказа:
{order.description}

Дай оценку по критериям и рекомендацию."""

    async def analyze_order(self, order: Order) -> OrderAnalysis | None:
        """Проанализировать один заказ."""
        await claude_limiter.wait()

        prompt = self._build_prompt(order)

        try:
            result = await self.claude.ask_structured(
                prompt=prompt,
                response_model=OrderAnalysis,
                system=ANALYZER_SYSTEM,
                model=settings.analyzer_model,
            )

            analysis = OrderAnalysis(**result)
            logger.info(
                f"Заказ #{order.id} '{order.title[:30]}...' -> "
                f"оценка={analysis.score}, рекомендация={analysis.recommendation}"
            )
            return analysis

        except Exception as e:
            logger.error(f"Ошибка анализа заказа #{order.id}: {e}")
            return None

    async def run(self, limit: int = 0) -> list[dict]:
        """Проанализировать все новые заказы.

        Args:
            limit: Максимум заказов для анализа (0 = все)

        Returns:
            Список результатов анализа
        """
        session = get_session()
        try:
            orders = get_new_orders(session)
            if limit > 0:
                orders = orders[:limit]

            if not orders:
                logger.info("Нет новых заказов для анализа")
                return []

            logger.info(f"Начинаю анализ {len(orders)} заказов...")
            self.claude.reset_counters()
            results = []

            for order in orders:
                analysis = await self.analyze_order(order)
                if not analysis:
                    continue

                # Сохраняем результат в БД
                update_order_analysis(
                    order_id=order.id,
                    score=analysis.score,
                    analysis=json.dumps(analysis.model_dump(), ensure_ascii=False),
                    session=session,
                )

                results.append({
                    "order_id": order.id,
                    "title": order.title,
                    "url": order.url,
                    "score": analysis.score,
                    "recommendation": analysis.recommendation,
                    "reasoning": analysis.reasoning,
                    "suggested_price": analysis.suggested_price,
                    "estimated_time": analysis.estimated_time,
                    "work_type": analysis.work_type,
                })

            api_cost = self.claude.estimated_cost_usd
            logger.info(
                f"Анализ завершён. Обработано: {len(results)}/{len(orders)}. "
                f"API стоимость: ~${api_cost}"
            )

            # Записываем расход API
            if api_cost > 0:
                from src.utils.finance import record_api_cost
                record_api_cost(api_cost, f"Анализ {len(results)} заказов", session=session)

            return results

        finally:
            session.close()


# Синглтон
analyzer_agent = AnalyzerAgent()
