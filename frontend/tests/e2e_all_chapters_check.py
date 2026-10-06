from __future__ import annotations

import os
import sys
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


BASE_URL = os.environ.get("TONGXIN_BASE_URL", "http://127.0.0.1:5173")
ROOT = Path(__file__).resolve().parents[2]
SCREENSHOTS = ROOT / "docs" / "screenshots"
SCREENSHOTS.mkdir(parents=True, exist_ok=True)

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


CHAPTERS = {
    "han": ("路线证据透镜", ".hs"),
    "northern-wei": ("文化证据对照尺", ".wei__card-actions .wei__act:first-child"),
    "tang": ("画内 / 画外透镜", ".hs"),
    "yuan": ("六体文字透镜", ".ys__tag"),
    "qing": ("路线精度透镜", ".qm__node"),
    "contemporary": ("来源与权利透镜", ".wk__card"),
}


def close_entity_drawer(page: Page) -> None:
    close = page.locator(".ds-drawer__close:visible")
    if close.count():
        close.last.click()
        page.locator(".ds-drawer:visible").wait_for(state="hidden")


def click_evidence(page: Page, selector: str, index: int) -> None:
    candidates = page.locator(f"{selector}:visible")
    if candidates.count() <= index:
        raise AssertionError(f"{selector} only has {candidates.count()} visible items")
    target = candidates.nth(index)
    target.evaluate("el => el.click()")
    page.wait_for_timeout(120)
    close_entity_drawer(page)


def run_chapter(page: Page, slug: str, lens_label: str, selector: str) -> None:
    page.goto(f"{BASE_URL}/chapter/{slug}/intro", wait_until="networkidle")
    page.get_by_role("button", name="接受身份").click()
    page.wait_for_url(f"**/chapter/{slug}")
    if slug == "yuan":
        # 元代完整 12 幕剧情另有专门回归；这里继续覆盖共用场景任务骨架。
        page.goto(f"{BASE_URL}/chapter/yuan/scene?module=story", wait_until="networkidle")
    else:
        page.locator(".briefing__module").nth(2).click()
    page.wait_for_url(f"**/chapter/{slug}/scene?module=story")
    page.locator(".cs__stage").wait_for()

    page.get_by_role("button", name=lens_label).click()
    assert page.get_by_role("button", name=lens_label).get_attribute("class").find("is-on") >= 0
    page.locator(f"{selector}:visible").first.wait_for()

    # 收起任务卷，避免遮住地图左侧节点；取证后再打开。
    handle = page.locator(".quest__handle")
    if handle.get_attribute("aria-expanded") == "true":
        handle.evaluate("el => el.click()")

    for index in range(3):
        click_evidence(page, selector, index)

    if handle.get_attribute("aria-expanded") != "true":
        handle.evaluate("el => el.click()")
    decision = page.locator(".quest__decision")
    decision.wait_for()
    if decision.is_disabled():
        debug_state = page.evaluate("JSON.parse(localStorage.getItem('tongxin.game.v2'))")
        raise AssertionError(
            f"{slug}: decision is still locked after 3 evidence items and lens: {debug_state.get(slug)}"
        )
    decision.click()
    page.locator(".decision__choices button").first.click()
    page.locator(".choice-result").wait_for()
    page.locator(".choice-result").wait_for(state="hidden", timeout=5000)
    if slug == "yuan":
        page.get_by_role("button", name="返回任务大厅", exact=True).click()
        page.wait_for_url("**/chapter/yuan")
        page.locator(".briefing__modules").wait_for()
    else:
        page.get_by_role("button", name="整理本章记录").click()
        page.wait_for_url(f"**/chapter/{slug}/summary")
        page.locator(".ending").wait_for()

    state = page.evaluate("JSON.parse(localStorage.getItem('tongxin.game.v2'))")
    assert state[slug]["decisionId"], f"{slug}: choice was not persisted"
    assert len(state[slug]["evidenceIds"]) >= 3, f"{slug}: evidence was not persisted"
    assert state[slug]["actions"]["LENS"], f"{slug}: lens action was not persisted"
    if slug != "yuan":
        assert state[slug]["completed"], f"{slug}: summary did not complete chapter"
    page.screenshot(path=str(SCREENSHOTS / f"v6-{slug}-summary.png"), full_page=True)
    print(slug, "PASS", state[slug]["decisionId"], len(state[slug]["evidenceIds"]))


def run_cocreation(page: Page) -> None:
    page.goto(f"{BASE_URL}/chapter/contemporary/create", wait_until="networkidle")
    page.locator(".co__card:visible").first.wait_for()
    page.locator(".co__card:visible").first.click()
    page.get_by_role("button", name="下一步").click()
    page.locator(".co__option:visible").first.click()
    page.get_by_role("button", name="下一步").click()
    page.locator(".co__option--card:visible").first.click()
    page.get_by_role("button", name="下一步").click()
    page.locator(".co__checkbox input").check()
    page.get_by_role("button", name="下一步").click()
    page.get_by_role("button", name="开始生成").click()
    result = page.locator(".co__result")
    result.wait_for()
    assert "非传统羌绣原作" in result.inner_text()
    assert "非本次实时生成" in result.inner_text()
    image = result.locator("img")
    assert image.get_attribute("src") == "/assets/contemporary/cocreation-sample-v1.png"
    assert image.evaluate("img => img.naturalWidth") > 0
    page.screenshot(path=str(SCREENSHOTS / "v6-contemporary-cocreation.png"), full_page=True)
    print("contemporary-cocreation PASS controlled-offline-sample-v1")


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page.set_default_timeout(8000)
        page.goto(BASE_URL, wait_until="domcontentloaded")
        page.evaluate("localStorage.removeItem('tongxin.game.v2')")
        for slug, (lens_label, selector) in CHAPTERS.items():
            run_chapter(page, slug, lens_label, selector)
        run_cocreation(page)
        browser.close()


if __name__ == "__main__":
    main()
