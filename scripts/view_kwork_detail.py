from playwright.sync_api import sync_playwright
import sys

sys.stdout.reconfigure(encoding='utf-8')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.goto("https://kwork.ru/user/marut87", timeout=30000)
    page.wait_for_load_state("networkidle")

    # Get profile text
    content = page.inner_text("body")
    print(content[:8000])

    browser.close()
