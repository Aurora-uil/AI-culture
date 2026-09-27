from pathlib import Path
import json
import os
import sys

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[2]
SCREENSHOTS = ROOT / "docs" / "screenshots"
SCREENSHOTS.mkdir(parents=True, exist_ok=True)
BASE_URL = os.environ.get("TONGXIN_BASE_URL", "http://127.0.0.1:5173")

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


GAME_STATE = {
    "yuan": {
        "started": True,
        "completed": True,
        "actions": {
            "ENTER": True,
            "INSPECT": True,
            "LENS": True,
            "DECISION": True,
            "COMPLETE": True,
        },
        "evidenceIds": ["script_sanskrit_lantsa", "script_tibetan", "script_phagspa"],
        "decisionId": "leave_pending",
        "methods": {"truth": 2, "empathy": 0, "connection": 0},
        "updatedAt": "2026-09-23T13:49:28.556Z",
    }
}


def main() -> None:
    pages = [
        ("home", "/", "六段人生"),
        ("timeline", "/timeline", "选择一段身份"),
        ("yuan-intro", "/chapter/yuan/intro", "石壁上的六种声音"),
        ("yuan-guide", "/chapter/yuan", "你的任务"),
        ("yuan-scene", "/chapter/yuan/scene", "当前任务"),
        ("tang-scene", "/chapter/tang/scene", "当前任务"),
        ("wei-scene", "/chapter/northern-wei/scene", "当前任务"),
        ("yuan-ending", "/chapter/yuan/summary", "共存之结"),
        ("journey", "/journey", "我的千年史册"),
    ]

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        state_json = json.dumps(GAME_STATE, ensure_ascii=False)
        context.add_init_script(
            script=f"localStorage.setItem('tongxin.game.v2', JSON.stringify({state_json}))"
        )
        page = context.new_page()
        results = []

        for name, path, marker in pages:
            page.goto(f"{BASE_URL}{path}", wait_until="networkidle")
            page.get_by_text(marker, exact=False).first.wait_for()
            page.wait_for_timeout(1400 if name == "home" else 450)
            metrics = page.evaluate(
                """() => ({
                    viewport: window.innerHeight,
                    document: document.documentElement.scrollHeight,
                    body: document.body.scrollHeight,
                    overflow: Math.max(document.documentElement.scrollHeight, document.body.scrollHeight) - window.innerHeight,
                    boxes: Array.from(document.querySelectorAll('.g-header,.cs,.ch-progress,.game-scene-page')).map(el => ({
                        className: el.className,
                        height: Math.round(el.getBoundingClientRect().height),
                        top: Math.round(el.getBoundingClientRect().top),
                        cssHeight: getComputedStyle(el).height
                    }))
                })"""
            )
            results.append((name, metrics))
            page.screenshot(path=str(SCREENSHOTS / f"v5-{name}.png"), full_page=True)
            if name == "timeline":
                page.locator(".era--recommended .era__link").hover()
                page.wait_for_timeout(320)
                page.screenshot(path=str(SCREENSHOTS / "v5-timeline-hover.png"), full_page=True)

        browser.close()

    failed = []
    for name, metrics in results:
        print(name, json.dumps(metrics, ensure_ascii=False))
        if metrics["overflow"] > 2:
            failed.append(f"{name}: +{metrics['overflow']}px")
    if failed:
        raise AssertionError("桌面页面仍发生整页滚动：" + ", ".join(failed))


if __name__ == "__main__":
    main()
