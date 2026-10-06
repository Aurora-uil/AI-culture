"""检索层。

**强制 metadata filter**（各章规格 §14.2，不可放宽）：

    review_status = 'approved'
    AND chapter_ids 含当前章
    AND source_level IN ('S','A','B')

有 EMBEDDING_API_KEY 时用向量余弦（语料只有数百条，numpy 暴力即可）；
没有时用纯 Python 中文检索（字符 bigram + 关键词加权），不依赖任何外部服务。
"""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass, field

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai import text_utils
from app.config import settings
from app.models import Entity, HistoricalEstimate, RagChunk, Source

logger = logging.getLogger(__name__)

# 允许进入检索的来源等级。C 级（普通网络材料）永不进入 AI 回答。
ALLOWED_SOURCE_LEVELS = ("S", "A", "B")

# 本地检索打分权重
WEIGHT_BM25 = 0.65
WEIGHT_KEYWORD = 0.25
WEIGHT_JACCARD = 0.10


@dataclass
class RetrievedChunk:
    """一条检索结果。字段命名与 build_evidence_block 对应。"""

    id: str
    text: str
    title: str = ""
    source_id: str | None = None
    source_level: str | None = None
    source_title: str = ""
    source_institution: str = ""
    source_perspective: str | None = None
    public_url: str | None = None
    chapter_ids: list[str] = field(default_factory=list)
    entity_ids: list[str] = field(default_factory=list)
    claim_ids: list[str] = field(default_factory=list)
    meaning_status: str | None = None
    score: float = 0.0

    def to_evidence_dict(self) -> dict:
        """转成 Prompt 里 <EVIDENCE> 块需要的字典。"""
        return {
            "id": self.id,
            "title": self.title,
            "text": self.text,
            "source_title": self.source_title,
            "source_level": self.source_level,
            "source_perspective": self.source_perspective,
            "public_url": self.public_url,
        }


# ============================================================
# 候选集
# ============================================================


def load_candidates(db: Session, chapter_id: str) -> list[RagChunk]:
    """按强制过滤条件取候选 chunk。数据库为空时返回空列表。"""
    try:
        stmt = select(RagChunk).where(
            RagChunk.review_status == "approved",
            RagChunk.source_level.in_(ALLOWED_SOURCE_LEVELS),
            RagChunk.chapter_ids.contains([chapter_id]),
        )
        return list(db.execute(stmt).scalars().all())
    except Exception as exc:  # noqa: BLE001 - 检索失败不应 500
        logger.warning("检索候选集查询失败（返回空）：%s", exc)
        return []


# ============================================================
# 向量检索
# ============================================================


def _cosine_scores(query_vector: list[float], chunks: list[RagChunk]) -> dict[str, float]:
    """numpy 暴力余弦。维度不一致（换过供应商）的 chunk 直接跳过。"""
    scores: dict[str, float] = {}
    if not query_vector:
        return scores

    query = np.asarray(query_vector, dtype=np.float64)
    query_norm = np.linalg.norm(query)
    if query_norm <= 0:
        return scores

    dim = len(query_vector)
    usable: list[RagChunk] = []
    matrix_rows: list[list[float]] = []
    for chunk in chunks:
        embedding = chunk.embedding
        if not embedding or len(embedding) != dim:
            continue
        usable.append(chunk)
        matrix_rows.append([float(v) for v in embedding])

    if not usable:
        return scores

    matrix = np.asarray(matrix_rows, dtype=np.float64)
    norms = np.linalg.norm(matrix, axis=1)
    norms[norms == 0] = 1e-9
    similarities = (matrix @ query) / (norms * query_norm)

    for chunk, similarity in zip(usable, similarities):
        scores[chunk.id] = float(max(0.0, min(1.0, similarity)))
    return scores


