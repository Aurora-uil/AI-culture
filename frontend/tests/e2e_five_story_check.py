from pathlib import Path
import re
from playwright.sync_api import sync_playwright, expect


BASE = "http://127.0.0.1:5173"
ROOT = Path(__file__).resolve().parents[2]
SCREENSHOTS = ROOT / "docs" / "screenshots"
SCREENSHOTS.mkdir(parents=True, exist_ok=True)
INTERLUDE_SCREENSHOT = SCREENSHOTS / "ui-commercial-pass" / "08-han-interlude-after.png"
INTERLUDE_SCREENSHOT.parent.mkdir(parents=True, exist_ok=True)
interlude_screenshot_written = False


def advance_dialogue(page):
    panel = page.locator(".dialogue-panel")
    for _ in range(14):
        if page.locator(".evidence-workbench").is_visible():
            return
        text_box = panel.locator(".dialogue-panel__text")
        metrics = text_box.evaluate("el => ({client: el.clientHeight, scroll: el.scrollHeight})")
        assert metrics["scroll"] <= metrics["client"] + 1, metrics
        box = panel.locator(".dialogue-panel__cue").bounding_box()
        assert box
        page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        page.wait_for_timeout(80)
    raise AssertionError("dialogue did not reveal the workbench")


def next_scene(page, expected_title):
    global interlude_screenshot_written
    panel = page.locator(".dialogue-panel")
    box = panel.locator(".dialogue-panel__cue").bounding_box()
    assert box
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.wait_for_timeout(120)
    interlude = page.locator('.chapter-interlude')
    if interlude.is_visible():
        if not interlude_screenshot_written:
            page.wait_for_timeout(420)
            page.screenshot(path=INTERLUDE_SCREENSHOT, full_page=True)
            interlude_screenshot_written = True
        interlude.get_by_role('button').click()
    page.wait_for_timeout(520)
    expect(page.locator(".story-heading h1")).to_have_text(expected_title)


def click_all_inspect_cards(page):
    cards = page.locator(".inspect-grid > button")
    for index in range(cards.count()):
        cards.nth(index).click()
    expect(page.locator(".dialogue-panel")).to_have_class(re.compile(r"\bis-ready\b"))


def choose_options(page, labels):
    workbench = page.locator(".evidence-workbench")
    for label in labels:
        workbench.get_by_role("button", name=label, exact=False).click()
    workbench.get_by_role("button", name="核验判断").click()


def assign_class(page, card_label, bin_label):
    cards = page.locator(".classify-card")
    card = None
    for index in range(cards.count()):
        candidate = cards.nth(index)
        if candidate.locator("strong").first.inner_text() == card_label:
            card = candidate
            break
    assert card is not None, card_label
    card.get_by_role("button", name=bin_label, exact=True).click()


def choose_slot(page, slot_label, option_label):
    slot = page.locator(".assemble-slot").filter(has_text=slot_label)
    slot.get_by_role("button", name=option_label, exact=False).click()


def assert_no_page_scroll(page):
    metrics = page.evaluate("""() => ({
      innerHeight: window.innerHeight,
      body: document.body.scrollHeight,
      html: document.documentElement.scrollHeight
    })""")
    assert metrics["body"] <= metrics["innerHeight"] + 1, metrics
    assert metrics["html"] <= metrics["innerHeight"] + 1, metrics


def smoke_chapters(browser):
    titles = {
        "han": ("一个人能走出一条路吗", "两只时间盒"),
        "northern-wei": ("空白墓石", "墓志先认识一个人"),
        "tang": ("名册上只有“吐蕃使臣”", "一个名字怎样走出画框"),
        "qing": ("河岸名册少了一户", "先发一碗粮，还是先补一个名字"),
        "contemporary": ("旧箱子上写着“受助作品”", "援助名单背面，还有交活和结算"),
    }
    for slug, (first, second) in titles.items():
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(f"{BASE}/chapter/{slug}/story")
        page.wait_for_load_state("networkidle")
        page.evaluate("localStorage.clear()")
        page.reload(wait_until="networkidle")
        page.wait_for_selector(".story-heading h1", timeout=15000)
        expect(page.locator(".story-heading h1")).to_have_text(first)
        expect(page.locator(".story-nav__progress")).to_contain_text("第一幕 · 第 01 场")
        advance_dialogue(page)
        click_all_inspect_cards(page)
        assert_no_page_scroll(page)
        if slug == "han":
            page.screenshot(path=SCREENSHOTS / "v15-han-story-first-scene.png", full_page=True)
        next_scene(page, second)
        page.close()


