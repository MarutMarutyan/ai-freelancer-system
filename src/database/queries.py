"""Частые запросы к базе данных."""

from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from src.database.db import get_session
from src.database.models import DailyStats, Execution, FinanceRecord, Order, Response


def get_new_orders(session: Optional[Session] = None) -> list[Order]:
    """Получить все новые (непроанализированные) заказы."""
    s = session or get_session()
    statement = select(Order).where(Order.status == "new")
    results = s.exec(statement).all()
    if not session:
        s.close()
    return list(results)


def get_analyzed_orders(
    session: Optional[Session] = None, min_score: int = 0
) -> list[Order]:
    """Получить проанализированные заказы с оценкой выше порога."""
    s = session or get_session()
    statement = (
        select(Order)
        .where(Order.status == "analyzed")
        .where(Order.score >= min_score)
        .order_by(Order.score.desc())
    )
    results = s.exec(statement).all()
    if not session:
        s.close()
    return list(results)


def get_order_by_id(order_id: int, session: Optional[Session] = None) -> Optional[Order]:
    """Получить заказ по ID."""
    s = session or get_session()
    order = s.get(Order, order_id)
    if not session:
        s.close()
    return order


def order_exists(kwork_id: str, session: Optional[Session] = None) -> bool:
    """Проверить существует ли заказ с таким kwork_id (дедупликация)."""
    s = session or get_session()
    statement = select(Order).where(Order.kwork_id == kwork_id)
    result = s.exec(statement).first()
    if not session:
        s.close()
    return result is not None


def save_order(order: Order, session: Optional[Session] = None) -> Order:
    """Сохранить заказ в БД."""
    s = session or get_session()
    s.add(order)
    s.commit()
    s.refresh(order)
    if not session:
        s.close()
    return order


def update_order_analysis(
    order_id: int, score: int, analysis: str, session: Optional[Session] = None
) -> None:
    """Обновить анализ заказа."""
    s = session or get_session()
    order = s.get(Order, order_id)
    if order:
        order.score = score
        order.analysis = analysis
        order.status = "analyzed"
        order.updated_at = datetime.utcnow()
        s.add(order)
        s.commit()
    if not session:
        s.close()


def save_response(response: Response, session: Optional[Session] = None) -> Response:
    """Сохранить отклик."""
    s = session or get_session()
    s.add(response)
    s.commit()
    s.refresh(response)
    if not session:
        s.close()
    return response


def save_finance_record(record: FinanceRecord, session: Optional[Session] = None) -> None:
    """Сохранить финансовую запись."""
    s = session or get_session()
    s.add(record)
    s.commit()
    if not session:
        s.close()


def get_today_stats(session: Optional[Session] = None) -> Optional[DailyStats]:
    """Получить статистику за сегодня."""
    s = session or get_session()
    today = datetime.utcnow().strftime("%Y-%m-%d")
    statement = select(DailyStats).where(DailyStats.date == today)
    result = s.exec(statement).first()
    if not session:
        s.close()
    return result
