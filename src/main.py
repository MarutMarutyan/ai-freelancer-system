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
    """Выполнить заказ с проверкой качества."""
    from src.agents.orchestrator import execute_with_qa
    from src.config import settings as cfg

    if not cfg.anthropic_api_key:
        console.print("[red]ANTHROPIC_API_KEY не настроен![/red]")
        return

    console.print(f"[cyan]Выполняю заказ #{order_id} (Executor + QA)...[/cyan]")
    console.print("[dim]Это может занять 1-3 минуты[/dim]\n")

    result = asyncio.run(execute_with_qa(order_id))

    if not result:
        console.print("[red]Не удалось выполнить заказ.[/red]")
        return

    # QA статус
    if result["qa_passed"]:
        console.print(f"[bold green]QA ПРОЙДЕН[/bold green] (итераций: {result['qa_iterations']})")
    else:
        console.print(f"[bold red]QA НЕ ПРОЙДЕН[/bold red] (итераций: {result['qa_iterations']})")

    # Чек-лист
    if result["qa_checklist"]:
        console.print("\n[yellow]Чек-лист QA:[/yellow]")
        for item in result["qa_checklist"]:
            console.print(f"  {safe_text(item)}")

    if result["qa_issues"]:
        console.print("\n[red]Проблемы:[/red]")
        for issue in result["qa_issues"]:
            console.print(f"  - {safe_text(issue)}")

    if result["qa_comment"]:
        console.print(f"\n[dim]QA: {safe_text(result['qa_comment'])}[/dim]")

    # Результат работы
    console.print(f"\n[bold cyan]--- РЕЗУЛЬТАТ РАБОТЫ ---[/bold cyan]")
    text = result["result_text"]
    if len(text) > 3000:
        console.print(safe_text(text[:3000]))
        console.print(f"\n[dim]...(обрезано, полный текст {len(text)} символов)[/dim]")
    else:
        console.print(safe_text(text))
    console.print(f"[bold cyan]--- КОНЕЦ ---[/bold cyan]")

    console.print(f"\n[dim]Сохранено (execution ID={result['execution_id']})[/dim]")
    console.print(f"[dim]API стоимость: ~${result['api_cost']}[/dim]")


@app.command()
def finance(days: int = typer.Option(30, "--days", "-d", help="За сколько дней показать")):
    """Показать финансовую сводку."""
    from src.utils.finance import get_finance_summary

    summary = get_finance_summary(days=days)

    table = Table(title=f"Финансы за {days} дней")
    table.add_column("Показатель", style="cyan")
    table.add_column("Значение", style="green")

    table.add_row("Доход", f"{summary['total_income']} руб.")
    table.add_row("Расходы API", f"${summary['total_api_cost']}")
    table.add_row("Расходы API (руб.)", f"{summary['total_api_cost_rub']} руб.")
    table.add_row("Комиссия Kwork", f"{summary['total_commission']} руб.")
    table.add_row("Чистая прибыль", f"{summary['net_profit']} руб.")
    table.add_row("---", "---")
    table.add_row("API за все время", f"${summary['all_time_api_cost']}")
    table.add_row("Доход за все время", f"{summary['all_time_income']} руб.")

    console.print(table)


@app.command()
def strategy():
    """Получить стратегические рекомендации от AI."""
    from src.agents.strategy import strategy_agent
    from src.config import settings as cfg

    if not cfg.anthropic_api_key:
        console.print("[red]ANTHROPIC_API_KEY не настроен![/red]")
        return

    console.print("[cyan]Анализирую статистику и готовлю рекомендации...[/cyan]")
    result = asyncio.run(strategy_agent.run())

    if not result:
        console.print("[red]Не удалось получить рекомендации.[/red]")
        return

    # Профиль
    console.print("\n[bold green]Профиль:[/bold green]")
    for tip in result["profile_tips"]:
        console.print(f"  - {safe_text(tip)}")

    # Ценообразование
    console.print("\n[bold yellow]Ценообразование:[/bold yellow]")
    for tip in result["pricing_tips"]:
        console.print(f"  - {safe_text(tip)}")

    # Фокус на категориях
    console.print("\n[bold cyan]Категории для фокуса:[/bold cyan]")
    for cat in result["category_focus"]:
        console.print(f"  - {safe_text(cat)}")

    # Следующие шаги
    console.print("\n[bold magenta]Следующие шаги:[/bold magenta]")
    for i, step in enumerate(result["next_steps"], 1):
        console.print(f"  {i}. {safe_text(step)}")

    console.print(f"\n[dim]API стоимость: ~${result['api_cost']}[/dim]")


@app.command()
def income(
    order_id: int = typer.Argument(help="ID заказа"),
    amount: float = typer.Argument(help="Сумма в рублях"),
):
    """Записать доход от выполненного заказа."""
    from src.utils.finance import record_income

    record_income(amount, order_id)
    commission = amount * 0.20
    net = amount - commission
    console.print(f"[green]Записан доход: {amount} руб.[/green]")
    console.print(f"[yellow]Комиссия Kwork (20%): {commission} руб.[/yellow]")
    console.print(f"[green]Чистый доход: {net} руб.[/green]")


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
