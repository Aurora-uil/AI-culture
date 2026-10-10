import json
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[2]
SHOT_DIR = ROOT / "docs" / "screenshots" / "ui-commercial-pass"
SHOT_DIR.mkdir(parents=True, exist_ok=True)
BASE_URL = "http://127.0.0.1:5173"

HAN_STATE = {
    "han": {
        "started": True,
        "completed": True,
        "actions": {
            "ENTER": True,
            "INSPECT": True,
            "LENS": True,
            "DECISION": True,
            "CHAT": True,
            "GRAPH": True,
            "COMPLETE": True,
        },
        "evidenceIds": ["han_caption_split", "han_chronology_gap", "han_dual_route"],
        "decisionId": "ask_travellers",
        "methods": {"truth": 1, "empathy": 0, "connection": 2},
        "updatedAt": "2026-10-09T08:00:00.000Z",
    }
}


def capture(page, name: str) -> None:
    page.wait_for_timeout(700)
    page.screenshot(path=str(SHOT_DIR / name), full_page=True)


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto(BASE_URL, wait_until="networkidle")
    page.evaluate(
        "value => localStorage.setItem('tongxin.game.v2', value)",
        json.dumps(HAN_STATE, ensure_ascii=False),
    )
    page.reload(wait_until="networkidle")
    assert page.locator(".splash__resume").is_visible()
    assert "未定之路" in page.locator(".splash__enter").inner_text()
    capture(page, "09-splash-resume-round3.png")

    page.goto(f"{BASE_URL}/chapter/han/summary", wait_until="networkidle")
    page.wait_for_selector(".ending__routes")
    assert page.locator(".ending__routes article").count() == 3
    assert page.locator(".ending__routes article.is-chosen").count() == 1
    capture(page, "10-summary-routes-round3.png")

    page.goto(f"{BASE_URL}/chapter/han/chat", wait_until="networkidle")
    page.wait_for_selector(".cc__identity")
    capture(page, "11-chat-archive-round3.png")

    page.goto(f"{BASE_URL}/chapter/han/graph", wait_until="networkidle")
    page.wait_for_selector(".cg__identity")
    capture(page, "12-graph-archive-round3.png")

    page.goto(f"{BASE_URL}/chapter/contemporary/create", wait_until="networkidle")
    page.wait_for_selector(".co__eyebrow")
    capture(page, "13-cocreation-ledger-round3.png")
    assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")

    decision = browser.new_page(viewport={"width": 1440, "height": 900})
    decision.goto(f"{BASE_URL}/chapter/han/story", wait_until="networkidle")
    decision.evaluate(
        """() => {
          localStorage.setItem('tongxin.game.v2', JSON.stringify({
            han: { started: true, completed: false, actions: { ENTER: true, INSPECT: true, LENS: true }, evidenceIds: [], decisionId: null, methods: { truth: 0, empathy: 0, connection: 0 }, updatedAt: new Date().toISOString() }
          }))
          localStorage.setItem('tongxin.han.story.v1', JSON.stringify({
            sceneIndex: 7, dialogueStep: 1, completedScenes: ['00','01','02','03','04','05','06'], inspected: {}, answers: {}, classifications: {}, assemblies: {}, decisionId: null, interludesSeen: ['02','05'], revisionCount: 2
          }))
        }"""
    )
    decision.reload(wait_until="networkidle")
    decision.wait_for_selector(".decision-grid")
    assert decision.locator(".decision-card__tradeoff").count() == 3
    decision.get_by_role("button", name="改写为长期网络物证", exact=False).click()
    assert decision.get_by_role("button", name="确认承担这条路线的后果").is_enabled()
    capture(decision, "15-final-tradeoff-round4.png")
    decision.close()

    mobile = browser.new_page(viewport={"width": 390, "height": 844})
    mobile.goto(f"{BASE_URL}/chapter/han/story", wait_until="networkidle")
    assert mobile.locator(".story-nav__tools button").count() == 3
    assert mobile.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    capture(mobile, "14-story-mobile-tools-round3.png")
    mobile.close()
    browser.close()

print(f"Round 3 UI screenshots written to {SHOT_DIR}")
