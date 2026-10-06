"""六章统一 AI 问答与章节视觉回归测试。"""

from __future__ import annotations

import os

from playwright.sync_api import sync_playwright


BASE_URL = os.environ.get("TONGXIN_BASE_URL", "http://127.0.0.1:5173")
SLUGS = ("han", "northern-wei", "tang", "yuan", "qing", "contemporary")


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.set_default_timeout(10000)

        for slug in SLUGS:
            page.goto(f"{BASE_URL}/chapter/{slug}/chat", wait_until="networkidle")
            page.locator(".chat__main").wait_for()
            assert page.locator(".chat__modes").count() == 0, slug
            assert page.get_by_text("叙事模式", exact=True).count() == 0, slug
            assert page.get_by_text("史实模式", exact=True).count() == 0, slug
            image = page.locator(".chat__portrait img")
            assert image.is_visible(), slug
            assert image.evaluate("img => img.naturalWidth") > 0, slug

        page.goto(f"{BASE_URL}/chapter/yuan/chat", wait_until="networkidle")
        yuan_image = page.locator(".chat__portrait img")
        yuan_image.wait_for()
        assert yuan_image.get_attribute("src") == "/assets/yuan/yuntai-east-wall-original.jpg"

        print("UNIFIED_CHAT_CHAPTERS", len(SLUGS))
        print("UNIFIED_CHAT_UI", "PASS")
        browser.close()


if __name__ == "__main__":
    main()