def full_han(browser):
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto(f"{BASE}/chapter/han/story")
    page.wait_for_load_state("networkidle")
    page.evaluate("localStorage.clear()")
    page.reload(wait_until="networkidle")
    page.wait_for_selector(".story-heading h1", timeout=15000)

    # 00 inspect
    advance_dialogue(page)
    click_all_inspect_cards(page)
    next_scene(page, "两只时间盒")

    # 01 single
    advance_dialogue(page)
    choose_options(page, ["张骞携带过锦护膊"])
    expect(page.locator(".story-feedback")).to_contain_text("不能自动生成")
    choose_options(page, ["两者可进入同一段长期交通史"])
    next_scene(page, "一条路，两张图")

    # 02 classify
    advance_dialogue(page)
    assign_class(page, "长安", "两层都可见")
    assign_class(page, "西域", "两层都可见")
    assign_class(page, "尼雅遗址", "长期网络节点")
    assign_class(page, "长安—西域示意连接", "出使相关节点")
    page.get_by_role("button", name="统一核验分层").click()
    page.screenshot(path=SCREENSHOTS / "v15-han-story-route-layers.png", full_page=True)
    next_scene(page, "尼雅不是道具")

    # 03 inspect
    advance_dialogue(page)
    click_all_inspect_cards(page)
    next_scene(page, "一个人的行囊装不下网络")

    # 04 multi
    advance_dialogue(page)
    choose_options(page, ["人员流动包含多类参与者", "路线与联系在长期中变化"])
    next_scene(page, "关系不是只有“有”或“没有”")

    # 05 classify
    advance_dialogue(page)
    assign_class(page, "张骞—第一次出使", "直接支持")
    assign_class(page, "尼雅—丝路交通网络", "长期联系")
    assign_class(page, "张骞—锦护膊", "不支持直连")
    page.get_by_role("button", name="统一核验分层").click()
    next_scene(page, "三句话的展签")

    # 06 assemble
    advance_dialogue(page)
    choose_slot(page, "确认事实", "1995年出土于尼雅遗址M8")
    choose_slot(page, "形成联系", "作为后世长期交通网络中的物质遗存")
    choose_slot(page, "保留未知", "现有资料不支持它与张骞存在直接关系")
    page.get_by_role("button", name="核验完整结论").click()
    next_scene(page, "应该记住谁")

    # 07 final
    advance_dialogue(page)
    page.get_by_role("button", name="改写为长期网络物证", exact=False).click()
    expect(page.get_by_role("button", name="确认承担这条路线的后果")).to_be_enabled()
    page.get_by_role("button", name="确认承担这条路线的后果").click()
    next_scene(page, "路上重新有了人")

    # 08 branch ending + 09 thematic coda. Dialogue length changes as the
    # story is refined, so advance through dialogue and interludes dynamically.
    for _ in range(20):
        if "/chapter/han/summary" in page.url:
            break
        interlude = page.locator(".chapter-interlude")
        if interlude.is_visible():
            interlude.get_by_role("button").click()
            page.wait_for_timeout(420)
            continue
        panel = page.locator(".dialogue-panel")
        box = panel.locator(".dialogue-panel__cue").bounding_box()
        assert box
        page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        page.wait_for_timeout(120)
    page.wait_for_url("**/chapter/han/summary")
    expect(page.locator(".ending__title h1")).to_have_text("相遇之结")
    expect(page.locator(".ending__revision")).to_contain_text("修订 1 次")
    expect(page.locator(".ending__boundaries")).to_contain_text("史料确证")
    expect(page.locator(".ending__boundaries")).to_contain_text("研究解释")
    expect(page.locator(".ending__boundaries")).to_contain_text("尚未确认")
    expect(page.locator(".ending__boundaries")).to_contain_text("剧情虚构")
    summary_metrics = page.evaluate("() => ({inner: innerWidth, body: document.body.scrollWidth})")
    assert summary_metrics["body"] <= summary_metrics["inner"] + 1, summary_metrics
    page.screenshot(path=SCREENSHOTS / "v19-han-role1-summary.png", full_page=True)
    page.close()


