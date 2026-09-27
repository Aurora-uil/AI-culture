from pathlib import Path
import os
import re
import sys

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[2]
SCREENSHOTS = ROOT / "docs" / "screenshots"
BASE_URL = os.environ.get("TONGXIN_BASE_URL", "http://127.0.0.1:5173")
SCREENSHOTS.mkdir(parents=True, exist_ok=True)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def main() -> None:
    console_errors: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        page.on(
            "console",
            lambda message: console_errors.append(message.text)
            if message.type == "error"
            else None,
        )

        page.goto(f"{BASE_URL}/", wait_until="networkidle")
        page.evaluate("localStorage.clear()")
        page.reload(wait_until="networkidle")
        page.get_by_text("六段人生", exact=True).wait_for()
        page.wait_for_timeout(1800)
        page.screenshot(path=str(SCREENSHOTS / "v5-splash-flow.png"), full_page=True)

        page.get_by_role("button", name="领取第一段身份").click()
        page.wait_for_url("**/timeline")
        page.get_by_text("选择一段身份", exact=False).wait_for()
        page.wait_for_timeout(700)
        page.screenshot(path=str(SCREENSHOTS / "v5-timeline-flow.png"), full_page=True)

        yuan_link = page.locator("article.era--recommended a.era__link")
        assert yuan_link.get_attribute("href") == "/chapter/yuan/intro"
        yuan_link.click()
        page.wait_for_url("**/chapter/yuan/intro")
        page.get_by_role("heading", name="石壁上的六种声音").wait_for()
        page.wait_for_timeout(700)
        page.screenshot(path=str(SCREENSHOTS / "v2-yuan-intro.png"), full_page=True)

        page.get_by_role("button", name="接受身份").click()
        page.wait_for_url("**/chapter/yuan")
        page.get_by_text("你的任务", exact=True).wait_for()
        page.wait_for_timeout(700)
        page.screenshot(path=str(SCREENSHOTS / "v2-yuan-briefing.png"), full_page=True)

        page.get_by_role("button", name="接受身份，进入场景").click()
        page.wait_for_url("**/chapter/yuan/scene")
        page.get_by_text("当前任务", exact=True).wait_for()
        page.wait_for_timeout(700)
        page.screenshot(path=str(SCREENSHOTS / "v5-yuan-scene-flow.png"), full_page=True)

        # 完整闭环：三处题刻 -> 六体透镜 -> 史料抉择 -> 章节结算。
        page.get_by_role("button", name=re.compile("当前任务")).click()
        for index, hotspot in enumerate(["梵文书写系统", "藏文", "八思巴文"]):
            page.get_by_role("button", name=re.compile(f"^{hotspot}，未探索")).click()
            # 内容库可能使用更精确的题刻名称，抽屉标题无需和场景短标签完全一致。
            page.get_by_role("dialog").wait_for()
            if index == 0:
                page.wait_for_timeout(450)
                page.screenshot(path=str(SCREENSHOTS / "v5-entity-drawer.png"), full_page=True)
            page.keyboard.press("Escape")

        page.get_by_role("button", name="六体文字透镜").click()
        page.get_by_role("button", name=re.compile("当前任务")).click()
        page.get_by_role("button", name="进入本章抉择").wait_for()
        page.get_by_role("button", name="进入本章抉择").click()
        page.get_by_role("heading", name="拓片的位置标记已经脱落").wait_for()
        page.get_by_role("button", name=re.compile("暂列“位置待核”")).click()
        page.get_by_text("你留下的选择", exact=True).wait_for()
        page.wait_for_timeout(400)
        page.screenshot(path=str(SCREENSHOTS / "v4-yuan-choice-result.png"), full_page=True)

        page.get_by_role("button", name=re.compile("整理本章记录")).click()
        page.wait_for_url("**/chapter/yuan/summary")
        page.get_by_text("共存之结", exact=True).wait_for()
        page.wait_for_timeout(700)
        page.screenshot(path=str(SCREENSHOTS / "v2-yuan-ending.png"), full_page=True)

        page.get_by_role("button", name="查看我的千年史册").click()
        page.wait_for_url("**/journey")
        page.get_by_role("heading", name="我的千年史册").wait_for()
        page.get_by_text("六体索引拓册", exact=True).wait_for()
        page.get_by_text("暂列“位置待核”", exact=True).wait_for()
        page.get_by_text("清代 · 向东的长路", exact=True).wait_for()
        page.wait_for_timeout(500)
        page.screenshot(path=str(SCREENSHOTS / "v2-journey.png"), full_page=True)

        saved = page.evaluate("JSON.parse(localStorage.getItem('tongxin.game.v2'))")
        assert saved["yuan"]["decisionId"] == "leave_pending"
        assert saved["yuan"]["completed"] is True
        assert len(saved["yuan"]["evidenceIds"]) >= 3

        page.set_viewport_size({"width": 390, "height": 844})
        page.goto(f"{BASE_URL}/", wait_until="networkidle")
        page.get_by_text("六段人生", exact=True).wait_for()
        page.wait_for_timeout(1900)
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        page.screenshot(path=str(SCREENSHOTS / "v2-splash-mobile.png"), full_page=True)

        print("URL", page.url)
        print("TITLE", page.title())
        print("YUAN_PROGRESS", saved["yuan"])
        print("CONSOLE_ERRORS", console_errors)
        browser.close()


if __name__ == "__main__":
    main()
