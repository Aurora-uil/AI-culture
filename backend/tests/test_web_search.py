from __future__ import annotations

import asyncio

from app.ai import service, validator, web_search
from app.ai.web_search import WebSearchResult, search_web, to_retrieved_chunks


def test_search_web_normalizes_and_deduplicates(monkeypatch) -> None:
    class FakeDDGS:
        def text(self, query: str, **kwargs):
            assert query == "居庸关云台六体文字"
            return [
                {
                    "title": " 北京市文物局：居庸关云台 ",
                    "href": "https://example.org/yuntai",
                    "body": " 云台券洞内保存多种文字题刻。 ",
                },
                {
                    "title": "重复结果",
                    "href": "https://example.org/yuntai",
                    "body": "不应重复。",
                },
                {"title": "无链接", "body": "应被忽略"},
            ]

    monkeypatch.setattr("app.ai.web_search._load_ddgs", lambda: FakeDDGS)
    monkeypatch.setattr("app.ai.web_search._search_sogou_sync", lambda query, max_results: [])

    results = asyncio.run(search_web("居庸关云台六体文字", max_results=5))

    assert results == [
        WebSearchResult(
            title="北京市文物局：居庸关云台",
            url="https://example.org/yuntai",
            snippet="云台券洞内保存多种文字题刻。",
        )
    ]


def test_search_web_returns_empty_when_provider_fails(monkeypatch) -> None:
    class BrokenDDGS:
        def text(self, query: str, **kwargs):
            raise RuntimeError("network unavailable")

    monkeypatch.setattr("app.ai.web_search._load_ddgs", lambda: BrokenDDGS)
    monkeypatch.setattr(
        "app.ai.web_search._search_sogou_sync",
        lambda query, max_results: (_ for _ in ()).throw(RuntimeError("sogou unavailable")),
    )
    monkeypatch.setattr(
        "app.ai.web_search._search_bing_sync",
        lambda query, max_results: (_ for _ in ()).throw(RuntimeError("bing unavailable")),
    )

    assert asyncio.run(search_web("居庸关云台")) == []


def test_search_web_uses_bing_fallback_when_ddgs_fails(monkeypatch) -> None:
    def broken_ddgs(query: str, max_results: int):
        raise RuntimeError("ddgs unavailable")

    def bing_results(query: str, max_results: int):
        return [
            {
                "title": "居庸关云台石刻",
                "href": "https://example.cn/yuntai",
                "body": "免密钥后备搜索结果。",
            }
        ]

    monkeypatch.setattr("app.ai.web_search._search_sync", broken_ddgs)
    monkeypatch.setattr("app.ai.web_search._search_sogou_sync", lambda query, max_results: [])
    monkeypatch.setattr("app.ai.web_search._search_bing_sync", bing_results)

    results = asyncio.run(search_web("居庸关云台"))

    assert results[0].url == "https://example.cn/yuntai"


def test_search_web_prefers_sogou_for_chinese_results(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.ai.web_search._search_sogou_sync",
        lambda query, max_results: [
            {
                "title": "云台六体文字石刻",
                "href": "https://example.cn/six-scripts",
                "body": "居庸关云台券洞内的六种文字题刻。",
            }
        ],
    )
    monkeypatch.setattr(
        "app.ai.web_search._search_sync",
        lambda query, max_results: (_ for _ in ()).throw(AssertionError("ddgs should not run")),
    )
    monkeypatch.setattr(
        "app.ai.web_search._search_bing_sync",
        lambda query, max_results: (_ for _ in ()).throw(AssertionError("bing should not run")),
    )

    results = asyncio.run(search_web("居庸关云台六体文字"))

    assert results[0].title == "云台六体文字石刻"


