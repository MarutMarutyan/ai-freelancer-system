"""
Скрипт для создания кворков на Kwork.
Заполняет форму автоматически, но НЕ публикует — пользователь проверяет сам.
"""
from playwright.sync_api import sync_playwright
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

KWORKS = [
    {
        "title": "Напишу продающий текст для сайта, соцсетей или рекламы",
        "category": "Тексты и переводы",
        "subcategory": "Копирайтинг",
        "description": (
            "Напишу качественный текст под вашу задачу:\n\n"
            "- Продающие тексты для лендингов и сайтов\n"
            "- Посты для соцсетей (ВК, Telegram, Instagram)\n"
            "- Описания товаров и услуг\n"
            "- SEO-статьи для блога\n"
            "- Рекламные тексты\n\n"
            "Что вы получите:\n"
            "- Текст до 3000 символов\n"
            "- Учёт вашей целевой аудитории\n"
            "- 1 бесплатная правка\n"
            "- Срок: 1-2 дня\n\n"
            "Перед началом работы могу показать мини-демо, чтобы вы оценили стиль."
        ),
        "buyer_needs": (
            "Для выполнения заказа мне потребуется от вас:\n\n"
            "1. Тема текста и его назначение (для сайта, соцсетей, рекламы)\n"
            "2. Целевая аудитория (кому адресован текст)\n"
            "3. Ключевые моменты, которые нужно отразить в тексте\n"
            "4. Примеры текстов, которые вам нравятся (если есть)\n"
            "5. Желаемый объём текста в символах"
        ),
        "volume": "до 3000 символов",
        "price": "500",
    },
    {
        "title": "Переведу текст с английского на русский или наоборот",
        "category": "Тексты и переводы",
        "subcategory": "Переводы",
        "description": (
            "Качественный перевод EN - RU и RU - EN:\n\n"
            "- Статьи и блоги\n"
            "- Описания товаров\n"
            "- Деловая переписка\n"
            "- Инструкции и документация\n"
            "- Субтитры и тексты для видео\n\n"
            "Что вы получите:\n"
            "- Перевод до 2000 символов\n"
            "- Сохранение смысла и стиля оригинала\n"
            "- 1 бесплатная правка\n"
            "- Срок: 1 день\n\n"
            "Перевожу грамотно, с учётом контекста. Не машинный перевод."
        ),
        "buyer_needs": (
            "Для выполнения перевода мне потребуется от вас:\n\n"
            "1. Текст для перевода (или ссылка на документ)\n"
            "2. Направление перевода (EN-RU или RU-EN)\n"
            "3. Контекст использования (сайт, документация, соцсети)\n"
            "4. Специальная терминология (если есть)\n"
            "5. Желаемый стиль (формальный, разговорный, нейтральный)"
        ),
        "volume": "до 2000 символов",
        "price": "500",
    },
    {
        "title": "Сделаю адаптивный лендинг на HTML CSS JS",
        "category": "Разработка и IT",
        "subcategory": "Сайты",
        "description": (
            "Создам современный лендинг под вашу задачу:\n\n"
            "- Адаптивный дизайн (телефон, планшет, ПК)\n"
            "- Чистый HTML/CSS/JavaScript\n"
            "- Форма обратной связи\n"
            "- Анимации при прокрутке\n"
            "- SEO-оптимизация\n\n"
            "Что вы получите:\n"
            "- Готовый лендинг из 3-5 секций\n"
            "- Все исходники\n"
            "- Помощь с размещением на хостинге\n"
            "- Срок: 2-3 дня\n\n"
            "Покажу демо-версию до начала работы."
        ),
        "buyer_needs": (
            "Для создания лендинга мне потребуется от вас:\n\n"
            "1. Тематика сайта и его цель (продажа, презентация, сбор заявок)\n"
            "2. Текст для размещения на сайте (или тезисы)\n"
            "3. Логотип и фирменные цвета (если есть)\n"
            "4. Примеры сайтов, которые вам нравятся (если есть)\n"
            "5. Нужна ли форма обратной связи и куда отправлять заявки"
        ),
        "volume": "лендинг 3-5 секций",
        "price": "1500",
    },
]


def wait_for_login(page):
    print("\n========================================")
    print("  Войди в аккаунт на Kwork")
    print("  Скрипт продолжит автоматически")
    print("========================================\n")
    for _ in range(120):
        time.sleep(2)
        try:
            if page.locator("a[href*='/user/']").first.is_visible(timeout=500):
                print(">>> Вход выполнен!\n")
                return True
        except:
            pass
    return False


