"""六章节 AI 助手会话必须按章节隔离。"""

from __future__ import annotations

import json
import os
import re

from playwright.sync_api import Route, sync_playwright


BASE_URL = os.environ.get("TONGXIN_BASE_URL", "http://127.0.0.1:5173")


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.set_default_timeout(30000)

        def answer_immediately(route: Route) -> None:
            question = json.loads(route.request.post_data or "{}").get("question", "")
            body = (
                'event: status\ndata: {"status":"generating"}\n\n'
                f'event: token\ndata: {json.dumps({"text": f"{question}的测试回答"}, ensure_ascii=False)}\n\n'
                'event: final\ndata: {"message_id":"msg_test","citations":[],"related_entities":[],"uncertainty":"low","status":"DONE","response_tier":"live_rag","message":null}\n\n'
            )
            route.fulfill(status=200, content_type="text/event-stream", body=body)

        page.route("**/api/v1/chat/messages", answer_immediately)
        page.goto(f"{BASE_URL}/chapter/yuan/chat", wait_until="networkidle")

        def switch_to_chat(slug: str, era: str) -> None:
            page.get_by_role("link", name="同心千年", exact=True).click()
            page.wait_for_url("**/timeline")
            page.locator(f'article[data-era="{slug}"] .era__link').click()
            page.wait_for_url(re.compile(rf"/chapter/{re.escape(slug)}(?:/intro)?$"))
            if page.url.endswith("/intro"):
                page.get_by_role("button", name="接受身份").click()
                page.wait_for_url(f"**/chapter/{slug}")
            page.get_by_role("button", name=re.compile("AI 助手问答")).click()
            page.wait_for_url(f"**/chapter/{slug}/chat")
            page.get_by_text(era, exact=True).wait_for()
            page.locator(".chat__input").wait_for()

        yuan_question = "只属于元代章节的问题"
        tang_question = "只属于唐代章节的问题"

        page.locator(".chat__input").fill(yuan_question)
        page.get_by_role("button", name="发送", exact=True).click()
        page.get_by_text(yuan_question, exact=True).wait_for()

        switch_to_chat("tang", "唐代")
        assert page.get_by_text(yuan_question, exact=True).count() == 0

        page.locator(".chat__input").fill(tang_question)
        page.get_by_role("button", name="发送", exact=True).click()
        page.get_by_text(tang_question, exact=True).wait_for()

        switch_to_chat("yuan", "元代")

        assert page.get_by_text(yuan_question, exact=True).count() == 1
        assert page.get_by_text(tang_question, exact=True).count() == 0

        print("CHAPTER_CHAT_ISOLATION", "PASS")
        browser.close()


if __name__ == "__main__":
    main()
