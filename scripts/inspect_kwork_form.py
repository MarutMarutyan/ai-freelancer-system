"""Инспектируем форму создания кворка — находим все элементы."""
from playwright.sync_api import sync_playwright
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')


def wait_for_login(page):
    print("\nВойди в аккаунт Kwork. Жду...\n")
    for _ in range(120):
        time.sleep(2)
        try:
            if page.locator("a[href*='/user/']").first.is_visible(timeout=500):
                print(">>> Вход выполнен!\n")
                return True
        except:
            pass
    return False


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_context(viewport={"width": 1280, "height": 900}).new_page()

        page.goto("https://kwork.ru/login", timeout=30000)
        page.wait_for_load_state("networkidle")

        if not wait_for_login(page):
            browser.close()
            return

        time.sleep(2)

        # Go to create kwork page
        page.goto("https://kwork.ru/new", timeout=30000)
        page.wait_for_load_state("networkidle")
        time.sleep(3)

        # Screenshot
        page.screenshot(path="scripts/form_inspect.png", full_page=True)

        # Get all form elements
        print("=== TEXTAREAS ===")
        textareas = page.locator("textarea").all()
        for i, ta in enumerate(textareas):
            visible = ta.is_visible()
            name = ta.get_attribute("name") or ""
            placeholder = ta.get_attribute("placeholder") or ""
            cls = ta.get_attribute("class") or ""
            print(f"  [{i}] visible={visible} name='{name}' placeholder='{placeholder}' class='{cls[:60]}'")

        print("\n=== INPUTS ===")
        inputs = page.locator("input").all()
        for i, inp in enumerate(inputs):
            visible = inp.is_visible()
            typ = inp.get_attribute("type") or ""
            name = inp.get_attribute("name") or ""
            placeholder = inp.get_attribute("placeholder") or ""
            value = inp.input_value() if visible else ""
            print(f"  [{i}] visible={visible} type='{typ}' name='{name}' placeholder='{placeholder}' value='{value}'")

        print("\n=== SELECTS ===")
        selects = page.locator("select").all()
        for i, sel in enumerate(selects):
            visible = sel.is_visible()
            name = sel.get_attribute("name") or ""
            print(f"  [{i}] visible={visible} name='{name}'")

        print("\n=== BUTTONS ===")
        buttons = page.locator("button").all()
        for i, btn in enumerate(buttons):
            visible = btn.is_visible()
            text = btn.inner_text() if visible else ""
            print(f"  [{i}] visible={visible} text='{text[:50]}'")

        # Get the HTML of the form area
        print("\n=== FORM HTML (first 3000 chars) ===")
        form_html = page.locator(".container, main, #app, [class*='create']").first.inner_html()
        print(form_html[:3000])

        input("\nНажми Enter чтобы закрыть...")
        browser.close()


if __name__ == "__main__":
    main()