def fill_kwork(page, kwork, index):
    total = len(KWORKS)
    print(f"\n=== Кворк {index + 1} из {total} ===")
    print(f"    {kwork['title']}\n")

    page.goto("https://kwork.ru/new", timeout=30000)
    page.wait_for_load_state("networkidle")
    time.sleep(3)

    # ---- STEP 1: Title + Category ----
    print("  [1/3] Название и рубрика...")

    # Title — the textarea is hidden, need to click on step 1 area first
    # The title field might become visible after clicking on the step
    step1_header = page.locator("text=Основное").first
    if step1_header.is_visible(timeout=3000):
        step1_header.click()
        time.sleep(1)

    # Try to find and fill the title textarea
    title_ta = page.locator("textarea[name='title']")
    if not title_ta.is_visible(timeout=2000):
        # Maybe it's shown as a different element, use JS to set value
        page.evaluate(f"""
            const el = document.querySelector("textarea[name='title']");
            if (el) {{
                el.value = {repr(kwork['title'])};
                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                el.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }}
        """)
        print("    Название заполнено через JS")
    else:
        title_ta.fill(kwork["title"])
        print("    Название заполнено")

    time.sleep(1)

    # Category — it's a custom dropdown, use JS to set the select value
    # First try clicking the visible dropdown
    try:
        rubrika = page.locator("text=Выберите рубрику").first
        if rubrika.is_visible(timeout=2000):
            rubrika.click()
            time.sleep(1)
            # Try to click the category option
            page.locator(f"text={kwork['category']}").first.click(timeout=3000)
            time.sleep(1)
            # Try subcategory
            try:
                page.locator(f"text={kwork['subcategory']}").first.click(timeout=3000)
                time.sleep(1)
            except:
                pass
            print(f"    Рубрика: {kwork['category']} > {kwork['subcategory']}")
    except:
        print("    ! Рубрику нужно выбрать вручную")

    page.screenshot(path=f"scripts/kwork_{index}_step1.png", full_page=True)

    # Click "Продолжить" for step 1
    try:
        buttons = page.locator("button, a, span, div").filter(has_text="Продолжить").all()
        for btn in buttons:
            if btn.is_visible():
                btn.click()
                time.sleep(2)
                break
    except:
        pass

    # ---- STEP 2: Description ----
    print("  [2/3] Описание...")

    # Description textarea
    desc_ta = page.locator("textarea[name='description']")
    if desc_ta.is_visible(timeout=3000):
        desc_ta.fill(kwork["description"])
        print("    Описание заполнено")
    else:
        page.evaluate(f"""
            const el = document.querySelector("textarea[name='description']");
            if (el) {{
                el.value = {repr(kwork['description'])};
                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }}
        """)
        print("    Описание заполнено через JS")

    time.sleep(1)

    # "От покупателя нужно" — instruction textarea
    instr_ta = page.locator("textarea[name='instruction']")
    if instr_ta.is_visible(timeout=2000):
        instr_ta.fill(kwork["buyer_needs"])
        print("    'От покупателя нужно' заполнено")
    else:
        page.evaluate(f"""
            const el = document.querySelector("textarea[name='instruction']");
            if (el) {{
                el.value = {repr(kwork['buyer_needs'])};
                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }}
        """)
        print("    'От покупателя нужно' заполнено через JS")

    page.screenshot(path=f"scripts/kwork_{index}_step2.png", full_page=True)

    # Click "Продолжить" for step 2
    try:
        buttons = page.locator("button, a, span, div").filter(has_text="Продолжить").all()
        for btn in buttons:
            if btn.is_visible():
                btn.click()
                time.sleep(2)
                break
    except:
        pass

    # ---- STEP 3: Price ----
    print("  [3/3] Стоимость...")

    # Volume field
    vol_input = page.locator("input[name='volume']")
    if vol_input.is_visible(timeout=2000):
        vol_input.fill(kwork["volume"])
    else:
        page.evaluate(f"""
            const el = document.querySelector("input[name='volume']");
            if (el) {{
                el.value = {repr(kwork['volume'])};
                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }}
        """)

    # Service size
    svc = page.locator("input[name='service_size']")
    if svc.is_visible(timeout=1000):
        svc.fill(kwork["volume"])

    time.sleep(1)

    page.screenshot(path=f"scripts/kwork_{index}_step3.png", full_page=True)

    print(f"\n  >>> Кворк {index + 1} заполнен!")
    print(f"  >>> ПРОВЕРЬ все поля в браузере")
    print(f"  >>> Выбери рубрику если она не выбралась автоматически")
    print(f"  >>> Нажми 'Сохранить' / 'Опубликовать' когда всё ок")
    print(f"  >>> Скриншоты: scripts/kwork_{index}_step1/2/3.png")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=200)
        page = browser.new_context(viewport={"width": 1280, "height": 900}).new_page()

        page.goto("https://kwork.ru/login", timeout=30000)
        page.wait_for_load_state("networkidle")

        if not wait_for_login(page):
            browser.close()
            return

        time.sleep(2)

        for i, kwork in enumerate(KWORKS):
            fill_kwork(page, kwork, i)
            if i < len(KWORKS) - 1:
                print(f"\n  Когда опубликуешь этот кворк,")
                print(f"  вернись в терминал и нажми Enter.")
                try:
                    input(f"  >>> Нажми Enter для кворка {i + 2}...")
                except EOFError:
                    print("  (auto-continuing in 30 seconds...)")
                    time.sleep(30)

        print("\n========================================")
        print("  ВСЕ 3 КВОРКА ЗАПОЛНЕНЫ!")
        print("  Проверь и опубликуй каждый")
        print("========================================")

        # Keep browser open for user to work
        try:
            input("\nНажми Enter чтобы закрыть браузер...")
        except EOFError:
            time.sleep(60)
        browser.close()


if __name__ == "__main__":
    main()