def test_sogou_parser_keeps_clean_summary_and_resolves_links() -> None:
    page = """
    <div class="vrwrap">
      <h3><a href="/link?url=abc">居庸关关城云台</a></h3>
      <div class="struct201102">.struct201102 { color: red; }
        <div class="fz-mid space-txt">云台原是元代过街塔的塔基，券洞内有六种文字题刻。</div>
      </div>
    </div>
    """

    results = web_search._parse_sogou_html(page, 5)

    assert results == [
        {
            "title": "居庸关关城云台",
            "href": "https://www.sogou.com/link?url=abc",
            "body": "云台原是元代过街塔的塔基，券洞内有六种文字题刻。",
        }
    ]


def test_web_results_become_untrusted_citable_chunks() -> None:
    chunks = to_retrieved_chunks(
        [
            WebSearchResult(
                title="居庸关云台",
                url="https://example.org/yuntai",
                snippet="可核对的网页摘要。",
            )
        ],
        chapter_id="yuan_yuntai",
    )

    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk.id.startswith("web_")
    assert chunk.source_id.startswith("web:")
    assert chunk.public_url == "https://example.org/yuntai"
    assert chunk.source_perspective == "web_search_unverified"
    assert chunk.source_level is None
    assert chunk.chapter_ids == ["yuan_yuntai"]


def test_answer_flow_is_web_search_then_one_deepseek_summary(monkeypatch) -> None:
    events: list[str] = []
    web_result = WebSearchResult(
        title="居庸关云台",
        url="https://example.org/yuntai",
        snippet="云台券洞内保存多种文字题刻。",
    )

    async def fake_search(question: str, max_results: int):
        events.append("web-search")
        return [web_result]

    async def fake_generate(db, chunks, chapter_id, question: str, rewritten: str):
        events.append("deepseek-summary")
        assert rewritten == question
        assert all(chunk.source_id.startswith("web:") for chunk in chunks)
        return {
            "answer_markdown": "测试回答",
            "citation_ids": [chunks[0].id],
            "related_entity_ids": [],
            "uncertainty": "medium",
        }

    async def fake_validate(*args, **kwargs):
        assert kwargs["provider"] is None
        return validator.ValidationResult(passed=True, llm_checked=False)

    class FakeProvider:
        model = "deepseek-test"

    monkeypatch.setattr(service.settings, "llm_api_key", "test-only")
    monkeypatch.setattr(service, "search_web", fake_search)
    monkeypatch.setattr(
        service,
        "_rewrite_question",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("question rewrite must not run")
        ),
    )
    monkeypatch.setattr(service, "_generate", fake_generate)
    monkeypatch.setattr(service.validator, "validate", fake_validate)
    monkeypatch.setattr(service, "get_provider", lambda: FakeProvider())

    answer = asyncio.run(
        service.answer_question(
            object(),
            chapter_id="yuan_yuntai",
            question="云台有哪些文字？",
        )
    )

    assert events == ["web-search", "deepseek-summary"]
    assert answer.citations[0].public_url == "https://example.org/yuntai"


def test_no_llm_key_still_returns_live_web_search_results(monkeypatch) -> None:
    calls: list[str] = []
    web_result = WebSearchResult(
        title="居庸关云台的历史背景",
        url="https://example.org/yuntai-history",
        snippet="居庸关云台始建于元代，现存石刻与题记是研究其背景的线索。",
    )

    async def fake_search(question: str, max_results: int):
        calls.append("web-search")
        assert "元代" in question
        assert "居庸关云台" in question
        return [web_result]

    class FakeProvider:
        model = "mock-faq"

    monkeypatch.setattr(service.settings, "llm_api_key", "")
    monkeypatch.setattr(service, "search_web", fake_search)
    monkeypatch.setattr(service, "get_provider", lambda: FakeProvider())

    answer = asyncio.run(
        service.answer_question(
            object(),
            chapter_id="yuan_yuntai",
            question="云台的背景是什么？",
        )
    )

    assert calls == ["web-search"]
    assert answer.status == "FALLBACK_WEB_SEARCH"
    assert answer.response_tier == "web_search_fallback"
    assert answer.citations[0].public_url == "https://example.org/yuntai-history"
    assert "居庸关云台的历史背景" in answer.answer_markdown
    assert "DeepSeek" in (answer.message or "")
