"""Оркестратор: координирует Executor и QA Agent."""

from loguru import logger

from src.agents.executor import ExecutorAgent
from src.agents.qa import QAAgent
from src.database.db import get_session
from src.database.models import Execution, Order
from src.database.queries import get_order_by_id

MAX_QA_ITERATIONS = 3


async def execute_with_qa(order_id: int) -> dict | None:
    """Выполнить заказ с проверкой качества.

    Цикл: Executor выполняет -> QA проверяет -> если не прошёл, Executor исправляет.
    Максимум MAX_QA_ITERATIONS итераций.

    Returns:
        Словарь с результатом или None
    """
    session = get_session()
    executor = ExecutorAgent()
    qa = QAAgent()

    try:
        order = get_order_by_id(order_id, session)
        if not order:
            logger.error(f"Заказ #{order_id} не найден")
            return None

        result_text = None
        qa_result = None
        feedback = ""
        iteration = 0

        for iteration in range(1, MAX_QA_ITERATIONS + 1):
            logger.info(f"Заказ #{order_id}: итерация {iteration}/{MAX_QA_ITERATIONS}")

            # 1. Executor выполняет (или исправляет)
            result_text = await executor.execute_order(order, feedback=feedback)
            if not result_text:
                return None

            # 2. QA проверяет
            qa_result = await qa.check_quality(order.description, result_text)
            if not qa_result:
                logger.warning("QA проверка не удалась, принимаем результат как есть")
                break

            if qa_result.passed:
                logger.info(f"Заказ #{order_id}: QA пройден на итерации {iteration}")
                break

            # 3. Формируем обратную связь для следующей итерации
            issues = "\n".join(f"- {issue}" for issue in qa_result.issues)
            feedback = f"{qa_result.overall_comment}\n\nПроблемы:\n{issues}"
            logger.info(f"Заказ #{order_id}: QA не пройден, проблем: {len(qa_result.issues)}")

        # Сохраняем результат в БД
        qa_passed = qa_result.passed if qa_result else False
        execution = Execution(
            order_id=order.id,
            task_description=order.description,
            result_text=result_text,
            qa_passed=qa_passed,
            qa_iterations=iteration,
            qa_checklist=qa_result.model_dump_json() if qa_result else None,
            status="completed" if qa_passed else "review",
        )
        session.add(execution)
        session.commit()
        session.refresh(execution)

        # Формируем чек-лист для отображения
        checklist_display = []
        if qa_result:
            for item in qa_result.checklist:
                passed = item.get("passed", False)
                mark = "+" if passed else "-"
                checklist_display.append(f"[{mark}] {item.get('item', '')}")

        # Записываем расходы API
        api_cost = executor.claude.estimated_cost_usd
        if api_cost > 0:
            from src.utils.finance import record_api_cost
            record_api_cost(api_cost, f"Выполнение заказа #{order_id}", order_id, session)

        return {
            "order_id": order.id,
            "order_title": order.title,
            "execution_id": execution.id,
            "result_text": result_text,
            "qa_passed": qa_passed,
            "qa_iterations": iteration,
            "qa_checklist": checklist_display,
            "qa_comment": qa_result.overall_comment if qa_result else "",
            "qa_issues": qa_result.issues if qa_result else [],
            "api_cost": api_cost,
        }

    finally:
        session.close()
