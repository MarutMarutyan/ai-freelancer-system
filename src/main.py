"""CLI-интерфейс AI Freelancer System."""

import asyncio

import typer
from rich.console import Console
from rich.table import Table

from src.config import settings
from src.database.db import init_db


def safe_text(text: str) -> str:
    """Заменить юникод-символы на ASCII для совместимости с cp1251."""
    replacements = {
        "\u2192": "->",  # →
        "\u2190": "<-",  # ←
        "\u2014": "--",  # —
        "\u2013": "-",   # –
        "\u2018": "'",   # '
        "\u2019": "'",   # '
        "\u201c": '"',   # "
        "\u201d": '"',   # "
        "\u2022": "-",   # •
        "\u2026": "...", # …
        "\u2713": "+",   # ✓
        "\u2717": "x",   # ✗
        "\u00ab": "<<",  # «
        "\u00bb": ">>",  # »
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    # Убираем оставшиеся непечатаемые символы
    return text.encode("cp1251", errors="replace").decode("cp1251")


app = typer.Typer(
    name="freelancer",
    help="AI Freelancer System — заработок на фрилансе с помощью Claude",
)
console = Console()


@app.callback()
def startup():
    """Инициализация при запуске."""
    init_db()


@app.command()
def status():
    """Показать статус системы."""
    table = Table(title="AI Freelancer System — Статус")
    table.add_column("Параметр", style="cyan")
    table.add_column("Значение", style="green")

    table.add_row("Claude API", "[green]OK[/green]" if settings.anthropic_api_key else "[red]Нет[/red]")
    table.add_row("Telegram Bot", "[green]OK[/green]" if settings.telegram_bot_token else "[red]Нет[/red]")
    table.add_row("Модель (анализ)", settings.analyzer_model)
    table.add_row("Модель (генерация)", settings.writer_model)
    table.add_row("Интервал сканирования", f"{settings.scan_interval_minutes} мин")
    table.add_row("Порог оценки", f"{settings.min_score_threshold}")

    console.print(table)


@app.command()
def scan():
    """Сканировать новые заказы на Kwork."""
    from src.kwork.categories import ACTIVE_CATEGORIES, get_category_name
    from src.kwork.parser import scan_new_projects

    cats = ACTIVE_CATEGORIES
    cat_names = [get_category_name(c) for c in cats]
    console.print(f"[cyan]Сканирую категории:[/cyan] {', '.join(cat_names)}")

    new_orders = asyncio.run(scan_new_projects(cats))

    if not new_orders:
        console.print("[yellow]Новых заказов не найдено[/yellow]")
        return

    table = Table(title=f"Найдено новых заказов: {len(new_orders)}")
    table.add_column("#", style="dim", width=4)
    table.add_column("Заказ", style="cyan", max_width=50)
    table.add_column("Бюджет", style="green", width=15)
    table.add_column("Категория", style="yellow", width=20)
    table.add_column("Откликов", style="magenta", width=10)

    for i, order in enumerate(new_orders, 1):
        budget = f"до {order.budget_max} руб." if order.budget_max else "не указан"
        table.add_row(
            str(i),
            order.title[:50],
            budget,
            order.category,
            str(order.responses_count),
        )

    console.print(table)


@app.command()
def analyze(
    limit: int = typer.Option(0, "--limit", "-l", help="Макс. заказов для анализа (0 = все)"),
):
    """Проанализировать новые заказы через Claude AI."""
    from src.agents.analyzer import analyzer_agent
    from src.config import settings as cfg

    if not cfg.anthropic_api_key:
        console.print("[red]ANTHROPIC_API_KEY не настроен! Добавь ключ в .env файл[/red]")
        return

    console.print("[cyan]Анализирую новые заказы через Claude API...[/cyan]")
    results = asyncio.run(analyzer_agent.run(limit=limit))

    if not results:
        console.print("[yellow]Нет заказов для анализа (запусти scan сначала)[/yellow]")
        return

    table = Table(title=f"Результаты анализа: {len(results)} заказов")
    table.add_column("#", style="dim", width=4)
    table.add_column("Заказ", style="cyan", max_width=40)
    table.add_column("Оценка", width=8)
    table.add_column("Рекомендация", width=14)
    table.add_column("Тип", style="yellow", width=12)
    table.add_column("Цена", style="green", width=10)
    table.add_column("Время", width=10)

    for i, r in enumerate(results, 1):
        score = r["score"]
        if score >= 70:
            score_style = f"[green]{score}[/green]"
        elif score >= 50:
            score_style = f"[yellow]{score}[/yellow]"
        else:
            score_style = f"[red]{score}[/red]"

        rec = r["recommendation"]
        rec_style = f"[green]{rec}[/green]" if rec == "respond" else f"[dim]{rec}[/dim]"

        table.add_row(
            str(i),
            r["title"][:40],
            score_style,
            rec_style,
            r["work_type"],
            f"{r['suggested_price']} r",
            r["estimated_time"],
        )

    console.print(table)

    # Показать лучшие заказы
    good = [r for r in results if r["score"] >= cfg.min_score_threshold]
    if good:
        console.print(f"\n[green]Подходящих заказов (>={cfg.min_score_threshold}): {len(good)}[/green]")
        for r in good:
            console.print(f"  [cyan]#{r['order_id']}[/cyan] {r['title'][:50]}")
            console.print(f"    {r['reasoning']}")
    else:
        console.print(f"\n[yellow]Подходящих заказов (>={cfg.min_score_threshold}) не найдено[/yellow]")

    console.print(f"\n[dim]API стоимость: ~${analyzer_agent.claude.estimated_cost_usd}[/dim]")


@app.command()
def pitch(order_id: int):
    """Подготовить отклик на заказ."""
    from src.agents.response_writer import response_writer
    from src.config import settings as cfg

    if not cfg.anthropic_api_key:
        console.print("[red]ANTHROPIC_API_KEY не настроен! Добавь ключ в .env файл[/red]")
        return

    console.print(f"[cyan]Генерирую отклик для заказа #{order_id}...[/cyan]")
    result = asyncio.run(response_writer.run(order_id))

    if not result:
        console.print("[red]Не удалось сгенерировать отклик. Проверь что заказ существует и проанализирован.[/red]")
        return

    # Заголовок
    console.print(f"\n[bold green]Отклик на заказ:[/bold green] {result['order_title']}")
    console.print(f"[dim]Цена: {result['proposed_price']} руб. | Срок: {result['proposed_deadline']}[/dim]\n")

    # Текст отклика
    console.print("[bold cyan]--- ТЕКСТ ОТКЛИКА ---[/bold cyan]")
    console.print(safe_text(result["pitch_text"]))
    console.print("[bold cyan]--- КОНЕЦ ОТКЛИКА ---[/bold cyan]\n")

    # Ключевые аргументы
    if result["key_points"]:
        console.print("[yellow]Ключевые аргументы:[/yellow]")
        for point in result["key_points"]:
            console.print(f"  - {safe_text(point)}")

    # Мини-демо
    if result.get("mini_demo"):
        console.print(f"\n[yellow]Мини-демо:[/yellow]")
        console.print(safe_text(result["mini_demo"]))

    console.print(f"\n[dim]Отклик сохранён как черновик (ID={result['response_id']})[/dim]")
    console.print("[dim]Скопируй текст и отправь на Kwork вручную[/dim]")
    console.print(f"[dim]API стоимость: ~${response_writer.claude.estimated_cost_usd}[/dim]")


@app.command()
def execute(order_id: int):
    """Выполнить заказ."""
    console.print(f"[yellow]Исполнитель будет доступен в Этапе 6 (заказ #{order_id})[/yellow]")


@app.command()
def bot():
    """Запустить Telegram-бота."""
    if not settings.telegram_bot_token:
        console.print("[red]TELEGRAM_BOT_TOKEN не настроен![/red]")
        console.print("1. Открой @BotFather в Telegram")
        console.print("2. Отправь /newbot и следуй инструкции")
        console.print("3. Скопируй токен в .env файл: TELEGRAM_BOT_TOKEN=...")
        console.print("4. Добавь свой Telegram ID: TELEGRAM_ADMIN_ID=...")
        console.print("   (узнай ID через @userinfobot)")
        return

    from src.bot.bot import start_bot
    console.print("[green]Запускаю Telegram-бота...[/green]")
    console.print("[dim]Нажми Ctrl+C для остановки[/dim]")
    asyncio.run(start_bot())


if __name__ == "__main__":
    app()