def full_qing(browser):
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto(f"{BASE}/chapter/qing/story")
    page.wait_for_load_state("networkidle")
    page.evaluate("localStorage.clear()")
    page.reload(wait_until="networkidle")
    page.wait_for_selector(".story-heading h1", timeout=15000)

    # 00: distinguish verified arrival/relief from the fictional household.
    advance_dialogue(page)
    click_all_inspect_cards(page)
    next_scene(page, "先发一碗粮，还是先补一个名字")

    # 01: aid now while marking the damaged register for verification.
    advance_dialogue(page)
    choose_options(page, ["先按眼前丁口救急"])
    next_scene(page, "为什么我的终点画在承德")

    # 02: migration, audience, and settlement are three different routes.
    advance_dialogue(page)
    assign_class(page, "伏尔加河下游", "大部众迁徙")
    assign_class(page, "伊犁河流域", "大部众迁徙")
    assign_class(page, "承德／热河", "首领赴承德")
    assign_class(page, "新疆相关安置地区", "抵达后安置")
    page.get_by_role("button", name="统一核验分层").click()
    next_scene(page, "三个数字，眼前是四个人")

    # 03: keep the original numerical scopes instead of averaging.
    advance_dialogue(page)
    choose_options(page, ["保留原表述并标明来源与口径"])
    next_scene(page, "为什么一定要向东")

    # 04: multiple historical contexts without inventing one collective mind.
    advance_dialogue(page)
    choose_options(page, ["政治与军事压力", "草场与生存环境", "与清朝的长期联系"])
    next_scene(page, "四方送来的，不只是一批牛羊")

    # 05: relief operates on tonight, livelihood, and settlement timescales.
    advance_dialogue(page)
    assign_class(page, "按口给食、按人授衣", "今夜救急")
    assign_class(page, "调运与采办马牛羊", "恢复生计")
    assign_class(page, "茶米与棉布持续运抵", "恢复生计")
    assign_class(page, "划定水草适宜的安置地", "长久安置")
    page.get_by_role("button", name="统一核验分层").click()
    next_scene(page, "不能让空白替人挨饿")

    # 06: assemble the shared two-page ledger.
    advance_dialogue(page)
    choose_slot(page, "史实依据", "食衣、牲畜与安置均有史料记录")
    choose_slot(page, "受损空白", "眼前丁口先登记救急")
    choose_slot(page, "共同动作", "归来者、书手与赶运人分别提供所知")
    page.get_by_role("button", name="核验完整结论").click()
    next_scene(page, "今夜的粮，明春的路")

    # 07: choose the route that connects immediate aid to long-term rebuilding.
    advance_dialogue(page)
    page.get_by_role("button", name="建立今夜—明春双页责任链", exact=False).click()
    page.get_by_role("button", name="确认承担这条路线的后果").click()
    next_scene(page, "第一锅茶烧起来")

    # 08-09: branch consequence and thematic coda.
    for _ in range(24):
        if "/chapter/qing/summary" in page.url:
            break
        interlude = page.locator(".chapter-interlude")
        if interlude.is_visible():
            interlude.get_by_role("button").click()
            page.wait_for_timeout(420)
            continue
        text_box = page.locator(".dialogue-panel__text")
        metrics = text_box.evaluate("el => ({client: el.clientHeight, scroll: el.scrollHeight})")
        assert metrics["scroll"] <= metrics["client"] + 1, metrics
        page.locator(".dialogue-panel__cue").click()
        page.wait_for_timeout(140)
    page.wait_for_url("**/chapter/qing/summary")
    expect(page.locator(".ending__title h1")).to_have_text("归属之结")
    expect(page.locator(".ending__choice")).to_contain_text("双页责任链")
    expect(page.locator(".ending__summary")).to_contain_text("今夜接到明春")
    page.screenshot(path=SCREENSHOTS / "v20-qing-shared-ledger-summary.png", full_page=True)
    page.close()


