"""HTTP-парсер биржи проектов Kwork."""

import json
import random

import httpx
from loguru import logger

from src.database.db import get_session
from src.database.models import Order
from src.database.queries import order_exists, save_order
from src.kwork.categories import ACTIVE_CATEGORIES, get_category_name
from src.kwork.models import KworkProject, KworkUser
from src.utils.rate_limiter import kwork_limiter

# Ротация User-Agent для имитации обычного браузера
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
]

BASE_URL = "https://kwork.ru/projects"


def _get_headers() -> dict:
    """Сгенерировать заголовки запроса со случайным User-Agent."""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }


def _extract_json_data(html: str) -> list[dict] | None:
    """Извлечь JSON-данные заказов из HTML страницы.

    Kwork хранит данные в window.stateData.wantsListData.pagination.data[].
    Используем json.JSONDecoder.raw_decode для парсинга массива прямо из HTML.
    """
    pag_idx = html.find('"pagination":{')
    if pag_idx < 0:
        logger.warning("Не удалось найти pagination в HTML")
        return None

    data_idx = html.find('"data":[', pag_idx)
    if data_idx < 0:
        logger.warning("Не удалось найти data[] в pagination")
        return None

    array_start = data_idx + 7  # позиция символа [

    try:
        decoder = json.JSONDecoder()
        projects, _ = decoder.raw_decode(html, array_start)
        return projects
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка парсинга JSON: {e}")
        return None


def _parse_project(raw: dict) -> KworkProject | None:
    """Преобразовать сырой JSON в модель KworkProject."""
    try:
        user_data = raw.get("user", {})
        user_extra = user_data.get("data", {}) if user_data else {}

        user = KworkUser(
            USERID=user_data.get("USERID", 0),
            username=user_data.get("username", ""),
            wants_count=int(user_extra.get("wants_count", 0)),
            wants_hired_percent=int(user_extra.get("wants_hired_percent", 0)),
        )

        project = KworkProject(
            id=raw["id"],
            name=raw.get("name", ""),
            description=raw.get("description", ""),
            category_id=str(raw.get("category_id", "")),
            price_limit=float(raw.get("priceLimit", 0)),
            possible_price_limit=float(raw.get("possiblePriceLimit", 0)),
            views_dirty=int(raw.get("views_dirty", 0)),
            date_create=raw.get("date_create"),
            date_expire=raw.get("date_expire"),
            time_left=raw.get("timeLeft", ""),
            max_days=raw.get("max_days"),
            user=user,
        )
        return project
    except (KeyError, ValueError, TypeError) as e:
        logger.warning(f"Ошибка парсинга проекта: {e}")
        return None


def _project_to_order(project: KworkProject) -> Order:
    """Преобразовать KworkProject в модель Order для БД."""
    return Order(
        kwork_id=str(project.id),
        title=project.name,
        description=project.description,
        category=get_category_name(project.category_id),
        budget_min=None,
        budget_max=int(project.price_limit) if project.price_limit else None,
        deadline=project.max_days,
        client_name=project.client_name,
        client_reviews_count=project.client_orders_count,
        responses_count=project.views_dirty,
        url=project.url,
        status="new",
    )


async def fetch_projects_page(
    category_id: str | None = None, page: int = 1
) -> list[KworkProject]:
    """Загрузить одну страницу проектов с Kwork.

    Args:
        category_id: ID категории (None = все категории)
        page: Номер страницы

    Returns:
        Список проектов
    """
    await kwork_limiter.wait()

    url = BASE_URL
    params = {}
    if category_id:
        params["c"] = category_id
    if page > 1:
        params["page"] = str(page)

    try:
        async with httpx.AsyncClient(
            follow_redirects=True, timeout=30.0
        ) as client:
            response = await client.get(url, headers=_get_headers(), params=params)
            response.raise_for_status()

        raw_projects = _extract_json_data(response.text)
        if not raw_projects:
            logger.info(f"Нет проектов на странице (категория={category_id}, стр={page})")
            return []

        projects = []
        for raw in raw_projects:
            project = _parse_project(raw)
            if project:
                projects.append(project)

        logger.info(f"Загружено {len(projects)} проектов (категория={category_id}, стр={page})")
        return projects

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP ошибка {e.response.status_code}: {e}")
        return []
    except httpx.RequestError as e:
        logger.error(f"Ошибка запроса: {e}")
        return []


async def scan_new_projects(categories: list[str] | None = None) -> list[Order]:
    """Сканировать новые проекты по категориям и сохранить в БД.

    Args:
        categories: Список ID категорий (None = использовать ACTIVE_CATEGORIES)

    Returns:
        Список новых заказов, сохранённых в БД
    """
    cats = categories or ACTIVE_CATEGORIES
    new_orders: list[Order] = []
    session = get_session()

    try:
        for cat_id in cats:
            cat_name = get_category_name(cat_id)
            logger.info(f"Сканирую категорию: {cat_name} (ID={cat_id})")

            projects = await fetch_projects_page(category_id=cat_id)

            for project in projects:
                # Дедупликация: проверяем есть ли уже в БД
                if order_exists(str(project.id), session):
                    continue

                order = _project_to_order(project)
                save_order(order, session)
                new_orders.append(order)
                logger.info(f"Новый заказ: {project.name[:50]}... ({project.budget_display})")

        logger.info(f"Сканирование завершено. Новых заказов: {len(new_orders)}")
    finally:
        # Обновляем и отсоединяем объекты от сессии
        for order in new_orders:
            session.refresh(order)
            session.expunge(order)
        session.close()

    return new_orders
