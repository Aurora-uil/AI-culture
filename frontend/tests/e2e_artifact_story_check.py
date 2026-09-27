"""文物剧情锚点的桌面与移动端冒烟回归。"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright


BASE_URL = os.environ.get("TONGXIN_BASE_URL", "http://127.0.0.1:5173")
SCREENSHOT = Path(tempfile.gettempdir()) / "tongxin-artifact-story-check.png"

ANCHORS = {
    "han": "“五星出东方利中国”锦护膊",
    "northern-wei": "元羽墓志",
    "tang": "《步辇图》",
    "yuan": "居庸关云台六体文字题刻",
    "qing": "《万法归一图屏》",
    "contemporary": "待授权的具体羌绣作品",
}


def assert_no_horizontal_overflow(page) -> None:
    assert page.evaluate(
        "document.documentElement.scrollWidth <= window.innerWidth + 1"
    ), "页面出现横向溢出"


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        for slug, anchor in ANCHORS.items():
            page.goto(f"{BASE_URL}/chapter/{slug}", wait_until="networkidle")
            story_anchor = page.locator(".briefing__anchor")
            story_anchor.wait_for()
            assert anchor in story_anchor.inner_text(), f"{slug}: 缺少剧情锚点 {anchor}"
            assert_no_horizontal_overflow(page)

        # 当代章必须把授权前置状态直接展示给玩家。
        page.goto(f"{BASE_URL}/chapter/contemporary", wait_until="networkidle")
        page.get_by_text("授权前置", exact=True).first.wait_for()

        # 场景任务抽屉继续显示剧情锚点，避免进入玩法后退回宏观叙事。
        page.goto(f"{BASE_URL}/chapter/han/scene", wait_until="networkidle")
        handle = page.locator(".quest__handle")
        handle.wait_for()
        if handle.get_attribute("aria-expanded") != "true":
            handle.click()
        page.locator(".quest__anchor").get_by_text(ANCHORS["han"], exact=True).wait_for()

        # 移动端允许纵向延展，但不能横向溢出或截断主文物名称。
        page.set_viewport_size({"width": 390, "height": 844})
        page.goto(f"{BASE_URL}/chapter/han", wait_until="networkidle")
        page.locator(".briefing__anchor").get_by_text(ANCHORS["han"], exact=True).wait_for()
        assert_no_horizontal_overflow(page)
        page.screenshot(path=str(SCREENSHOT), full_page=True)

        print("ARTIFACT_STORY_CHAPTERS", len(ANCHORS))
        print("MOBILE_SCREENSHOT", SCREENSHOT)
        browser.close()


if __name__ == "__main__":
    main()
