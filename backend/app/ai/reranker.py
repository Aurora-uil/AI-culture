"""重排：用 Prompt C 做相关性打分（0–3），无 LLM 时用启发式打分。

规格要求「不得因为片段提到了『元代』就判为高度相关」，启发式里对应
扣掉「只命中章节名 / 通用词」的分片。
"""

from __future__ import annotations

import json
import logging
import re

from app.ai import text_utils
from app.ai.prompts.common import PROMPT_C_RELEVANCE
from app.ai.retriever import RetrievedChunk
from app.config import settings

logger = logging.getLogger(__name__)

# 0–3 分映射到是否保留：0 分直接丢弃
MIN_KEEP_RELEVANCE = 1

# 通用词：命中这些不代表相关
GENERIC_TERMS = {
    "元代", "汉代", "唐代", "北魏", "清代", "当代", "历史", "文化", "研究",
    "资料", "来源", "问题", "什么", "为什么", "怎么", "如何",
}


def heuristic_score(question: str, chunk: RetrievedChunk) -> int:
    """启发式相关性打分（0–3）。无 LLM 时使用。"""
    haystack = f"{chunk.title}\n{chunk.text}"

    keywords = [
        keyword
        for keyword in text_utils.extract_keywords(question, limit=15)
        if keyword not in GENERIC_TERMS
    ]
    if not keywords:
        return 1 if chunk.score >= settings.retrieval_min_score else 0

    normalized = text_utils.normalize(haystack)
    hits = sum(1 for keyword in keywords if keyword in normalized)
    coverage = hits / len(keywords)

    if coverage >= 0.5 and chunk.score >= 0.35:
        return 3
    if coverage >= 0.3:
        return 2
    if coverage > 0 or chunk.score >= settings.retrieval_min_score:
        return 1
    return 0


def _parse_scores(raw: str) -> dict[str, int]:
    """从 LLM 输出里解析 {chunk_id: relevance}。解析失败返回空字典。"""
    if not raw:
        return {}

    text = raw.strip()
    # 去掉可能的 ```json 围栏
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()

    data = None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # 模型可能包裹了说明文字，尝试截取第一个 JSON 数组
        match = re.search(r"\[.*\]", text, flags=re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
            except json.JSONDecodeError:
                return {}

    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return {}

    scores: dict[str, int] = {}
    for item in data:
        if not isinstance(item, dict):
            continue
        chunk_id = item.get("chunk_id")
        relevance = item.get("relevance")
        if not chunk_id:
            continue
        try:
            scores[str(chunk_id)] = int(relevance)
        except (TypeError, ValueError):
            continue
    return scores


async def rerank(
    question: str,
    chunks: list[RetrievedChunk],
    chapter_id: str | None = None,
    top_n: int | None = None,
    provider=None,
) -> list[RetrievedChunk]:
    """重排并截断到 top_n。无 LLM 或调用失败时自动用启发式。"""
    top_n = int(top_n or settings.retrieval_final_k)
    if not chunks:
        return []

    scores: dict[str, int] = {}

    if provider is not None and settings.llm_configured:
        try:
            prompt = _build_prompt(question, chunks)
            raw = await provider.complete(
                [
                    {"role": "system", "content": PROMPT_C_RELEVANCE},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=800,
                json_mode=True,
                chapter_id=chapter_id,
            )
            scores = _parse_scores(raw)
        except Exception as exc:  # noqa: BLE001 - 重排失败退回启发式
            logger.warning("Prompt C 重排失败，改用启发式打分：%s", exc)
            scores = {}

    ranked: list[tuple[int, float, RetrievedChunk]] = []
    for chunk in chunks:
        if chunk.id in scores:
            relevance = scores[chunk.id]
        else:
            relevance = heuristic_score(question, chunk)
        if relevance < MIN_KEEP_RELEVANCE:
            continue
        ranked.append((relevance, chunk.score, chunk))

    ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)

    result = []
    for relevance, _, chunk in ranked[:top_n]:
        # 把 0–3 相关性折进 score，便于上层做统一展示
        chunk.score = round(min(1.0, 0.4 * chunk.score + 0.2 * relevance), 4)
        result.append(chunk)
    return result


def _build_prompt(question: str, chunks: list[RetrievedChunk]) -> str:
    lines = [f"用户问题：{question}", "", "待判断片段："]
    for chunk in chunks:
        excerpt = text_utils.truncate(chunk.text, 400)
        lines.append(f"- chunk_id: {chunk.id}")
        lines.append(f"  标题: {chunk.title}")
        lines.append(f"  内容: {excerpt}")
        lines.append("")
    lines.append("请对每个片段输出 JSON 数组。")
    return "\n".join(lines)
