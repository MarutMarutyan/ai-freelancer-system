"""Pydantic-схемы для structured output от Claude API."""

import re

from pydantic import BaseModel, Field, field_validator


class OrderAnalysis(BaseModel):
    """Результат анализа заказа."""

    score: int = Field(ge=0, le=100, description="Общая оценка заказа 0-100")
    feasibility: int = Field(ge=0, le=25, description="Выполнимость через AI (0-25)")
    value: int = Field(ge=0, le=25, description="Соотношение бюджет/время (0-25)")
    competition: int = Field(ge=0, le=25, description="Конкуренция (0-25)")
    reliability: int = Field(ge=0, le=25, description="Надёжность клиента (0-25)")
    recommendation: str = Field(description="respond (откликаться) или skip (пропустить)")
    reasoning: str = Field(description="Краткое обоснование оценки на русском")
    suggested_price: int = Field(description="Рекомендуемая цена в рублях (одно число)")
    estimated_time: str = Field(description="Примерное время выполнения")
    work_type: str = Field(description="Тип работы: text/code/translation/other")

    @field_validator("suggested_price", mode="before")
    @classmethod
    def parse_price(cls, v):
        """Извлечь число из строки вроде '8000-12000 руб.' -> 8000."""
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            numbers = re.findall(r"\d+", v)
            return int(numbers[0]) if numbers else 0
        return 0


class QAResult(BaseModel):
    """Результат проверки качества."""

    passed: bool = Field(description="Прошла ли работа проверку")
    checklist: list[dict] = Field(
        description="Чек-лист: [{item: str, passed: bool, comment: str}]"
    )
    issues: list[str] = Field(default=[], description="Список проблем если есть")
    overall_comment: str = Field(description="Общий комментарий")


class StrategyAdvice(BaseModel):
    """Рекомендации по стратегии."""

    profile_tips: list[str] = Field(description="Советы по улучшению профиля")
    pricing_tips: list[str] = Field(description="Советы по ценообразованию")
    category_focus: list[str] = Field(description="На каких категориях фокусироваться")
    next_steps: list[str] = Field(description="Конкретные следующие шаги")
