"""CLI-интерфейс AI Freelancer System."""

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
    console.print("[yellow]Сканер заказов будет доступен в Этапе 2[/yellow]")


@app.command()
def analyze():
    """Проанализировать новые заказы."""
    console.print("[yellow]Анализатор будет доступен в Этапе 3[/yellow]")


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
