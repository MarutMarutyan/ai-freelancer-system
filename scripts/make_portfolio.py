"""Создаёт 5 демо-скриншотов лендингов для портфолио на Kwork. 1920x1280."""
from PIL import Image, ImageDraw, ImageFont
import os
import random

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "templates", "portfolio")
os.makedirs(OUTPUT_DIR, exist_ok=True)

font_h1 = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 64)
font_h2 = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 40)
font_body = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 28)
font_btn = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 30)
font_nav = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 22)
font_small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 20)

LANDINGS = [
    {
        "name": "landing_fitness.png",
        "title": "Лендинг фитнес-клуба",
        "nav_color": (30, 30, 30),
        "hero_top": (20, 60, 120),
        "hero_bottom": (40, 120, 200),
        "accent": (255, 165, 0),
        "logo": "FitLife",
        "nav": ["Главная", "Услуги", "Тренеры", "Контакты"],
        "headline": "Начни свой путь\nк здоровому телу",
        "subtext": "Персональные тренировки и программы питания от лучших тренеров",
        "btn": "Записаться на тренировку",
        "sections": ["Наши услуги", "Команда тренеров", "Отзывы клиентов"],
        "cards": [
            ["Персональные\nтренировки", "Групповые\nзанятия", "Программы\nпитания"],
            ["Алексей\nСтаж 10 лет", "Мария\nСтаж 7 лет", "Дмитрий\nСтаж 12 лет"],
            None,
        ],
    },
    {
        "name": "landing_restaurant.png",
        "title": "Лендинг ресторана",
        "nav_color": (50, 20, 20),
        "hero_top": (80, 20, 20),
        "hero_bottom": (160, 50, 50),
        "accent": (220, 180, 50),
        "logo": "Gusto",
        "nav": ["Меню", "О нас", "Бронирование", "Доставка"],
        "headline": "Итальянская кухня\nв сердце города",
        "subtext": "Авторские блюда от шеф-повара с 15-летним опытом",
        "btn": "Забронировать стол",
        "sections": ["Наше меню", "О ресторане", "Отзывы гостей"],
        "cards": [
            ["Паста\nот 450 руб.", "Пицца\nот 590 руб.", "Десерты\nот 350 руб."],
            None, None,
        ],
    },
    {
        "name": "landing_startup.png",
        "title": "Лендинг IT-стартапа",
        "nav_color": (25, 25, 50),
        "hero_top": (30, 30, 80),
        "hero_bottom": (80, 60, 180),
        "accent": (0, 210, 150),
        "logo": "NexTech",
        "nav": ["Продукт", "Возможности", "Цены", "Контакты"],
        "headline": "Автоматизация\nвашего бизнеса",
        "subtext": "CRM-система нового поколения для малого и среднего бизнеса",
        "btn": "Попробовать бесплатно",
        "sections": ["Возможности", "Тарифы", "Наши клиенты"],
        "cards": [
            ["Аналитика\nв реальном времени", "Интеграции\nс сервисами", "Мобильное\nприложение"],
            ["Старт\n990 руб/мес", "Бизнес\n2490 руб/мес", "Корпорация\n5990 руб/мес"],
            None,
        ],
    },
    {
        "name": "landing_education.png",
        "title": "Лендинг онлайн-школы",
        "nav_color": (20, 50, 40),
        "hero_top": (20, 80, 60),
        "hero_bottom": (40, 160, 120),
        "accent": (255, 200, 50),
        "logo": "EduPro",
        "nav": ["Курсы", "Преподаватели", "Отзывы", "Контакты"],
        "headline": "Онлайн-курсы\nот экспертов",
        "subtext": "Более 50 программ обучения с сертификатом по окончании",
        "btn": "Выбрать курс",
        "sections": ["Популярные курсы", "Преподаватели", "Сертификаты"],
        "cards": [
            ["Python\n12 недель", "Дизайн\n8 недель", "Маркетинг\n10 недель"],
            None, None,
        ],
    },
    {
        "name": "landing_realestate.png",
        "title": "Лендинг жилого комплекса",
        "nav_color": (30, 40, 50),
        "hero_top": (30, 50, 70),
        "hero_bottom": (60, 100, 140),
        "accent": (230, 120, 30),
        "logo": "DomStroy",
        "nav": ["Квартиры", "О комплексе", "Ипотека", "Контакты"],
        "headline": "Квартиры в новом\nжилом комплексе",
        "subtext": "От 3.5 млн руб. Ипотека от 5.9%. Сдача в 2026 году",
        "btn": "Подобрать квартиру",
        "sections": ["Планировки", "Инфраструктура", "Ход строительства"],
        "cards": [
            ["Студия\nот 3.5 млн", "1-комнатная\nот 5.2 млн", "2-комнатная\nот 7.8 млн"],
            None, None,
        ],
    },
]


