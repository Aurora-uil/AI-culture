"""元代 AI 问答联网搜索端到端回归测试。"""

from __future__ import annotations

import os

from playwright.sync_api import sync_playwright


BASE_URL = os.environ.get("TONGXIN_BASE_URL", "http://127.0.0.1:5173")


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.set_default_timeout(30000)

        page.goto(f"{BASE_URL}/chapter/yuan/chat", wait_until="networkidle")
        page.locator(".chat__input").fill("云台的背景是什么")
        page.get_by_role("button", name="发送", exact=True).click()

        tier = page.get_by_text("已联网搜索 · DeepSeek 归纳", exact=True)
        tier.wait_for()
        answer = page.locator(".msg--ai").last
        answer_text = answer.inner_text()
        assert "居庸关云台" in answer_text
        assert len(answer_text) >= 120
        assert "资料不足" not in answer_text
        citations = answer.locator(".msg__cite")
        assert citations.count() >= 1
        links = answer.locator(".msg__cite[href]")
        if links.count():
            assert links.first.get_attribute("target") == "_blank"

        print("WEB_SEARCH_CHAT_STATUS", "DONE")
        print("WEB_SEARCH_CHAT_TIER", "live_rag")
        print("WEB_SEARCH_CHAT_CITATIONS", citations.count())
        print("WEB_SEARCH_CHAT_LINKS", links.count())
        print("WEB_SEARCH_CHAT_UI", "PASS")
        browser.close()


if __name__ == "__main__":
    main()
