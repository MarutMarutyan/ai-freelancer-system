# AI Freelancer System

## О проекте
AI-система для заработка на фриланс-площадках (Kwork) с помощью Claude AI.
Система находит заказы, оценивает их, пишет отклики и помогает выполнять работу.

## Стек
- Python 3.11+, anthropic SDK, httpx, beautifulsoup4
- SQLite через sqlmodel, pydantic v2
- CLI: typer + rich
- Telegram: aiogram 3.x
- Логи: loguru

## Структура
- `src/agents/` — AI-агенты (scanner, analyzer, response_writer, executor, qa, strategy)
- `src/kwork/` — парсер и модели Kwork
- `src/claude_api/` — обёртка над Claude API, промпты, схемы
- `src/database/` — SQLite модели и запросы
- `src/bot/` — Telegram-бот
- `src/utils/` — логгер, rate limiter, финансы
- `templates/` — шаблоны откликов и описаний кворков

## Правила
- Коммиты на русском языке
- НЕ коммитить .env файлы
- Все промпты хранить в `src/claude_api/prompts.py`
- Для анализа использовать Haiku (дешевле), для генерации — Sonnet
- Rate limiting: Kwork — 1 запрос/10 сек, Claude API — 0.5 сек между запросами

## Запуск
```bash
pip install -e .
python -m src.main --help
```

## Команды CLI
- `freelancer status` — статус системы
- `freelancer scan` — сканировать заказы
- `freelancer analyze` — анализировать заказы
- `freelancer pitch <id>` — подготовить отклик
- `freelancer execute <id>` — выполнить заказ
- `freelancer finance` — финансовая сводка
- `freelancer strategy` — рекомендации AI-стратега
- `freelancer income <id> <сумма>` — записать доход от заказа
- `freelancer bot` — запустить Telegram-бота

## Telegram-бот команды
- `/start` — главное меню с кнопками
- `/scan` — сканировать заказы
- `/analyze` — анализировать новые
- `/orders` — лучшие заказы
- `/pitch <id>` — сгенерировать отклик
- `/execute <id>` — выполнить заказ
- `/finance` — финансовая сводка
- `/income <id> <сумма>` — записать доход
- `/strategy` — рекомендации AI
- `/status` — статус системы
