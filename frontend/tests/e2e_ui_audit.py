from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[2]
SHOT_DIR = ROOT / "docs" / "screenshots" / "ui-commercial-pass"
SHOT_DIR.mkdir(parents=True, exist_ok=True)


def capture(page, name: str) -> None:
    page.wait_for_timeout(900)
    page.screenshot(path=str(SHOT_DIR / name), full_page=True)


def click_dialogue(page) -> None:
    box = page.locator('.dialogue-panel').bounding_box()
    assert box
    page.mouse.click(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
    page.wait_for_timeout(120)


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)

    page.goto("http://127.0.0.1:5173/", wait_until="networkidle")
    assert page.locator('.splash h1').is_visible()
    capture(page, "01-splash-after.png")

    page.goto("http://127.0.0.1:5173/timeline", wait_until="networkidle")
    capture(page, "02-timeline-after.png")

    page.goto("http://127.0.0.1:5173/chapter/han/intro", wait_until="networkidle")
    capture(page, "03-intro-after.png")

    page.goto("http://127.0.0.1:5173/chapter/han/story", wait_until="networkidle")
    page.evaluate("localStorage.removeItem('tongxin.han.story.v1')")
    page.reload(wait_until="networkidle")
    capture(page, "04-story-dialogue-after.png")
    page.locator('.story-nav__reading').nth(0).click()
    assert page.locator('.chapter-story').evaluate("el => el.classList.contains('is-large-text')")
    assert page.evaluate("localStorage.getItem('tongxin.reading.largeText')") == '1'
    page.locator('.story-nav__reading').nth(0).click()

    # 阅读字号与音效都属于跨章节偏好；切换后应写入同一个全局设置。
    page.locator('.story-nav__reading').nth(1).click()
    assert page.evaluate("localStorage.getItem('tongxin.sound')") == 'off'
    page.locator('.story-nav__reading').nth(1).click()
    assert page.evaluate("localStorage.getItem('tongxin.sound')") == 'on'

    click_dialogue(page)
    click_dialogue(page)
    page.wait_for_selector(".evidence-workbench")
    capture(page, "05-story-workbench-after.png")

    mobile = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=1)
    mobile.goto("http://127.0.0.1:5173/chapter/contemporary/story", wait_until="networkidle")
    mobile.evaluate("localStorage.removeItem('tongxin.contemporary.story.v1')")
    mobile.reload(wait_until="networkidle")
    capture(mobile, "06-story-mobile-after.png")

    assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")
    assert mobile.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")

    compact = browser.new_page(viewport={"width": 1366, "height": 768}, device_scale_factor=1)
    compact.goto("http://127.0.0.1:5173/chapter/yuan/story", wait_until="networkidle")
    compact.evaluate("localStorage.removeItem('tongxin.yuan.story.v6')")
    compact.reload(wait_until="networkidle")
    compact.wait_for_selector('.dialogue-panel')
    assert compact.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    assert compact.evaluate("document.documentElement.scrollHeight <= window.innerHeight")
    capture(compact, "07-yuan-1366-after.png")
    compact.close()
    browser.close()

print(f"UI audit screenshots written to {SHOT_DIR}")
