"""Обёртка над Anthropic SDK для работы с Claude API."""

from typing import Optional

import anthropic
from loguru import logger

from src.config import settings


class ClaudeClient:
    """Клиент для взаимодействия с Claude API."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._total_input_tokens = 0
        self._total_output_tokens = 0

    async def ask(
        self,
        prompt: str,
        system: str = "",
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        """Отправить запрос к Claude и получить текстовый ответ."""
        model = model or settings.writer_model

        messages = [{"role": "user", "content": prompt}]

        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=messages,
                temperature=temperature,
            )

            # Считаем токены для статистики расходов
            self._total_input_tokens += response.usage.input_tokens
            self._total_output_tokens += response.usage.output_tokens

            logger.debug(
                f"Claude API: {response.usage.input_tokens} in, "
                f"{response.usage.output_tokens} out, model={model}"
            )

            return response.content[0].text

        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            raise

    async def ask_structured(
        self,
        prompt: str,
        response_model: type,
        system: str = "",
        model: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> dict:
        """Отправить запрос и получить структурированный JSON-ответ.

        Используем tool_use для гарантированного JSON.
        """
        model = model or settings.analyzer_model

        # Создаём инструмент из Pydantic-модели
        tool_schema = response_model.model_json_schema()
        tool = {
            "name": "structured_response",
            "description": "Return structured data",
            "input_schema": tool_schema,
        }

        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}],
                tools=[tool],
                tool_choice={"type": "tool", "name": "structured_response"},
            )

            self._total_input_tokens += response.usage.input_tokens
            self._total_output_tokens += response.usage.output_tokens

            # Извлекаем данные из tool_use
            for block in response.content:
                if block.type == "tool_use":
                    return block.input

            raise ValueError("No structured response in Claude output")

        except anthropic.APIError as e:
            logger.error(f"Claude API structured error: {e}")
            raise


    def reset_counters(self):
        """Сбросить счётчики токенов."""
        self._total_input_tokens = 0
        self._total_output_tokens = 0

    @property
    def total_tokens(self) -> dict:
        """Общее количество использованных токенов."""
        return {
            "input": self._total_input_tokens,
            "output": self._total_output_tokens,
        }

    @property
    def estimated_cost_usd(self) -> float:
        """Примерная стоимость в USD (на основе цен Sonnet)."""
        # Haiku 4.5 pricing
        input_cost = self._total_input_tokens / 1_000_000 * 0.8
        output_cost = self._total_output_tokens / 1_000_000 * 4.0
        return round(input_cost + output_cost, 4)


# Синглтон клиента
claude_client = ClaudeClient()