def lerp(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def gradient(draw, x1, y1, x2, y2, c_top, c_bot):
    for y in range(y1, y2):
        t = (y - y1) / max(1, y2 - y1)
        draw.line([(x1, y), (x2, y)], fill=lerp(c_top, c_bot, t))


def centered(draw, text, y, font, fill, w):
    lines = text.split("\n")
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        draw.text((w // 2 - tw // 2, y), line, fill=fill, font=font)
        y += bbox[3] - bbox[1] + 12
    return y


def create_landing(landing):
    w, h = 1920, 1280
    img = Image.new("RGB", (w, h), (245, 245, 245))
    draw = ImageDraw.Draw(img)
    random.seed(hash(landing["name"]))

    # === NAV BAR ===
    nav_h = 70
    draw.rectangle([0, 0, w, nav_h], fill=landing["nav_color"])
    draw.text((40, 18), landing["logo"], fill=landing["accent"], font=font_h2)
    nav_x = w - 600
    for item in landing["nav"]:
        draw.text((nav_x, 24), item, fill=(200, 200, 200), font=font_nav)
        nav_x += 150

    # === HERO SECTION ===
    hero_h = 500
    gradient(draw, 0, nav_h, w, nav_h + hero_h, landing["hero_top"], landing["hero_bottom"])

    # Decorative elements
    for _ in range(60):
        cx = random.randint(0, w)
        cy = random.randint(nav_h, nav_h + hero_h)
        cr = random.randint(5, 50)
        c = lerp(landing["hero_bottom"], (255, 255, 255), random.uniform(0.05, 0.2))
        draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=c)

    # Subtle overlay
    overlay = Image.new("RGB", (w, hero_h))
    od = ImageDraw.Draw(overlay)
    gradient(od, 0, 0, w, hero_h, landing["hero_top"], landing["hero_bottom"])
    blended = Image.blend(img.crop((0, nav_h, w, nav_h + hero_h)), overlay, 0.55)
    img.paste(blended, (0, nav_h))
    draw = ImageDraw.Draw(img)

    # Hero text
    y = nav_h + 120
    for line in landing["headline"].split("\n"):
        # Shadow
        bbox = draw.textbbox((0, 0), line, font=font_h1)
        tw = bbox[2] - bbox[0]
        draw.text((w // 2 - tw // 2 + 2, y + 2), line, fill=(0, 0, 0), font=font_h1)
        draw.text((w // 2 - tw // 2, y), line, fill="white", font=font_h1)
        y += 78

    centered(draw, landing["subtext"], y + 15, font_body, (200, 210, 220), w)

    # CTA button
    btn_w, btn_h = 400, 65
    btn_x = w // 2 - btn_w // 2
    btn_y = y + 70
    draw.rounded_rectangle([btn_x, btn_y, btn_x + btn_w, btn_y + btn_h],
                            radius=32, fill=landing["accent"])
    bbox = draw.textbbox((0, 0), landing["btn"], font=font_btn)
    btw = bbox[2] - bbox[0]
    bth = bbox[3] - bbox[1]
    draw.text((btn_x + btn_w // 2 - btw // 2, btn_y + btn_h // 2 - bth // 2 - 2),
              landing["btn"], fill="white", font=font_btn)

    # === CONTENT SECTIONS ===
    section_y = nav_h + hero_h
    for i, section_title in enumerate(landing["sections"]):
        sec_h = 220
        bg = (255, 255, 255) if i % 2 == 0 else (240, 242, 245)
        draw.rectangle([0, section_y, w, section_y + sec_h], fill=bg)

        # Title
        bbox = draw.textbbox((0, 0), section_title, font=font_h2)
        tw = bbox[2] - bbox[0]
        draw.text((w // 2 - tw // 2, section_y + 25), section_title, fill=(40, 40, 40), font=font_h2)

        # Accent line
        draw.rectangle([w // 2 - 50, section_y + 75, w // 2 + 50, section_y + 78],
                       fill=landing["accent"])

        # Cards
        cards = landing["cards"][i] if i < len(landing["cards"]) else None
        if cards:
            card_w = 350
            gap = 60
            total = len(cards) * card_w + (len(cards) - 1) * gap
            start_x = w // 2 - total // 2
            for j, card_text in enumerate(cards):
                cx = start_x + j * (card_w + gap)
                card_bg = (230, 235, 240) if i % 2 == 0 else (220, 225, 230)
                draw.rounded_rectangle([cx, section_y + 95, cx + card_w, section_y + 200],
                                       radius=12, fill=card_bg)
                # Card text
                lines = card_text.split("\n")
                ty = section_y + 110
                for line in lines:
                    bbox = draw.textbbox((0, 0), line, font=font_small)
                    lw = bbox[2] - bbox[0]
                    draw.text((cx + card_w // 2 - lw // 2, ty), line,
                             fill=(60, 60, 60), font=font_small)
                    ty += 30
        else:
            # Placeholder lines
            for k in range(3):
                lw = random.randint(300, 600)
                draw.rectangle([w // 2 - lw // 2, section_y + 100 + k * 35,
                               w // 2 + lw // 2, section_y + 115 + k * 35],
                              fill=(200, 205, 210) if i % 2 == 0 else (190, 195, 200))

        section_y += sec_h

    # === FOOTER ===
    footer_h = h - section_y
    draw.rectangle([0, section_y, w, h], fill=landing["nav_color"])
    draw.text((40, section_y + 20), landing["logo"], fill=landing["accent"], font=font_h2)
    draw.text((40, section_y + 70), "info@example.com  |  +7 (999) 123-45-67",
              fill=(150, 150, 150), font=font_nav)
    draw.text((w - 300, section_y + 70), "2025 All rights reserved",
              fill=(100, 100, 100), font=font_small)

    filepath = os.path.join(OUTPUT_DIR, landing["name"])
    img.save(filepath, "PNG")
    size_kb = os.path.getsize(filepath) / 1024
    print(f"OK: {landing['name']} ({size_kb:.0f} Kb) - {landing['title']}")


for l in LANDINGS:
    create_landing(l)

print("\nGotovo!")
