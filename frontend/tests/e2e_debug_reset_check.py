import os
import sys

from playwright.sync_api import sync_playwright


BASE_URL = os.environ.get("TONGXIN_BASE_URL", "http://127.0.0.1:5173")
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(f"{BASE_URL}/", wait_until="networkidle")
        page.evaluate(
            """
            localStorage.setItem('tongxin.game.v2', JSON.stringify({
              yuan: {
                started: true,
                completed: true,
                actions: { COMPLETE: true },
                evidenceIds: ['yuan-proof'],
                decisionId: 'limited_confirmation',
                methods: { truth: 1, empathy: 1, connection: 1 },
                updatedAt: new Date().toISOString()
              }
            }));
            localStorage.setItem('tongxin.yuan.story.v6', JSON.stringify({ sceneIndex: 11 }));
            """
        )
        page.reload(wait_until="networkidle")

        page.get_by_text("已结成 1/6", exact=True).wait_for()
        page.once("dialog", lambda dialog: dialog.accept())
        page.get_by_role("button", name="调试 · 重置进度").click()
        page.get_by_role("button", name="进度已重置").wait_for()
        page.get_by_text("已结成 0/6", exact=True).wait_for()

        assert page.evaluate("localStorage.getItem('tongxin.game.v2')") is None
        assert page.evaluate("localStorage.getItem('tongxin.yuan.story.v6')") is None

        page.get_by_role("button", name="领取第一段身份").click()
        page.wait_for_url("**/timeline")
        yuan_link = page.locator("article.era--recommended a.era__link")
        assert yuan_link.get_attribute("href") == "/chapter/yuan/intro"

        print("DEBUG_RESET_GAME_STORAGE", "CLEARED")
        print("DEBUG_RESET_YUAN_STORAGE", "CLEARED")
        print("DEBUG_RESET_YUAN_ROUTE", yuan_link.get_attribute("href"))
        browser.close()


if __name__ == "__main__":
    main()
