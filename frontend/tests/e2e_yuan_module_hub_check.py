"""六章三板块大厅、独立入口与返回路径回归测试。"""

from __future__ import annotations

import os

from playwright.sync_api import Page, sync_playwright


BASE_URL = os.environ.get("TONGXIN_BASE_URL", "http://127.0.0.1:5173")

CHAPTERS = {
    "han": ("路线与文物探查", "展签校勘剧情"),
    "northern-wei": ("双城证据探查", "墓志展陈剧情"),
    "tang": ("画卷人物探查", "画外来使剧情"),
    "yuan": ("六体文字探查", "12 幕证据剧情"),
    "qing": ("东归路线探查", "多声部东归剧情"),
    "contemporary": ("羌绣知识探查", "授权共创剧情"),
}


def open_hub(page: Page, slug: str) -> None:
    page.goto(f"{BASE_URL}/chapter/{slug}", wait_until="networkidle")
    page.locator(".briefing__modules").wait_for()


def assert_three_cards(page: Page, explore_title: str, story_title: str) -> None:
    cards = page.locator(".briefing__module")
    assert cards.count() == 3
    assert page.get_by_role("button", name=explore_title, exact=False).is_visible()
    assert page.get_by_role("button", name="AI 助手问答", exact=False).is_visible()
    assert page.get_by_role("button", name=story_title, exact=False).is_visible()
    for index in range(3):
        assert cards.nth(index).locator(".briefing__module-progress").inner_text().startswith("当前进度 · ")
        assert cards.nth(index).locator(".briefing__module-experience").inner_text().startswith("预计体验 · ")


def assert_module_routes(page: Page, slug: str, explore_title: str, story_title: str) -> None:
    page.get_by_role("button", name=explore_title, exact=False).click()
    page.wait_for_url(f"**/chapter/{slug}/scene?module=explore")
    assert page.locator(".quest").count() == 0
    lens_button = page.locator(".cs__tools .cs__tool").first
    lens_class = lens_button.get_attribute("class") or ""
    assert "is-on" in lens_class, f"{slug}: 探查模式未自动开启透镜（{lens_class}）"
    page.get_by_role("button", name="返回任务大厅", exact=True).click()
    page.wait_for_url(f"**/chapter/{slug}")
    assert page.locator(".briefing__module").nth(2).locator(".briefing__module-progress").inner_text() == "当前进度 · 未开始"

    page.get_by_role("button", name="AI 助手问答", exact=False).click()
    page.wait_for_url(f"**/chapter/{slug}/chat")
    page.get_by_role("button", name="任务大厅", exact=False).click()
    page.wait_for_url(f"**/chapter/{slug}")
    assert page.locator(".briefing__module").nth(2).locator(".briefing__module-progress").inner_text() == "当前进度 · 未开始"

    page.get_by_role("button", name=story_title, exact=False).click()
    if slug == "yuan":
        page.wait_for_url("**/chapter/yuan/story")
        page.get_by_role("link", name="任务简报", exact=False).click()
    else:
        page.wait_for_url(f"**/chapter/{slug}/scene?module=story")
        page.locator(".quest").wait_for()
        assert page.locator(".quest").is_visible(), f"{slug}: 剧情模式未显示任务卷"
        page.get_by_role("button", name="返回任务大厅", exact=True).click()
    page.wait_for_url(f"**/chapter/{slug}")
    if slug != "yuan":
        assert page.locator(".briefing__module").nth(2).locator(".briefing__module-progress").inner_text() == "当前进度 · 进行中"


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.set_default_timeout(12000)

        page.goto(BASE_URL, wait_until="domcontentloaded")
        page.evaluate("localStorage.clear()")
        for slug, (explore_title, story_title) in CHAPTERS.items():
            open_hub(page, slug)
            assert_three_cards(page, explore_title, story_title)
            assert_module_routes(page, slug, explore_title, story_title)

        mobile = browser.new_page(viewport={"width": 390, "height": 844})
        open_hub(mobile, "han")
        assert mobile.locator(".briefing__module").count() == 3
        assert mobile.evaluate("document.documentElement.scrollWidth <= window.innerWidth")

        print("CHAPTER_MODULE_HUBS", len(CHAPTERS), "PASS")
        print("CHAPTER_MODULE_HUBS_MOBILE", "PASS")
        browser.close()


if __name__ == "__main__":
    main()
