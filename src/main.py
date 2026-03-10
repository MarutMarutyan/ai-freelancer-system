"""CLI-интерфейс AI Freelancer System."""

import asyncio

import typer
from rich.console import Console
from rich.table import Table

from src.config import settings
from src.database.db import init_db

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
    console.print(f"[yellow]Генератор откликов будет доступен в Этапе 4 (заказ #{order_id})[/yellow]")


@app.command()
def execute(order_id: int):
    """Выполнить заказ."""
    console.print(f"[yellow]Исполнитель будет доступен в Этапе 6 (заказ #{order_id})[/yellow]")


@app.command()
def bot():
    """Запустить Telegram-бота."""
    console.print("[yellow]Telegram-бот будет доступен в Этапе 5[/yellow]")


if __name__ == "__main__":
    app()
