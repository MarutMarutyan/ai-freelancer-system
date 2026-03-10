"""Обработчики команд Telegram-бота."""

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from loguru import logger

from src.config import settings

router = Router()


def admin_only(func):
    """Декоратор: только админ может использовать бота."""
    async def wrapper(message: Message, **kwargs):
        if settings.telegram_admin_id and message.from_user.id != settings.telegram_admin_id:
            await message.answer("Доступ запрещён.")
            return
        return await func(message)
    wrapper.__name__ = func.__name__
    return wrapper


def main_menu_kb() -> InlineKeyboardMarkup:
    """Главное меню с кнопками."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Сканировать", callback_data="scan"),
            InlineKeyboardButton(text="Анализировать", callback_data="analyze"),
        ],
        [
            InlineKeyboardButton(text="Лучшие заказы", callback_data="orders"),
            InlineKeyboardButton(text="Статус", callback_data="status"),
        ],
    ])


@router.message(CommandStart())
@admin_only
async def cmd_start(message: Message):
    """Команда /start."""
    await message.answer(
        "AI Freelancer System\n\n"
        "Команды:\n"
        "/scan - Сканировать заказы\n"
        "/analyze - Анализировать новые\n"
        "/orders - Лучшие заказы\n"
        "/pitch <id> - Сгенерировать отклик\n"
        "/status - Статус системы\n\n"
        "Или используй кнопки:",
        reply_markup=main_menu_kb(),
    )


@router.message(Command("scan"))
@admin_only
async def cmd_scan(message: Message):
    """Сканировать новые заказы."""
    await message.answer("Сканирую заказы на Kwork...")

    from src.kwork.categories import ACTIVE_CATEGORIES
    from src.kwork.parser import scan_new_projects

    try:
        new_orders = await scan_new_projects(ACTIVE_CATEGORIES)

        if not new_orders:
            await message.answer("Новых заказов не найдено.")
            return

        text = f"Найдено {len(new_orders)} новых заказов:\n\n"
        for i, order in enumerate(new_orders[:10], 1):
            budget = f"до {order.budget_max} р." if order.budget_max else "?"
            text += f"{i}. {order.title[:50]}\n   Бюджет: {budget}\n\n"

        if len(new_orders) > 10:
            text += f"...и ещё {len(new_orders) - 10}\n"

        text += "\nЗапусти /analyze для анализа"
        await message.answer(text)

    except Exception as e:
        logger.error(f"Ошибка сканирования: {e}")
        await message.answer(f"Ошибка: {e}")


@router.message(Command("analyze"))
@admin_only
async def cmd_analyze(message: Message):
    """Анализировать новые заказы."""
    await message.answer("Анализирую заказы через Claude AI...\nЭто может занять 1-2 минуты.")

    from src.agents.analyzer import analyzer_agent

    try:
        results = await analyzer_agent.run()

        if not results:
            await message.answer("Нет новых заказов для анализа.\nЗапусти /scan сначала.")
            return

        good = [r for r in results if r["score"] >= settings.min_score_threshold]

        text = f"Проанализировано: {len(results)} заказов\n"
        text += f"Подходящих (>={settings.min_score_threshold}): {len(good)}\n\n"

        # Показываем топ-5 по оценке
        sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)
        for r in sorted_results[:5]:
            emoji = "!" if r["score"] >= settings.min_score_threshold else " "
            text += (
                f"{emoji} #{r['order_id']} [{r['score']}] {r['title'][:40]}\n"
                f"  {r['work_type']} | {r['suggested_price']}р.\n\n"
            )

        text += f"API: ~${analyzer_agent.claude.estimated_cost_usd}\n"
        text += "Для отклика: /pitch <id>"
        await message.answer(text)

    except Exception as e:
        logger.error(f"Ошибка анализа: {e}")
        await message.answer(f"Ошибка: {e}")


@router.message(Command("orders"))
@admin_only
async def cmd_orders(message: Message):
    """Показать лучшие проанализированные заказы."""
    from src.database.db import get_session
    from src.database.queries import get_analyzed_orders

    session = get_session()
    try:
        orders = get_analyzed_orders(session, min_score=0)

        if not orders:
            await message.answer("Нет проанализированных заказов.\nЗапусти /scan и /analyze.")
            return

        text = f"Заказы (всего {len(orders)}):\n\n"
        for order in orders[:10]:
            mark = ">>>" if order.score >= settings.min_score_threshold else "   "
            budget = f"{order.budget_max}р." if order.budget_max else "?"
            text += (
                f"{mark} #{order.id} [{order.score}] {order.title[:40]}\n"
                f"    {budget} | {order.responses_count} откл.\n\n"
            )

        # Кнопки для топ-заказов
        buttons = []
        for order in orders[:5]:
            buttons.append([InlineKeyboardButton(
                text=f"Отклик на #{order.id} ({order.score}б.)",
                callback_data=f"pitch_{order.id}",
            )])

        kb = InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None
        await message.answer(text, reply_markup=kb)

    finally:
        session.close()


@router.message(Command("pitch"))
@admin_only
async def cmd_pitch(message: Message):
    """Сгенерировать отклик на заказ."""
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /pitch <id заказа>\nПример: /pitch 8")
        return

    try:
        order_id = int(parts[1])
    except ValueError:
        await message.answer("ID заказа должен быть числом.\nПример: /pitch 8")
        return

    await message.answer(f"Генерирую отклик для заказа #{order_id}...")

    from src.agents.response_writer import response_writer

    try:
        result = await response_writer.run(order_id)

        if not result:
            await message.answer(
                "Не удалось сгенерировать отклик.\n"
                "Проверь что заказ существует и проанализирован (/analyze)."
            )
            return

        # Основной текст отклика
        text = (
            f"Отклик на: {result['order_title'][:50]}\n"
            f"Цена: {result['proposed_price']} руб.\n"
            f"Срок: {result['proposed_deadline']}\n\n"
            f"--- ТЕКСТ ---\n"
            f"{result['pitch_text']}\n"
            f"--- КОНЕЦ ---\n\n"
        )

        # Ключевые аргументы
        if result["key_points"]:
            text += "Аргументы:\n"
            for p in result["key_points"]:
                text += f"- {p}\n"

        text += f"\nСохранён как черновик (ID={result['response_id']})"
        text += f"\nAPI: ~${response_writer.claude.estimated_cost_usd}"

        # Telegram лимит 4096 символов
        if len(text) > 4000:
            await message.answer(text[:4000] + "\n...(обрезано)")
        else:
            await message.answer(text)

        # Мини-демо отдельным сообщением если есть
        if result.get("mini_demo"):
            demo = f"Мини-демо:\n\n{result['mini_demo']}"
            if len(demo) > 4000:
                demo = demo[:4000] + "\n...(обрезано)"
            await message.answer(demo)

    except Exception as e:
        logger.error(f"Ошибка генерации отклика: {e}")
        await message.answer(f"Ошибка: {e}")


@router.message(Command("execute"))
@admin_only
async def cmd_execute(message: Message):
    """Выполнить заказ."""
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /execute <id заказа>\nПример: /execute 8")
        return

    try:
        order_id = int(parts[1])
    except ValueError:
        await message.answer("ID заказа должен быть числом.")
        return

    await message.answer(
        f"Выполняю заказ #{order_id} (Executor + QA)...\n"
        "Это может занять 1-3 минуты."
    )

    from src.agents.orchestrator import execute_with_qa

    try:
        result = await execute_with_qa(order_id)

        if not result:
            await message.answer("Не удалось выполнить заказ.")
            return

        qa_status = "QA ПРОЙДЕН" if result["qa_passed"] else "QA НЕ ПРОЙДЕН"
        text = (
            f"{qa_status} (итераций: {result['qa_iterations']})\n\n"
        )

        # Чек-лист
        if result["qa_checklist"]:
            text += "Чек-лист:\n"
            for item in result["qa_checklist"]:
                text += f"  {item}\n"
            text += "\n"

        if result["qa_comment"]:
            text += f"QA: {result['qa_comment']}\n\n"

        # Результат (обрезаем для Telegram)
        work = result["result_text"]
        if len(work) > 3000:
            text += f"--- РЕЗУЛЬТАТ (первые 3000 из {len(work)}) ---\n"
            text += work[:3000] + "\n...(обрезано)"
        else:
            text += f"--- РЕЗУЛЬТАТ ---\n{work}"

        text += f"\n\nID={result['execution_id']} | API: ~${result['api_cost']}"

        # Разбиваем на части если длинный
        if len(text) > 4000:
            await message.answer(text[:4000] + "\n...(обрезано)")
        else:
            await message.answer(text)

    except Exception as e:
        logger.error(f"Ошибка выполнения: {e}")
        await message.answer(f"Ошибка: {e}")


@router.message(Command("status"))
@admin_only
async def cmd_status(message: Message):
    """Статус системы."""
    from src.database.db import get_session
    from src.database.models import Order
    from sqlmodel import select, func

    session = get_session()
    try:
        total = session.exec(select(func.count(Order.id))).one()
        new = session.exec(select(func.count(Order.id)).where(Order.status == "new")).one()
        analyzed = session.exec(select(func.count(Order.id)).where(Order.status == "analyzed")).one()
        responded = session.exec(select(func.count(Order.id)).where(Order.status == "responded")).one()

        text = (
            "Статус системы:\n\n"
            f"Заказов в БД: {total}\n"
            f"  Новых: {new}\n"
            f"  Проанализировано: {analyzed}\n"
            f"  С откликом: {responded}\n\n"
            f"Claude API: {'OK' if settings.anthropic_api_key else 'Нет ключа'}\n"
            f"Модель анализа: {settings.analyzer_model}\n"
            f"Модель генерации: {settings.writer_model}\n"
            f"Порог оценки: {settings.min_score_threshold}\n"
        )
        await message.answer(text, reply_markup=main_menu_kb())

    finally:
        session.close()


# --- Обработчики кнопок ---

def _is_admin(callback: CallbackQuery) -> bool:
    """Проверить что callback от админа."""
    if settings.telegram_admin_id and callback.from_user.id != settings.telegram_admin_id:
        return False
    return True


@router.callback_query(F.data == "scan")
async def cb_scan(callback: CallbackQuery):
    """Кнопка сканирования."""
    if not _is_admin(callback):
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    await callback.answer("Сканирую...")

    from src.kwork.categories import ACTIVE_CATEGORIES
    from src.kwork.parser import scan_new_projects

    try:
        new_orders = await scan_new_projects(ACTIVE_CATEGORIES)
        if not new_orders:
            await callback.message.answer("Новых заказов не найдено.")
            return
        text = f"Найдено {len(new_orders)} новых заказов:\n\n"
        for i, order in enumerate(new_orders[:10], 1):
            budget = f"до {order.budget_max} р." if order.budget_max else "?"
            text += f"{i}. {order.title[:50]}\n   {budget}\n\n"
        text += "Запусти /analyze для анализа"
        await callback.message.answer(text)
    except Exception as e:
        await callback.message.answer(f"Ошибка: {e}")


@router.callback_query(F.data == "analyze")
async def cb_analyze(callback: CallbackQuery):
    """Кнопка анализа."""
    if not _is_admin(callback):
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    await callback.answer("Анализирую...")
    await callback.message.answer("Анализирую через Claude AI...\nЭто займёт 1-2 минуты.")

    from src.agents.analyzer import analyzer_agent

    try:
        results = await analyzer_agent.run()
        if not results:
            await callback.message.answer("Нет новых заказов.\nЗапусти /scan сначала.")
            return
        good = [r for r in results if r["score"] >= settings.min_score_threshold]
        text = f"Проанализировано: {len(results)}\nПодходящих: {len(good)}\n\n"
        for r in sorted(results, key=lambda x: x["score"], reverse=True)[:5]:
            text += f"#{r['order_id']} [{r['score']}] {r['title'][:40]}\n"
        text += f"\nAPI: ~${analyzer_agent.claude.estimated_cost_usd}"
        await callback.message.answer(text)
    except Exception as e:
        await callback.message.answer(f"Ошибка: {e}")


@router.callback_query(F.data == "orders")
async def cb_orders(callback: CallbackQuery):
    """Кнопка списка заказов."""
    if not _is_admin(callback):
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    await callback.answer()

    from src.database.db import get_session
    from src.database.queries import get_analyzed_orders

    session = get_session()
    try:
        orders = get_analyzed_orders(session, min_score=0)
        if not orders:
            await callback.message.answer("Нет проанализированных заказов.\nЗапусти /scan и /analyze.")
            return

        text = f"Заказы (всего {len(orders)}):\n\n"
        for order in orders[:10]:
            mark = ">>>" if order.score >= settings.min_score_threshold else "   "
            budget = f"{order.budget_max}р." if order.budget_max else "?"
            text += (
                f"{mark} #{order.id} [{order.score}] {order.title[:40]}\n"
                f"    {budget} | {order.responses_count} откл.\n\n"
            )

        buttons = []
        for order in orders[:5]:
            buttons.append([InlineKeyboardButton(
                text=f"Отклик на #{order.id} ({order.score}б.)",
                callback_data=f"pitch_{order.id}",
            )])
        kb = InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None
        await callback.message.answer(text, reply_markup=kb)
    finally:
        session.close()


@router.callback_query(F.data == "status")
async def cb_status(callback: CallbackQuery):
    """Кнопка статуса."""
    if not _is_admin(callback):
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    await callback.answer()

    from src.database.db import get_session
    from src.database.models import Order
    from sqlmodel import select, func

    session = get_session()
    try:
        total = session.exec(select(func.count(Order.id))).one()
        new = session.exec(select(func.count(Order.id)).where(Order.status == "new")).one()
        analyzed = session.exec(select(func.count(Order.id)).where(Order.status == "analyzed")).one()
        responded = session.exec(select(func.count(Order.id)).where(Order.status == "responded")).one()

        text = (
            "Статус системы:\n\n"
            f"Заказов в БД: {total}\n"
            f"  Новых: {new}\n"
            f"  Проанализировано: {analyzed}\n"
            f"  С откликом: {responded}\n\n"
            f"Claude API: {'OK' if settings.anthropic_api_key else 'Нет ключа'}\n"
            f"Модель анализа: {settings.analyzer_model}\n"
            f"Модель генерации: {settings.writer_model}\n"
            f"Порог оценки: {settings.min_score_threshold}\n"
        )
        await callback.message.answer(text, reply_markup=main_menu_kb())
    finally:
        session.close()


@router.callback_query(F.data.startswith("pitch_"))
async def cb_pitch(callback: CallbackQuery):
    """Кнопка генерации отклика."""
    if not _is_admin(callback):
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    order_id = int(callback.data.split("_")[1])
    await callback.answer(f"Генерирую отклик #{order_id}...")

    from src.agents.response_writer import response_writer

    try:
        result = await response_writer.run(order_id)
        if not result:
            await callback.message.answer("Не удалось. Проверь что заказ проанализирован.")
            return
        text = (
            f"Отклик на: {result['order_title'][:50]}\n"
            f"Цена: {result['proposed_price']} р. | Срок: {result['proposed_deadline']}\n\n"
            f"{result['pitch_text']}\n\n"
            f"ID={result['response_id']}"
        )
        if len(text) > 4000:
            text = text[:4000] + "\n...(обрезано)"
        await callback.message.answer(text)
    except Exception as e:
        await callback.message.answer(f"Ошибка: {e}")
