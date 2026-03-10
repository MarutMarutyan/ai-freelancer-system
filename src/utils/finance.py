"""Модуль финансов: учёт доходов, расходов, прибыли."""

from datetime import datetime, timedelta
from typing import Optional

from loguru import logger
from sqlmodel import Session, func, select

from src.database.db import get_session
from src.database.models import DailyStats, Execution, FinanceRecord, Order


def record_api_cost(
    cost_usd: float,
    description: str = "Claude API",
    order_id: int | None = None,
    session: Optional[Session] = None,
) -> None:
    """Записать расход на Claude API."""
    if cost_usd <= 0:
        return

    s = session or get_session()
    record = FinanceRecord(
        date=datetime.utcnow().strftime("%Y-%m-%d"),
        type="expense",
        category="api_cost",
        amount=cost_usd,
        description=description,
        order_id=order_id,
    )
    s.add(record)
    s.commit()
    logger.debug(f"Записан расход API: ${cost_usd:.4f} — {description}")
    if not session:
        s.close()


def record_income(
    amount_rub: float,
    order_id: int,
    description: str = "Оплата заказа",
    session: Optional[Session] = None,
) -> None:
    """Записать доход от заказа."""
    s = session or get_session()

    # Доход
    income = FinanceRecord(
        date=datetime.utcnow().strftime("%Y-%m-%d"),
        type="income",
        category="order",
        amount=amount_rub,
        description=description,
        order_id=order_id,
    )
    s.add(income)

    # Комиссия Kwork 20%
    commission = amount_rub * 0.20
    commission_record = FinanceRecord(
        date=datetime.utcnow().strftime("%Y-%m-%d"),
        type="expense",
        category="kwork_commission",
        amount=commission,
        description=f"Комиссия Kwork 20% от {amount_rub} руб.",
        order_id=order_id,
    )
    s.add(commission_record)

    s.commit()
    logger.info(f"Записан доход: {amount_rub} руб. (комиссия: {commission} руб.)")
    if not session:
        s.close()


def get_finance_summary(
    session: Optional[Session] = None,
    days: int = 30,
) -> dict:
    """Финансовая сводка за последние N дней."""
    s = session or get_session()
    cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")

    try:
        # Доходы
        income_result = s.exec(
            select(func.coalesce(func.sum(FinanceRecord.amount), 0.0)).where(
                FinanceRecord.type == "income",
                FinanceRecord.date >= cutoff,
            )
        ).one()
        total_income = float(income_result)

        # Расходы на API (в USD)
        api_result = s.exec(
            select(func.coalesce(func.sum(FinanceRecord.amount), 0.0)).where(
                FinanceRecord.type == "expense",
                FinanceRecord.category == "api_cost",
                FinanceRecord.date >= cutoff,
            )
        ).one()
        total_api_cost = float(api_result)

        # Комиссия Kwork
        commission_result = s.exec(
            select(func.coalesce(func.sum(FinanceRecord.amount), 0.0)).where(
                FinanceRecord.type == "expense",
                FinanceRecord.category == "kwork_commission",
                FinanceRecord.date >= cutoff,
            )
        ).one()
        total_commission = float(commission_result)

        # Чистая прибыль (доход - комиссия - API*курс)
        # Примерный курс USD/RUB
        usd_to_rub = 90.0
        api_cost_rub = total_api_cost * usd_to_rub
        net_profit = total_income - total_commission - api_cost_rub

        # Всего расходов за всё время
        all_api = s.exec(
            select(func.coalesce(func.sum(FinanceRecord.amount), 0.0)).where(
                FinanceRecord.type == "expense",
                FinanceRecord.category == "api_cost",
            )
        ).one()

        all_income = s.exec(
            select(func.coalesce(func.sum(FinanceRecord.amount), 0.0)).where(
                FinanceRecord.type == "income",
            )
        ).one()

        return {
            "period_days": days,
            "total_income": round(total_income, 2),
            "total_api_cost": round(total_api_cost, 4),
            "total_api_cost_rub": round(api_cost_rub, 2),
            "total_commission": round(total_commission, 2),
            "net_profit": round(net_profit, 2),
            "all_time_api_cost": round(float(all_api), 4),
            "all_time_income": round(float(all_income), 2),
        }

    finally:
        if not session:
            s.close()


def update_daily_stats(
    orders_scanned: int = 0,
    orders_analyzed: int = 0,
    responses_sent: int = 0,
    orders_won: int = 0,
    revenue: float = 0.0,
    api_cost: float = 0.0,
    tokens_used: int = 0,
    session: Optional[Session] = None,
) -> None:
    """Обновить ежедневную статистику (добавить к текущему дню)."""
    s = session or get_session()
    today = datetime.utcnow().strftime("%Y-%m-%d")

    stats = s.exec(select(DailyStats).where(DailyStats.date == today)).first()
    if not stats:
        stats = DailyStats(date=today)
        s.add(stats)

    stats.orders_scanned += orders_scanned
    stats.orders_analyzed += orders_analyzed
    stats.responses_sent += responses_sent
    stats.orders_won += orders_won
    stats.revenue += revenue
    stats.api_cost += api_cost
    stats.tokens_used += tokens_used

    s.commit()
    if not session:
        s.close()
