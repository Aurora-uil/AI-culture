"""元代 V6.0 剧情章完整路径与存档冒烟测试。"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


BASE_URL = os.environ.get("TONGXIN_BASE_URL", "http://127.0.0.1:5173")
SCREENSHOT = Path(tempfile.gettempdir()) / "tongxin-yuan-story-ending.png"
CHARACTER_SCREENSHOT = Path(tempfile.gettempdir()) / "tongxin-yuan-story-character.png"
MINIGAME_SCREENSHOT = Path(tempfile.gettempdir()) / "tongxin-yuan-story-minigame.png"
MOBILE_MINIGAME_SCREENSHOT = Path(tempfile.gettempdir()) / "tongxin-yuan-story-minigame-mobile.png"
TRANSITION_SCREENSHOT = Path(tempfile.gettempdir()) / "tongxin-yuan-scene-transition.png"
SEEN_BACKGROUNDS: set[str] = set()
SEEN_FRAMINGS: set[str] = set()


def finish_dialogue(page: Page) -> None:
    for _ in range(12):
        cue = page.locator(".dialogue-cue span")
        cue.wait_for()
        if cue.inner_text() != "点击对话框继续":
            return
        page.locator(".dialogue-panel").click()
    raise AssertionError("对白推进超过预期步数")


def continue_story(page: Page) -> None:
    cue = page.locator(".dialogue-cue span")
    cue.wait_for()
    assert cue.inner_text() in {"点击继续剧情", "点击进入证据剧场"}, "当前调查尚未满足推进条件"
    page.locator(".dialogue-panel").click()
    page.locator(".scene-transition").wait_for(state="hidden", timeout=2000)


def assert_scene(page: Page, scene_id: str, title: str) -> None:
    display_index = str(int(scene_id) + 1).zfill(2)
    page.get_by_text(f"SCENE {display_index} / 12", exact=True).wait_for()
    page.locator(".scene-heading").get_by_role("heading", name=title, exact=True).wait_for()
    assert page.locator(".scene-heading span, .scene-heading small").count() == 0
    background = page.locator(".story-backdrop__main").get_attribute("src")
    stage_class = page.locator(".story-stage").get_attribute("class") or ""
    if background:
        SEEN_BACKGROUNDS.add(background)
    for class_name in stage_class.split():
        if class_name.startswith("framing-"):
            SEEN_FRAMINGS.add(class_name)


def assert_single_screen(page: Page) -> None:
    page.evaluate("window.scrollTo(0, 99999)")
    assert page.evaluate("window.scrollY === 0"), "剧情页面仍可纵向滚动"
    workbench = page.locator(".workbench")
    if workbench.count():
        assert workbench.evaluate("el => el.scrollHeight <= el.clientHeight + 1"), "玩法面板出现纵向滚动"


def main() -> None:
    console_errors: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
        page.goto(f"{BASE_URL}/chapter/yuan/story", wait_until="networkidle")
        page.evaluate("localStorage.removeItem('tongxin.yuan.story.v6')")
        page.reload(wait_until="networkidle")

        assert_scene(page, "00", "第七块")
        finish_dialogue(page)
        page.locator(".dialogue-panel").click()
        page.locator(".scene-transition").wait_for(state="visible")
        page.wait_for_timeout(180)
        page.screenshot(path=str(TRANSITION_SCREENSHOT), full_page=True)
        page.locator(".scene-transition").wait_for(state="hidden", timeout=2000)

        assert_scene(page, "01", "两份都对不上")
        page.wait_for_timeout(1000)
        page.screenshot(path=str(CHARACTER_SCREENSHOT), full_page=True)
        finish_dialogue(page)
        page.locator(".compare-game").wait_for()
        page.wait_for_timeout(350)
        page.screenshot(path=str(MINIGAME_SCREENSHOT), full_page=True)
        assert_single_screen(page)
        for answer in ["相同", "不同", "无法确认"]:
            page.locator(".verdict-deck").get_by_role("button", name=answer, exact=True).click()
        page.get_by_role("button", name="合拢证据，提交推断", exact=True).click()
        continue_story(page)

        assert_scene(page, "02", "最方便的一版")
        finish_dialogue(page)
        for button in page.locator(".relay-pool button").all():
            button.click()
        page.get_by_role("button", name="核对工序链", exact=True).click()
        assert_single_screen(page)
        continue_story(page)

        assert_scene(page, "03", "一份更整齐的石壁")
        finish_dialogue(page)
        for answer in ["统一定位", "保留组块", "保持原向"]:
            page.get_by_role("button", name=answer, exact=True).click()
        page.get_by_role("button", name="压印校准结果", exact=True).click()
        assert_single_screen(page)
        continue_story(page)

        assert_scene(page, "04", "雨水")
        finish_dialogue(page)
        for answer in ["可连接", "只能部分连接", "不能连接"]:
            page.locator(".relation-options").get_by_role("button", name=answer, exact=True).click()
        page.get_by_role("button", name="审查整条关系链", exact=True).click()
        page.get_by_role("button", name="记录嫌疑，但暂不归责").click()
        assert_single_screen(page)
        continue_story(page)

        assert_scene(page, "05", "不是谁把它放错了")
        finish_dialogue(page)
        page.get_by_role("slider", name="移动结构校样").fill("50")
        page.get_by_role("button", name="固定重合点").click()
        assert_single_screen(page)
        continue_story(page)

        assert_scene(page, "06", "共同的规矩")
        finish_dialogue(page)
        for label in ["必须一致", "必须一致", "需要协调", "需要协调", "必须保留", "必须保留"]:
            page.locator(".rule-options").get_by_role("button", name=label, exact=False).click()
        page.get_by_role("button", name="核验规则权限", exact=True).click()
        assert page.locator(".game-resolution").get_by_text("矩阵闭合", exact=False).is_visible()
        assert_single_screen(page)

        # 本章关键玩法必须支持刷新恢复，避免长剧情意外丢失。
        page.reload(wait_until="networkidle")
        assert_scene(page, "06", "共同的规矩")
        assert page.locator(".rule-tabs button.done").count() == 6
        continue_story(page)

        assert_scene(page, "07", "六种文字，多少种人")
        finish_dialogue(page)
        assert_single_screen(page)
        for inference in ["证据支持", "不能推出", "部分确认"]:
            page.locator(".people-options").get_by_role("button", name=inference, exact=False).click()
        page.get_by_role("button", name="审查三条推断", exact=True).click()
        page.get_by_role("button", name="不能直接对应", exact=False).click()
        continue_story(page)

        assert_scene(page, "08", "今天到底按什么做")
        finish_dialogue(page)
        assert_single_screen(page)
        for deduction in [
            "两份校样可能承担不同阶段功能",
            "统一外框定位，保留内部结构",
            "版本确切先后，以及文字对应哪些人群",
        ]:
            page.get_by_role("button", name=deduction, exact=False).click()
        page.get_by_role("button", name="压印整条裁决链", exact=True).click()
        page.get_by_role("button", name="有限确认，并保留两份版本", exact=False).click()
        continue_story(page)

        assert_scene(page, "09", "门洞")
        finish_dialogue(page)
        assert_single_screen(page)
        continue_story(page)

        assert_scene(page, "10", "回到当代")
        finish_dialogue(page)
        answers = ["证据支持", "不能推出", "部分确认", "不能推出"]
        for answer in answers:
            page.locator(".archive-card").get_by_role("button", name=answer, exact=True).click()
        page.get_by_role("button", name="作为版本证据保留", exact=True).click()
        assert page.get_by_text("居庸关云台题刻中", exact=False).is_visible()
        assert_single_screen(page)
        continue_story(page)

        assert_scene(page, "11", "证据关系图")
        finish_dialogue(page)
        assert_single_screen(page)
        page.wait_for_timeout(500)
        page.screenshot(path=str(SCREENSHOT), full_page=True)
        page.locator(".dialogue-panel").click()
        page.wait_for_url("**/chapter/yuan/summary")
        page.get_by_text("共存之结", exact=True).wait_for()
        page.get_by_text("有限确认，并保留两份版本", exact=True).wait_for()
        page.get_by_text("有限确认 · 协作继续", exact=True).wait_for()
        page.get_by_text("旧版可继续复核", exact=False).wait_for()
        assert page.get_by_role("button", name="重开元代篇 · 尝试另一条路线", exact=True).is_visible()

        assert len(SEEN_FRAMINGS) == 12, f"场景镜头不足: {sorted(SEEN_FRAMINGS)}"
        # 六套底图经过前、中、后景叠加、镜头裁切和色调变化，组成十二种独立构图。
        assert len(SEEN_BACKGROUNDS) >= 6, f"独立背景基底不足: {sorted(SEEN_BACKGROUNDS)}"

        # 独立启动前端时，结章页的可选后端摘要接口会由 Vite 返回 500；
        # 这不影响剧情主流程。仍然拦截其余脚本与 Vue 运行时错误。
        fatal_errors = [
            error for error in console_errors
            if not error.startswith("Failed to load resource")
        ]
        assert not fatal_errors, f"浏览器控制台脚本错误: {fatal_errors}"

        mobile = browser.new_page(viewport={"width": 390, "height": 844})
        mobile.goto(f"{BASE_URL}/chapter/yuan/story", wait_until="networkidle")
        mobile.evaluate(
            "localStorage.setItem('tongxin.yuan.story.v6', JSON.stringify({ sceneIndex: 1, dialogueStep: 3 }))"
        )
        mobile.reload(wait_until="networkidle")
        mobile.locator(".compare-game").wait_for()
        assert mobile.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        assert_single_screen(mobile)
        mobile.screenshot(path=str(MOBILE_MINIGAME_SCREENSHOT), full_page=True)
        for scene_index in range(12):
            mobile.evaluate(
                "state => localStorage.setItem('tongxin.yuan.story.v6', JSON.stringify(state))",
                {"sceneIndex": scene_index, "dialogueStep": 99},
            )
            mobile.reload(wait_until="networkidle")
            mobile.locator(".workbench").wait_for()
            assert_single_screen(mobile)
        mobile.close()

        print("OPTIONAL_API_ERRORS", len(console_errors) - len(fatal_errors))
        print("YUAN_STORY_SCENES", 12)
        print("YUAN_STORY_FRAMINGS", len(SEEN_FRAMINGS))
        print("YUAN_STORY_BACKGROUNDS", len(SEEN_BACKGROUNDS))
        print("YUAN_STORY_ENDING", SCREENSHOT)
        print("YUAN_STORY_CHARACTER", CHARACTER_SCREENSHOT)
        print("YUAN_STORY_MINIGAME", MINIGAME_SCREENSHOT)
        print("YUAN_STORY_MINIGAME_MOBILE", MOBILE_MINIGAME_SCREENSHOT)
        print("YUAN_STORY_TRANSITION", TRANSITION_SCREENSHOT)
        browser.close()


if __name__ == "__main__":
    main()
