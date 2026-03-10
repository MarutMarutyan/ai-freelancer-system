"""Агент-стратег: рекомендации по развитию профиля."""

from loguru import logger

from src.agents.base import BaseAgent
from src.claude_api.prompts import STRATEGY_SYSTEM
from src.claude_api.schemas import StrategyAdvice
from src.config import settings
from src.database.db import get_session
from src.database.queries import get_profile_stats
from src.utils.finance import get_finance_summary
from src.utils.rate_limiter import claude_limiter


class StrategyAgent(BaseAgent):
    """Анализирует статистику и даёт рекомендации."""

    name = "strategy"

    def _build_prompt(self, stats: dict, finance: dict) -> str:
        """Сформировать промпт для стратегических рекомендаций."""
        return f"""Проанализируй текущую ситуацию фрилансера и дай рекомендации.

СТАТИСТИКА ПРОФИЛЯ:
- Всего заказов просканировано: {stats['total_orders']}
- Проанализировано: {stats['analyzed']}
- Откликов отправлено: {stats['responded']}
- Заказов выиграно: {stats['won']}
- Заказов выполнено: {stats['executed']}
- QA пройдено с первого раза: {stats['qa_first_pass']}
- Средняя оценка заказов: {stats['avg_score']}
- Конверсия откликов: {stats['conversion_rate']}%

ФИНАНСЫ:
- Общий доход: {finance['total_income']} руб.
- Расходы на API: ${finance['total_api_cost']}
- Комиссия Kwork (20%): {finance['total_commission']} руб.
- Чистая прибыль: {finance['net_profit']} руб.

КАТЕГОРИИ ЗАКАЗОВ (по частоте):
{stats['categories_summary']}

Дай конкретные, действенные рекомендации. Учитывай что это новичок на Kwork."""

    async def run(self) -> dict | None:
        """Получить стратегические рекомендации."""
        await claude_limiter.wait()

        session = get_session()
        try:
            stats = get_profile_stats(session)
            finance = get_finance_summary(session)

            prompt = self._build_prompt(stats, finance)

            result = await self.claude.ask_structured(
                prompt=prompt,
                response_model=StrategyAdvice,
                system=STRATEGY_SYSTEM,
                model=settings.analyzer_model,  # Haiku — достаточно для рекомендаций
            )

            advice = StrategyAdvice(**result)
            logger.info(f"Стратег: {len(advice.next_steps)} рекомендаций")

            return {
                "profile_tips": advice.profile_tips,
                "pricing_tips": advice.pricing_tips,
                "category_focus": advice.category_focus,
                "next_steps": advice.next_steps,
                "stats": stats,
                "finance": finance,
                "api_cost": self.claude.estimated_cost_usd,
            }

        except Exception as e:
            logger.error(f"Ошибка стратега: {e}")
            return None

        finally:
            session.close()


# Синглтон
strategy_agent = StrategyAgent()
