from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.goto("https://kwork.ru/user/marut87", timeout=30000)
    page.wait_for_load_state("networkidle")

    # Screenshot full page
    page.screenshot(path="scripts/kwork_profile.png", full_page=True)
    print("Screenshot saved to scripts/kwork_profile.png")

    # Get page text content
    content = page.inner_text("body")
    print("=== PAGE CONTENT ===")
    print(content[:5000])

    browser.close()
