"""SQLModel-модели для базы данных."""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Order(SQLModel, table=True):
    """Заказы с Kwork."""

    __tablename__ = "orders"

    id: Optional[int] = Field(default=None, primary_key=True)
    kwork_id: str = Field(unique=True, index=True)
    title: str
    description: str
    category: str = ""
    budget_min: Optional[int] = None
    budget_max: Optional[int] = None
    deadline: Optional[str] = None
    client_name: Optional[str] = None
    client_reviews_count: int = 0
    responses_count: int = 0
    url: str
    status: str = Field(default="new", index=True)  # new/analyzed/responded/won/rejected/skipped
    score: Optional[int] = None  # 0-100
    analysis: Optional[str] = None  # JSON с детальным анализом
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Response(SQLModel, table=True):
    """Отклики на заказы."""

    __tablename__ = "responses"

    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id", index=True)
    draft_text: str
    final_text: Optional[str] = None
    proposed_price: Optional[int] = None
    proposed_deadline: Optional[str] = None
    status: str = Field(default="draft")  # draft/approved/sent/won/lost
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Execution(SQLModel, table=True):
    """Выполненные работы."""

    __tablename__ = "executions"

    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id", index=True)
    task_description: str
    result_text: Optional[str] = None
    result_files: Optional[str] = None  # JSON массив путей
    qa_checklist: Optional[str] = None  # JSON чек-лист от QA
    qa_passed: bool = False
    qa_iterations: int = 0
    status: str = Field(default="in_progress")  # in_progress/review/delivered/completed
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Kwork(SQLModel, table=True):
    """Созданные кворки (услуги в магазине)."""

    __tablename__ = "kworks"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    category: str
    price: int
    delivery_days: int
    status: str = Field(default="draft")  # draft/active/paused
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FinanceRecord(SQLModel, table=True):
    """Финансовые записи — доходы и расходы."""

    __tablename__ = "finance"

    id: Optional[int] = Field(default=None, primary_key=True)
    date: str  # YYYY-MM-DD
    type: str  # income/expense
    category: str  # order/api_cost/kwork_commission
    amount: float
    description: Optional[str] = None
    order_id: Optional[int] = Field(default=None, foreign_key="orders.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DailyStats(SQLModel, table=True):
    """Ежедневная статистика."""

    __tablename__ = "daily_stats"

    id: Optional[int] = Field(default=None, primary_key=True)
    date: str = Field(unique=True)  # YYYY-MM-DD
    orders_scanned: int = 0
    orders_analyzed: int = 0
    responses_sent: int = 0
    orders_won: int = 0
    revenue: float = 0.0
    api_cost: float = 0.0
    tokens_used: int = 0