def full_contemporary(browser):
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto(f"{BASE}/chapter/contemporary/story")
    page.wait_for_load_state("networkidle")
    page.evaluate("localStorage.clear()")
    page.reload(wait_until="networkidle")
    page.wait_for_selector(".story-heading h1", timeout=15000)

    # 00: confirm the public facts behind the fictional 2008 archive box.
    advance_dialogue(page)
    click_all_inspect_cards(page)
    next_scene(page, "援助名单背面，还有交活和结算")

    # 01: keep support, local agency, and connecting organizations distinct.
    advance_dialogue(page)
    assign_class(page, "组织培训并提供就业帮扶资源", "公共与社会支援")
    assign_class(page, "当地妇女学习、绣制并逐步参与授艺", "本地主体行动")
    assign_class(page, "帮扶中心、合作社与企业组织验收销售", "协作连接")
    assign_class(page, "各地消费者购买和使用羌绣产品", "协作连接")
    page.get_by_role("button", name="统一核验分层").click()
    next_scene(page, "十几年后，培训表上出现更多来路")

    # 02: confirm a diverse learning network without flattening identities.
    advance_dialogue(page)
    choose_options(page, ["汶川、理县、茂县", "不同省份、不同民族", "教师、学员、设计者和销售者"])
    next_scene(page, "二十四个共创包，不能只装一种声音")

    # 03: choose a round-trip kit rather than distributed coloring of one design.
    advance_dialogue(page)
    choose_options(page, ["署名起针片 + 创作者说明"])
    next_scene(page, "模型把二十多件作品平均成一张")

    # 04: preserve works, limit AI to support, and remove the averaged pattern.
    advance_dialogue(page)
    assign_class(page, "二十四位创作者分别署名的起针片", "保留独立作品")
    assign_class(page, "经本人复核的语音转写与问题索引", "AI辅助往返")
    assign_class(page, "AI生成的统一“同心纹样”", "退出项目")
    assign_class(page, "学校、作者与回件之间的关系地图", "AI辅助往返")
    page.get_by_role("button", name="统一核验分层").click()
    next_scene(page, "一只接针包，要走一个来回")

    # 05: assemble a complete outbound, response, and return loop.
    advance_dialogue(page)
    choose_slot(page, "从工坊出发", "署名起针片、本人说明")
    choose_slot(page, "在远方回应", "用自己的材料回应具体内容")
    choose_slot(page, "回到工坊", "双方分别落款、互相回信")
    page.get_by_role("button", name="核验完整结论").click()
    next_scene(page, "试寄回信没有照着原作绣")

    # 06: describe the two related works without renaming the reply as Qiang embroidery.
    advance_dialogue(page)
    choose_options(page, ["阿若羌绣起针片《山路》"])
    next_scene(page, "二十四只箱子，三种寄法")

    # 07: choose eight complete round trips over copied scale.
    advance_dialogue(page)
    page.get_by_role("button", name="先做八组一对一，十六校延期", exact=False).click()
    page.get_by_role("button", name="确认承担这条路线的后果").click()
    next_scene(page, "寄出的材料，必须有人接回来")

    # 08-09: branch consequence and thematic coda.
    for _ in range(26):
        if "/chapter/contemporary/summary" in page.url:
            break
        interlude = page.locator(".chapter-interlude")
        if interlude.is_visible():
            interlude.get_by_role("button").click()
            page.wait_for_timeout(420)
            continue
        text_box = page.locator(".dialogue-panel__text")
        metrics = text_box.evaluate("el => ({client: el.clientHeight, scroll: el.scrollHeight})")
        assert metrics["scroll"] <= metrics["client"] + 1, metrics
        page.locator(".dialogue-panel__cue").click()
        page.wait_for_timeout(140)
    page.wait_for_url("**/chapter/contemporary/summary")
    expect(page.locator(".ending__title h1")).to_have_text("传承之结")
    expect(page.locator(".ending__choice")).to_contain_text("先做八组一对一")
    expect(page.locator(".ending__summary")).to_contain_text("每条连接的两端都有人")
    page.screenshot(path=SCREENSHOTS / "v22-contemporary-reply-network-summary.png", full_page=True)
    page.close()


