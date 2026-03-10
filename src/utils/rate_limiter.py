"""Rate limiter для запросов к Kwork и Claude API."""

import asyncio
import random
import time

from loguru import logger


class RateLimiter:
    """Ограничитель частоты запросов с случайной задержкой."""

    def __init__(self, min_delay: float, max_delay: float | None = None):
        """
        Args:
            min_delay: Минимальная задержка между запросами (секунды)
            max_delay: Максимальная задержка (если None, = min_delay * 1.5)
        """
        self.min_delay = min_delay
        self.max_delay = max_delay or min_delay * 1.5
        self._last_request_time = 0.0

    async def wait(self):
        """Дождаться пока можно делать следующий запрос."""
        now = time.time()
        elapsed = now - self._last_request_time
        delay = random.uniform(self.min_delay, self.max_delay)

        if elapsed < delay:
            wait_time = delay - elapsed
            logger.debug(f"Rate limiter: ждём {wait_time:.1f} сек")
            await asyncio.sleep(wait_time)

        self._last_request_time = time.time()


# Лимитер для Kwork (1 запрос / 10 сек с рандомом)
kwork_limiter = RateLimiter(min_delay=10.0, max_delay=15.0)

# Лимитер для Claude API (без жёстких ограничений, но с небольшой паузой)
claude_limiter = RateLimiter(min_delay=0.5, max_delay=1.0)
