"""Создаёт обложки для кворков 660x440 px. Минимум 30 Кб."""
from PIL import Image, ImageDraw, ImageFont
import os
import math
import random

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "templates", "covers")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load fonts
font_title = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 52)
font_subtitle = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 28)
font_icon = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 60)
font_icon_small = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 32)

COVERS = [
    {
        "filename": "cover_copywriting.png",
        "bg_top": (22, 80, 130),
        "bg_bottom": (52, 152, 219),
        "title": "КОПИРАЙТИНГ",
        "subtitle": "Тексты для сайтов\nи соцсетей",
        "icon_text": "Aa",
    },
    {
        "filename": "cover_translation.png",
        "bg_top": (20, 100, 60),
        "bg_bottom": (46, 204, 113),
        "title": "ПЕРЕВОД EN/RU",
        "subtitle": "English - Русский\nРусский - English",
        "icon_text": "EN\nRU",
    },
    {
        "filename": "cover_landing.png",
        "bg_top": (80, 40, 110),
        "bg_bottom": (155, 89, 182),
        "title": "ЛЕНДИНГ",
        "subtitle": "Адаптивный сайт\nHTML / CSS / JS",
        "icon_text": "</>",
    },
]


def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def draw_centered_text(draw, text, y, font, fill, w):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text((w // 2 - tw // 2, y), text, fill=fill, font=font)


def create_cover(cover):
    w, h = 660, 440
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)

    random.seed(hash(cover["filename"]))

    # Gradient background
    for y in range(h):
        color = lerp_color(cover["bg_top"], cover["bg_bottom"], y / h)
        draw.line([(0, y), (w, y)], fill=color)

    # Decorative pattern - many small circles for texture (increases file size)
    for _ in range(200):
        x = random.randint(0, w)
        y = random.randint(0, h)
        r = random.randint(2, 15)
        alpha = random.randint(10, 35)
        c = lerp_color(cover["bg_top"], (255, 255, 255), 0.3)
        c_with_var = (
            min(255, c[0] + random.randint(-20, 20)),
            min(255, c[1] + random.randint(-20, 20)),
            min(255, c[2] + random.randint(-20, 20)),
        )
        draw.ellipse([x - r, y - r, x + r, y + r], fill=c_with_var)

    # Redraw gradient with transparency effect by drawing semi-transparent overlay
    overlay = Image.new("RGB", (w, h))
    od = ImageDraw.Draw(overlay)
    for y in range(h):
        color = lerp_color(cover["bg_top"], cover["bg_bottom"], y / h)
        od.line([(0, y), (w, y)], fill=color)
    img = Image.blend(img, overlay, 0.7)
    draw = ImageDraw.Draw(img)

    # Decorative diagonal lines
    for i in range(-h, w + h, 30):
        c = lerp_color(cover["bg_bottom"], (255, 255, 255), 0.15)
        draw.line([(i, 0), (i + h // 2, h)], fill=c, width=1)

    # Large decorative circle behind icon (soft glow effect)
    cx, cy = w // 2, 125
    for r in range(90, 40, -2):
        alpha = 0.02 + (90 - r) * 0.005
        c = lerp_color(cover["bg_bottom"], (255, 255, 255), alpha)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c)

    # White circle for icon
    cr = 58
    # Shadow
    draw.ellipse([cx - cr + 4, cy - cr + 4, cx + cr + 4, cy + cr + 4],
                 fill=lerp_color(cover["bg_top"], (0, 0, 0), 0.5))
    # Main circle
    draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill="white")

    # Icon text
    icon_lines = cover["icon_text"].split("\n")
    icon_color = cover["bg_top"]
    if len(icon_lines) == 1:
        bbox = draw.textbbox((0, 0), icon_lines[0], font=font_icon)
        iw = bbox[2] - bbox[0]
        ih = bbox[3] - bbox[1]
        draw.text((cx - iw // 2, cy - ih // 2 - 8), icon_lines[0],
                   fill=icon_color, font=font_icon)
    else:
        total_h = len(icon_lines) * 34
        y_start = cy - total_h // 2 - 5
        for line in icon_lines:
            bbox = draw.textbbox((0, 0), line, font=font_icon_small)
            lw = bbox[2] - bbox[0]
            draw.text((cx - lw // 2, y_start), line, fill=icon_color, font=font_icon_small)
            y_start += 34

    # Title with shadow
    title_y = 215
    draw_centered_text(draw, cover["title"], title_y + 2, font_title, (0, 0, 0), w)
    draw_centered_text(draw, cover["title"], title_y, font_title, "white", w)

    # Decorative line under title
    title_bbox = draw.textbbox((0, 0), cover["title"], font=font_title)
    title_w = title_bbox[2] - title_bbox[0]
    line_y = 278
    draw.rectangle([w // 2 - title_w // 3, line_y,
                     w // 2 + title_w // 3, line_y + 2], fill=(255, 255, 255))

    # Subtitle
    lines = cover["subtitle"].split("\n")
    y_start = 298
    for line in lines:
        draw_centered_text(draw, line, y_start + 1, font_subtitle, (0, 0, 0), w)
        draw_centered_text(draw, line, y_start, font_subtitle, (230, 235, 240), w)
        y_start += 38

    # Bottom accent
    for y in range(h - 8, h):
        t = (y - (h - 8)) / 8
        c = lerp_color(cover["bg_bottom"], (255, 255, 255), t)
        draw.line([(0, y), (w, y)], fill=c)

    filepath = os.path.join(OUTPUT_DIR, cover["filename"])
    img.save(filepath, "PNG")

    size_kb = os.path.getsize(filepath) / 1024
    print(f"OK: {cover['filename']} ({size_kb:.0f} Kb)")


for c in COVERS:
    create_cover(c)

print("\nGotovo!")
