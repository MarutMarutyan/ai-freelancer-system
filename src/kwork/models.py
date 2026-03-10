"""Pydantic-модели для данных с Kwork."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class KworkUser(BaseModel):
    """Информация о заказчике."""

    user_id: int = Field(alias="USERID", default=0)
    username: str = ""
    wants_count: int = 0  # сколько заказов размещал
    wants_hired_percent: int = 0  # % заказов с наймом

    class Config:
        populate_by_name = True


class KworkProject(BaseModel):
    """Заказ (проект) с биржи Kwork."""

    id: int
    name: str
    description: str = ""
    category_id: str = ""
    price_limit: float = 0  # максимальный бюджет
    possible_price_limit: float = 0  # возможный бюджет (до 3x)
    views_dirty: int = 0  # количество откликов
    date_create: Optional[str] = None
    date_expire: Optional[str] = None
    time_left: str = ""
    max_days: Optional[str] = None
    user: Optional[KworkUser] = None

    @property
    def url(self) -> str:
        return f"https://kwork.ru/projects/{self.id}"

    @property
    def budget_display(self) -> str:
        if self.price_limit > 0:
            return f"до {int(self.price_limit)} руб."
        return "не указан"

    @property
    def client_name(self) -> str:
        return self.user.username if self.user else ""

    @property
    def client_orders_count(self) -> int:
        return self.user.wants_count if self.user else 0

    @property
    def client_hire_rate(self) -> int:
        return self.user.wants_hired_percent if self.user else 0
