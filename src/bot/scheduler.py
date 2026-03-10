"""Автоматическое сканирование и анализ по расписанию."""

import json

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from loguru import logger

from src.config import settings


async def auto_scan_and_analyze(bot: Bot):
    """Сканировать новые заказы, анализировать, уведомить админа о подходящих."""
    if not settings.telegram_admin_id:
        return

    admin_id = settings.telegram_admin_id

    try:
        # 1. Сканируем
        from src.kwork.categories import ACTIVE_CATEGORIES
        from src.kwork.parser import scan_new_projects

        new_orders = await scan_new_projects(ACTIVE_CATEGORIES)
        if not new_orders:
            logger.info("Автосканирование: новых заказов нет")
            return

        logger.info(f"Автосканирование: найдено {len(new_orders)} новых заказов")

        # 2. Анализируем новые
        from src.agents.analyzer import AnalyzerAgent

        analyzer = AnalyzerAgent()
        results = await analyzer.run()

        if not results:
            return

        # 3. Фильтруем подходящие
        good = [r for r in results if r["score"] >= settings.min_score_threshold]

        if not good:
            logger.info(f"Автосканирование: {len(results)} заказов, подходящих нет")
            return

        # 4. Уведомляем админа о подходящих заказах
        text = f"Новые подходящие заказы ({len(good)}):\n\n"
        buttons = []

        for r in sorted(good, key=lambda x: x["score"], reverse=True):
            text += (
                f"#{r['order_id']} [{r['score']}] {r['title'][:45]}\n"
                f"  {r['work_type']} | {r['suggested_price']}р.\n"
                f"  {r['reasoning'][:80]}\n\n"
            )
            buttons.append([InlineKeyboardButton(
                text=f"Отклик на #{r['order_id']} ({r['score']}б.)",
                callback_data=f"pitch_{r['order_id']}",
            )])

        api_cost = analyzer.claude.estimated_cost_usd
        text += f"API: ~${api_cost}"

        # Записываем расходы и статистику
        from src.utils.finance import record_api_cost, update_daily_stats
        if api_cost > 0:
            record_api_cost(api_cost, f"Автосканирование: {len(results)} заказов")
        update_daily_stats(
            orders_scanned=len(new_orders),
            orders_analyzed=len(results),
            api_cost=api_cost,
        )

        kb = InlineKeyboardMarkup(inline_keyboard=buttons)

        if len(text) > 4000:
            text = text[:4000] + "\n...(обрезано)"

        await bot.send_message(admin_id, text, reply_markup=kb)
        logger.info(f"Автосканирование: отправлено {len(good)} подходящих заказов")

    except Exception as e:
        logger.error(f"Ошибка автосканирования: {e}")
        try:
            await bot.send_message(admin_id, f"Ошибка автосканирования: {e}")
        except Exception:
            pass
