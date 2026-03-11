# AI Freelancer System

AI-система для автоматизации работы на фриланс-площадке [Kwork](https://kwork.ru) с помощью Claude AI.

Система находит заказы, оценивает их качество, генерирует персональные отклики и помогает выполнять работу — всё через CLI или Telegram-бот.

---

## Возможности

- **Сканирование заказов** — автоматически находит новые заказы на Kwork по выбранным категориям
- **AI-анализ** — оценивает каждый заказ по шкале 0–100 (Haiku — быстро и дёшево)
- **Генерация откликов** — пишет персональный отклик под конкретный заказ (Sonnet)
- **Выполнение заказа** — помогает выполнить работу с проверкой качества (QA-цикл)
- **AI-стратег** — анализирует историю и даёт рекомендации по заработку
- **Финансы** — учёт доходов, расходов на API, комиссий Kwork
- **Telegram-бот** — всё то же самое через телефон

---

## Стек

| Компонент | Технология |
|-----------|-----------|
| Язык | Python 3.11+ |
| AI | Anthropic Claude API (Haiku + Sonnet) |
| База данных | SQLite через SQLModel |
| CLI | Typer + Rich |
| Telegram | aiogram 3.x |
| HTTP | httpx |
| Парсинг | beautifulsoup4 |
| Логи | loguru |

---

## Установка

### 1. Клонировать репозиторий

```bash
git clone https://github.com/YOUR_USERNAME/ai-freelancer-system.git
cd ai-freelancer-system
```

### 2. Создать виртуальное окружение

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Установить зависимости

```bash
pip install -e .
```

### 4. Настроить переменные окружения

```bash
cp .env.example .env
```

Открой `.env` и заполни:

```env
ANTHROPIC_API_KEY=sk-ant-xxx        # Ключ с console.anthropic.com
TELEGRAM_BOT_TOKEN=123456:ABC-DEF   # От @BotFather в Telegram
TELEGRAM_ADMIN_ID=123456789         # Твой Telegram ID (от @userinfobot)
```

---

## Запуск

```bash
# Проверить статус системы
freelancer status

# Сканировать новые заказы на Kwork
freelancer scan

# Анализировать заказы с помощью AI
freelancer analyze

# Посмотреть лучшие заказы
freelancer analyze --top 10

# Подготовить отклик на заказ
freelancer pitch 12345

# Выполнить заказ с AI-помощью
freelancer execute 12345

# Записать полученный доход
freelancer income 12345 1500

# Финансовая сводка
freelancer finance

# Рекомендации AI-стратега
freelancer strategy

# Запустить Telegram-бота
freelancer bot
```

---

## Telegram-бот

После запуска `freelancer bot` бот доступен в Telegram:

| Команда | Действие |
|---------|---------|
| `/start` | Главное меню с кнопками |
| `/scan` | Сканировать заказы |
| `/analyze` | Анализировать новые заказы |
| `/orders` | Лучшие заказы |
| `/pitch <id>` | Сгенерировать отклик |
| `/execute <id>` | Выполнить заказ |
| `/finance` | Финансовая сводка |
| `/income <id> <сумма>` | Записать доход |
| `/strategy` | Рекомендации AI |
| `/status` | Статус системы |

---

## Структура проекта

```
ai-freelancer-system/
├── src/
│   ├── agents/          # AI-агенты (analyzer, writer, executor, qa, strategy)
│   ├── bot/             # Telegram-бот (aiogram 3.x)
│   ├── claude_api/      # Обёртка над Claude API, промпты, схемы
│   ├── database/        # SQLite модели и запросы
│   ├── kwork/           # Парсер Kwork
│   ├── utils/           # Логгер, rate limiter, финансы
│   ├── config.py        # Настройки через pydantic-settings
│   └── main.py          # CLI (typer)
├── templates/           # Шаблоны откликов и описаний кворков
├── tests/               # Тесты
├── .env.example         # Шаблон переменных окружения
└── pyproject.toml       # Зависимости
```

---

## Как работает AI-анализ

1. **Сканер** парсит Kwork и сохраняет заказы в SQLite
2. **Анализатор** (Claude Haiku) оценивает каждый заказ: реалистичность цены, сложность, конкуренцию
3. Заказы с оценкой > 50 считаются перспективными
4. **Генератор откликов** (Claude Sonnet) пишет персональный текст под конкретный заказ
5. **QA-агент** проверяет результат работы (до 3 итераций)

---

## Получение API ключей

- **Anthropic API Key**: [console.anthropic.com](https://console.anthropic.com) → API Keys
- **Telegram Bot Token**: напиши [@BotFather](https://t.me/BotFather) в Telegram → `/newbot`
- **Telegram Admin ID**: напиши [@userinfobot](https://t.me/userinfobot) → скопируй ID

---

## Лицензия

MIT License — используй свободно.