def mobile_layout(browser):
    page = browser.new_page(viewport={"width": 390, "height": 844})
    page.goto(f"{BASE}/chapter/contemporary/story")
    page.wait_for_load_state("networkidle")
    page.evaluate("localStorage.clear()")
    page.reload(wait_until="networkidle")
    page.wait_for_selector(".story-heading h1", timeout=15000)
    advance_dialogue(page)
    assert_no_page_scroll(page)
    page.screenshot(path=SCREENSHOTS / "v15-contemporary-story-mobile.png", full_page=True)
    workbench = page.locator(".evidence-workbench")
    box = workbench.bounding_box()
    assert box and box["x"] >= 0 and box["x"] + box["width"] <= 390.5, box
    page.close()


def mobile_qing_layout(browser):
    page = browser.new_page(viewport={"width": 390, "height": 844})
    page.goto(f"{BASE}/chapter/qing/story")
    page.wait_for_load_state("networkidle")
    page.evaluate("localStorage.clear()")
    page.reload(wait_until="networkidle")
    page.wait_for_selector(".story-heading h1", timeout=15000)
    expect(page.locator(".story-heading h1")).to_have_text("河岸名册少了一户")
    advance_dialogue(page)
    assert_no_page_scroll(page)
    page.screenshot(path=SCREENSHOTS / "v20-qing-riverbank-mobile.png", full_page=True)
    workbench = page.locator(".evidence-workbench")
    box = workbench.bounding_box()
    assert box and box["x"] >= 0 and box["x"] + box["width"] <= 390.5, box
    page.close()


def thematic_codas(browser):
    titles = {
        "han": "路从来不是一个人的",
        "northern-wei": "一方石上，两座故乡",
        "tang": "画卷只画下相见",
        "qing": "长路被许多双手接住",
        "contemporary": "关系图没有生成一朵“共同的花”",
    }
    for slug, title in titles.items():
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(f"{BASE}/chapter/{slug}/story")
        page.wait_for_load_state("networkidle")
        state = {
            "sceneIndex": 9,
            "dialogueStep": 0,
            "completedScenes": [str(index).zfill(2) for index in range(9)],
            "inspected": {},
            "answers": {},
            "classifications": {},
            "assemblies": {},
            "decisionId": None,
            "interludesSeen": [],
            "revisionCount": 0,
        }
        page.evaluate(
            "([key, value]) => localStorage.setItem(key, JSON.stringify(value))",
            [f"tongxin.{slug}.story.v1", state],
        )
        page.reload(wait_until="networkidle")
        expect(page.locator(".story-heading h1")).to_have_text(title)
        viewport_metrics = page.evaluate("() => ({inner: innerHeight, html: document.documentElement.scrollHeight})")
        assert viewport_metrics["html"] <= viewport_metrics["inner"] + 1, (slug, viewport_metrics)
        dialogue_steps = 6 if slug == "contemporary" else 4
        for step in range(dialogue_steps):
            text_box = page.locator(".dialogue-panel__text")
            metrics = text_box.evaluate("el => ({client: el.clientHeight, scroll: el.scrollHeight})")
            assert metrics["scroll"] <= metrics["client"] + 1, (slug, step, metrics)
            if step < dialogue_steps - 1:
                page.locator(".dialogue-panel__cue").click()
                page.wait_for_timeout(120)
        if slug == "han":
            page.screenshot(path=SCREENSHOTS / "v16-han-thematic-coda.png", full_page=True)
        if slug == "northern-wei":
            page.screenshot(path=SCREENSHOTS / "v17-wei-two-hometowns-coda.png", full_page=True)
        if slug == "tang":
            page.screenshot(path=SCREENSHOTS / "v18-tang-meeting-coda.png", full_page=True)
        if slug == "qing":
            page.screenshot(path=SCREENSHOTS / "v20-qing-many-hands-coda.png", full_page=True)
        page.close()


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        smoke_chapters(browser)
        full_han(browser)
        full_qing(browser)
        full_contemporary(browser)
        mobile_layout(browser)
        mobile_qing_layout(browser)
        thematic_codas(browser)
        browser.close()
    print("five chapter story checks passed")


if __name__ == "__main__":
    main()