async def embed_query(text: str) -> list[float] | None:
    """把查询文本向量化。未配置 Embedding 或调用失败时返回 None。"""
    if not settings.embedding_configured or not text:
        return None

    import httpx

    base_url = (settings.embedding_base_url or "").rstrip("/")
    endpoint = f"{base_url}/embeddings" if not base_url.endswith("/embeddings") else base_url
    payload = {
        "model": settings.embedding_model,
        "input": text,
    }
    headers = {
        "Authorization": f"Bearer {settings.embedding_api_key}",
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
            response = await client.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        return list(data["data"][0]["embedding"])
    except Exception as exc:  # noqa: BLE001 - 向量失败自动退回本地检索
        logger.warning("Embedding 调用失败，改用本地中文检索：%s", exc)
        return None


# ============================================================
# 本地中文检索
# ============================================================


def _local_scores(question: str, chunks: list[RagChunk]) -> dict[str, float]:
    """字符 bigram BM25 + 关键词命中 + Jaccard，归一化到 0–1。"""
    if not chunks:
        return {}

    query_tokens = Counter(text_utils.tokenize(question))
    doc_tokens = {chunk.id: text_utils.tokenize(chunk.text or "") for chunk in chunks}
    lengths = [len(tokens) for tokens in doc_tokens.values()]
    avg_len = sum(lengths) / len(lengths) if lengths else 1.0

    raw: dict[str, float] = {}
    for chunk in chunks:
        tokens = doc_tokens[chunk.id]
        bm25 = text_utils.bm25_like_score(query_tokens, tokens, avg_len)
        # 标题命中额外加权：标题通常就是该段材料的主题
        title_bonus = text_utils.bm25_like_score(
            query_tokens, text_utils.tokenize(chunk.title or ""), avg_len
        )
        raw[chunk.id] = bm25 + 0.5 * title_bonus

    max_raw = max(raw.values()) if raw else 0.0
    if max_raw <= 0:
        # 完全没有词面重合，退化为 Jaccard，仍可能命中短问题
        return {chunk.id: text_utils.jaccard(question, chunk.text or "") for chunk in chunks}

    scores: dict[str, float] = {}
    for chunk in chunks:
        normalized_bm25 = raw[chunk.id] / max_raw
        keyword = text_utils.keyword_overlap(question, (chunk.title or "") + (chunk.text or ""))
        jac = text_utils.jaccard(question, (chunk.title or "") + (chunk.text or ""))
        scores[chunk.id] = round(
            WEIGHT_BM25 * normalized_bm25 + WEIGHT_KEYWORD * keyword + WEIGHT_JACCARD * jac, 6
        )
    return scores


# ============================================================
# 对外接口
# ============================================================


async def retrieve(
    db: Session,
    question: str,
    chapter_id: str,
    top_k: int | None = None,
    min_score: float | None = None,
) -> list[RetrievedChunk]:
    """检索 top_k 条证据。检索不到时返回空列表（上层据此返回 NO_EVIDENCE）。"""
    top_k = int(top_k or settings.retrieval_top_k)
    min_score = float(settings.retrieval_min_score if min_score is None else min_score)

    if not question or not question.strip():
        return []

    chunks = load_candidates(db, chapter_id)
    if not chunks:
        logger.info("章节 %s 没有可检索的 chunk（内容可能尚未 seed）", chapter_id)
        return []

    # 有向量就用向量，否则本地
    scores: dict[str, float] = {}
    query_vector = await embed_query(question)
    if query_vector:
        scores = _cosine_scores(query_vector, chunks)

    if not scores:
        scores = _local_scores(question, chunks)

    ranked = sorted(chunks, key=lambda c: scores.get(c.id, 0.0), reverse=True)[:top_k]

    source_ids = [c.source_id for c in ranked if c.source_id]
    source_map = _load_sources(db, source_ids)

    results: list[RetrievedChunk] = []
    for chunk in ranked:
        score = float(scores.get(chunk.id, 0.0))
        if score < min_score:
            continue
        source = source_map.get(chunk.source_id or "")
        results.append(
            RetrievedChunk(
                id=chunk.id,
                text=chunk.text or "",
                title=chunk.title or "",
                source_id=chunk.source_id,
                source_level=chunk.source_level,
                source_title=source.title if source else "",
                source_institution=source.institution if source else "",
                source_perspective=source.source_perspective if source else None,
                public_url=source.public_url if source else None,
                chapter_ids=list(chunk.chapter_ids or []),
                entity_ids=list(chunk.entity_ids or []),
                claim_ids=list(chunk.claim_ids or []),
                meaning_status=chunk.meaning_status,
                score=score,
            )
        )
    return results


def load_sources(db: Session, source_ids: list[str]) -> dict[str, Source]:
    """按 ID 批量取来源，返回 {id: Source}。失败时返回空字典。

    注意：这里吞掉异常但**记录日志**。上游会把空字典理解成「这些来源不存在」，
    于是回答不带任何引用 —— 数据库故障就会表现成「AI 回答没有来源」，
    让人误以为是内容本身没有绑定来源。日志是唯一的排查线索。
    """
    if not source_ids:
        return {}
    try:
        rows = db.execute(select(Source).where(Source.id.in_(source_ids))).scalars().all()
        return {s.id: s for s in rows}
    except Exception as exc:  # noqa: BLE001
        logger.warning("按 ID 批量读取来源失败：%s", exc)
        return {}


# 兼容内部旧名
_load_sources = load_sources


def load_chapter_estimates(db: Session, chapter_id: str) -> list[dict]:
    """该章的历史数字，供 <HISTORICAL_ESTIMATES> 块使用。

    多来源并列，不求平均、不合并。
    """
    try:
        rows = db.execute(
            select(HistoricalEstimate).where(HistoricalEstimate.chapter_id == chapter_id)
        ).scalars().all()
    except Exception:  # noqa: BLE001
        return []
    if not rows:
        return []

    source_map = _load_sources(db, [r.source_id for r in rows if r.source_id])
    return [
        {
            "display_name": row.display_name,
            "value_text": row.value_text,
            "source_title": source_map[row.source_id].title if row.source_id in source_map else None,
            "scope_note": row.scope_note,
        }
        for row in rows
    ]


def load_entities(db: Session, entity_ids: list[str]) -> list[Entity]:
    """按 ID 取实体，保持传入顺序。"""
    if not entity_ids:
        return []
    try:
        rows = db.execute(select(Entity).where(Entity.id.in_(entity_ids))).scalars().all()
    except Exception:  # noqa: BLE001
        return []
    order = {entity_id: index for index, entity_id in enumerate(entity_ids)}
    return sorted(rows, key=lambda e: order.get(e.id, 999))
