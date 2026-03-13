"""Агент-генератор откликов на заказы."""

import json

from loguru import logger

from src.agents.base import BaseAgent
from src.claude_api.prompts import RESPONSE_WRITER_SYSTEM
from src.claude_api.schemas import PitchResponse
from src.config import settings
from src.database.db import get_session
from src.database.models import Order, Response
from src.database.queries import get_order_by_id, save_response
from src.utils.rate_limiter import claude_limiter


class ResponseWriterAgent(BaseAgent):
    """Генерирует убедительные отклики на заказы."""

    name = "response_writer"

    def _build_prompt(self, order: Order, analysis: dict | None) -> str:
        """Сформировать промпт для генерации отклика."""
        budget_info = f"до {order.budget_max} руб." if order.budget_max else "не указан"

        analysis_info = ""
        if analysis:
            analysis_info = f"""
Результат анализа:
- Тип работы: {analysis.get('work_type', 'неизвестен')}
- Рекомендуемая цена: {analysis.get('suggested_price', 'не указана')} руб.
- Время выполнения: {analysis.get('estimated_time', 'не указано')}
- Обоснование: {analysis.get('reasoning', '')}"""

        competition = "мало конкурентов" if (order.responses_count or 0) <= 3 else f"{order.responses_count} откликов"

        return f"""Напиши выигрышный отклик на заказ с Kwork.

=== ЗАКАЗ ===
Заголовок: {order.title}
Категория: {order.category}
Бюджет: {budget_info}
Срок клиента: {order.deadline or "не указан"} дней
Конкуренция: {competition}

Описание:
{order.description}
{analysis_info}

=== ЗАДАЧА ===
Профиль новый, отзывов нет. Напиши отклик по структуре из системного промпта.
Главное — убери страх заказчика перед новичком: покажи что ты точно понял задачу и предложи гарантию результата."""

    async def generate_pitch(self, order: Order) -> PitchResponse | None:
        """Сгенерировать отклик на заказ."""
        await claude_limiter.wait()

        # Получаем анализ если есть
        analysis = None
        if order.analysis:
            try:
                analysis = json.loads(order.analysis)
            except json.JSONDecodeError:
                pass

        prompt = self._build_prompt(order, analysis)

        try:
            result = await self.claude.ask_structured(
                prompt=prompt,
                response_model=PitchResponse,
                system=RESPONSE_WRITER_SYSTEM,
                model=settings.writer_model,
            )

            pitch = PitchResponse(**result)

            # Пересчитываем дату дедлайна на основе сегодняшней даты
            import re
            from datetime import datetime, timedelta
            match = re.search(r'(\d+)', pitch.proposed_deadline or '')
            if match:
                days = int(match.group(1))
                deadline_date = datetime.now() + timedelta(days=days)
                months = ['января','февраля','марта','апреля','мая','июня',
                          'июля','августа','сентября','октября','ноября','декабря']
                date_str = f"{deadline_date.day} {months[deadline_date.month-1]}"
                pitch.proposed_deadline = f"{days} дней ({date_str})"

            logger.info(
                f"Отклик для заказа #{order.id} сгенерирован "
                f"(цена={pitch.proposed_price}, срок={pitch.proposed_deadline})"
            )
            return pitch

        except Exception as e:
            logger.error(f"Ошибка генерации отклика для заказа #{order.id}: {e}")
            return None

    async def run(self, order_id: int) -> dict | None:
        """Сгенерировать отклик для заказа и сохранить в БД.

        Args:
            order_id: ID заказа в БД

        Returns:
            Словарь с данными отклика или None
        """
        session = get_session()
        try:
            order = get_order_by_id(order_id, session)
            if not order:
                logger.error(f"Заказ #{order_id} не найден")
                return None

            if order.status == "new":
                logger.warning(
                    f"Заказ #{order_id} ещё не проанализирован. "
                    "Запусти analyze сначала."
                )
                return None

            pitch = await self.generate_pitch(order)
            if not pitch:
                return None

            # Сохраняем отклик в БД
            response = Response(
                order_id=order.id,
                draft_text=pitch.pitch_text,
                proposed_price=pitch.proposed_price,
                proposed_deadline=pitch.proposed_deadline,
                status="draft",
            )
            save_response(response, session)

            # Обновляем статус заказа
            order.status = "responded"
            session.add(order)
            session.commit()

            # Записываем расход API
            api_cost = self.claude.estimated_cost_usd
            if api_cost > 0:
                from src.utils.finance import record_api_cost
                record_api_cost(api_cost, f"Отклик на заказ #{order_id}", order_id, session)

            return {
                "order_id": order.id,
                "order_title": order.title,
                "order_url": order.url,
                "pitch_text": pitch.pitch_text,
                "proposed_price": pitch.proposed_price,
                "proposed_deadline": pitch.proposed_deadline,
                "key_points": pitch.key_points,
                "mini_demo": pitch.mini_demo,
                "response_id": response.id,
            }

        finally:
            session.close()


# Синглтон
response_writer = ResponseWriterAgent()
