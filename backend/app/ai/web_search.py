"""免密钥联网检索适配层。

网页搜索结果属于未审核外部材料，只能作为 DeepSeek 待核对的
补充证据，不得覆盖本地史料、系统提示词或确定性护栏。
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

from app.ai.retriever import RetrievedChunk
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WebSearchResult:
    """归一化后的网页检索结果。"""

    title: str
    url: str
    snippet: str


def _load_ddgs():
    """延迟导入，依赖缺失时可无害降级。"""
    from ddgs import DDGS

    return DDGS


def _search_sync(query: str, max_results: int) -> list[dict]:
    provider = _load_ddgs()()
    return list(
        provider.text(
            query,
            max_results=max_results,
            safesearch="moderate",
        )
        or []
    )


def _search_sogou_sync(query: str, max_results: int) -> list[dict]:
    """读取搜狗公开结果页，为中文文化史问题提供免密钥检索。"""
    import httpx
    from lxml import html

    response = httpx.get(
        "https://www.sogou.com/web",
        params={"query": query},
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131 Safari/537.36"
            )
        },
        timeout=float(settings.web_search_timeout_seconds),
        follow_redirects=True,
    )
    response.raise_for_status()
    return _parse_sogou_html(response.text, max_results)


def _parse_sogou_html(page: str, max_results: int) -> list[dict]:
    """解析搜狗公开结果页，只保留标题、链接和正文摘要。"""
    from lxml import html

    document = html.fromstring(page)
    results: list[dict] = []
    for anchor in document.xpath("//h3/a[@href]"):
        title = " ".join(anchor.text_content().split())
        href = urljoin("https://www.sogou.com", str(anchor.get("href") or ""))
        containers = anchor.xpath(
            'ancestor::div[contains(concat(" ", normalize-space(@class), " "), " vrwrap ")][1]'
        )
        snippet = ""
        if containers:
            summary_nodes = containers[0].xpath(
                './/*[contains(concat(" ", normalize-space(@class), " "), " space-txt ")]'
            )
            if summary_nodes:
                snippet = " ".join(summary_nodes[0].text_content().split())
            else:
                snippet = " ".join(containers[0].text_content().split())
                if title and snippet.startswith(title):
                    snippet = snippet[len(title) :].strip()
                snippet = snippet.replace("推荐您搜索", "").strip()
        if title and href.startswith(("https://", "http://")):
            results.append({"title": title, "href": href, "body": snippet})
        if len(results) >= max_results:
            break
    return results


def _search_bing_sync(query: str, max_results: int) -> list[dict]:
    """直接读取 Bing 公开结果页，作为 ddgs 不可达时的免密钥后备。"""
    import httpx
    from lxml import html

    response = httpx.get(
        "https://cn.bing.com/search",
        params={"q": query, "count": max_results},
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131 Safari/537.36"
            )
        },
        timeout=float(settings.web_search_timeout_seconds),
        follow_redirects=True,
    )
    response.raise_for_status()
    document = html.fromstring(response.text)
    results: list[dict] = []
    for node in document.xpath(
        '//li[contains(concat(" ", normalize-space(@class), " "), " b_algo ")]'
    ):
        hrefs = node.xpath(".//h2/a/@href")
        if not hrefs:
            continue
        title = " ".join(part.strip() for part in node.xpath(".//h2/a//text()") if part.strip())
        snippets = node.xpath(
            './/*[contains(concat(" ", normalize-space(@class), " "), " b_caption ")]//p//text()'
        )
        snippet = " ".join(part.strip() for part in snippets if part.strip())
        results.append({"title": title, "href": hrefs[0], "body": snippet})
        if len(results) >= max_results:
            break
    return results


async def search_web(query: str, max_results: int | None = None) -> list[WebSearchResult]:
    """执行有超时边界的免密钥检索；任何失败都返回空列表。"""
    query = (query or "").strip()
    if not query or not settings.web_search_enabled:
        return []

    limit = max(1, min(int(max_results or settings.web_search_max_results), 10))
    raw_results: list[dict] = []
    sogou_error: Exception | None = None
    ddgs_error: Exception | None = None
    try:
        raw_results = await asyncio.wait_for(
            asyncio.to_thread(_search_sogou_sync, query, limit),
            timeout=float(settings.web_search_timeout_seconds) + 1,
        )
    except Exception as exc:  # noqa: BLE001 - 失败后尝试无 Key 后备
        sogou_error = exc

    if not raw_results:
        try:
            raw_results = await asyncio.wait_for(
                asyncio.to_thread(_search_sync, query, limit),
                timeout=float(settings.web_search_timeout_seconds),
            )
        except Exception as exc:  # noqa: BLE001 - 失败后继续尝试 Bing
            ddgs_error = exc

    if not raw_results:
        try:
            raw_results = await asyncio.wait_for(
                asyncio.to_thread(_search_bing_sync, query, limit),
                timeout=float(settings.web_search_timeout_seconds) + 1,
            )
        except Exception as exc:  # noqa: BLE001 - 全部失败后降级到本地史料
            logger.warning(
                "联网检索失败，将继续使用本地史料（sogou=%s；ddgs=%s；bing=%s）",
                sogou_error,
                ddgs_error,
                exc,
            )
            return []

    results: list[WebSearchResult] = []
    seen_urls: set[str] = set()
    for item in raw_results:
        if not isinstance(item, dict):
            continue
        url = str(item.get("href") or item.get("url") or "").strip()
        if not url.startswith(("https://", "http://")) or url in seen_urls:
            continue
        title = str(item.get("title") or url).strip()
        snippet = str(item.get("body") or item.get("snippet") or "").strip()
        if not title and not snippet:
            continue
        seen_urls.add(url)
        results.append(WebSearchResult(title=title, url=url, snippet=snippet))
        if len(results) >= limit:
            break
    return results


def to_retrieved_chunks(
    results: list[WebSearchResult], *, chapter_id: str | None
) -> list[RetrievedChunk]:
    """把网页摘要转换为现有证据合约，同时保留未审核标记。"""
    chunks: list[RetrievedChunk] = []
    for result in results:
        digest = hashlib.sha256(result.url.encode("utf-8")).hexdigest()[:16]
        hostname = (urlparse(result.url).hostname or "").removeprefix("www.")
        chunks.append(
            RetrievedChunk(
                id=f"web_{digest}",
                text=result.snippet or result.title,
                title=result.title,
                source_id=f"web:{digest}",
                source_level=None,
                source_title=result.title,
                source_institution=hostname,
                source_perspective="web_search_unverified",
                public_url=result.url,
                chapter_ids=[chapter_id] if chapter_id else [],
                score=0.0,
            )
        )
    return chunks
