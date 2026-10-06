"""元代云台六体文字热点的页面坐标回归测试。"""

from __future__ import annotations

import os

from playwright.sync_api import sync_playwright


BASE_URL = os.environ.get("TONGXIN_BASE_URL", "http://127.0.0.1:5173")

EXPECTED_CENTERS = {
    "梵文书写系统": (50.0, 30.25),
    "藏文": (50.0, 43.25),
    "八思巴文": (13.5, 71.5),
    "回鹘文": (36.75, 71.5),
    "西夏文": (61.25, 71.5),
    "汉文": (86.0, 71.5),
}


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        # 旧调试坐标不得覆盖已校准的新版本坐标。
        context.add_init_script(
            "localStorage.setItem('tongxin.yuan.hotspots.debug.v1', "
            "JSON.stringify({hs_script_tibetan:[[0.1,0.1],[0.2,0.1],[0.2,0.2],[0.1,0.2]]}))"
        )
        page = context.new_page()
        page.goto(f"{BASE_URL}/chapter/yuan/scene", wait_until="networkidle")

        layer = page.locator(".scene__hotspots")
        layer.wait_for()
        for label, (expected_left, expected_top) in EXPECTED_CENTERS.items():
            hotspot = layer.locator(f'[aria-label^="{label}"]')
            hotspot.wait_for()
            position = hotspot.evaluate(
                "el => ({left: parseFloat(el.style.left), top: parseFloat(el.style.top)})"
            )
            assert abs(position["left"] - expected_left) < 0.01, (label, position)
            assert abs(position["top"] - expected_top) < 0.01, (label, position)

        print("YUAN_HOTSPOT_LAYOUT", "PASS")
        browser.close()


if __name__ == "__main__":
    main()
