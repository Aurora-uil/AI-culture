"""AI 编排层。

流程（各章规格 §14.3）：

    原始问题
      ↓  问题改写（Prompt B）
      ↓  检索（强制 metadata filter）
      ↓  重排（Prompt C）
      ↓  生成（Prompt A）
      ↓  护栏（确定性规则，必跑）
      ↓  核验（Prompt D，无 LLM 时跳过）
      ↓  结构化结果

关键约束：
- **No Context No Answer**：检索不到证据一律 NO_EVIDENCE、answer 为空，
  绝不让模型凭常识补全。
- `response_tier` 必须如实标注，绝不把兜底伪装成实时 AI。
"""

from __future__ import annotations

import json
import logging
import re

from sqlalchemy.orm import Session

from app.ai import guards, reranker, validator
from app.ai.llm import get_provider
from app.ai.llm.base import LlmError, LlmTimeoutError
from app.ai.prompts import (
    GUARD_REWRITE_SUFFIX,
    PROMPT_VERSION,
    build_evidence_block,
    build_rewrite_prompt,
    get_system_prompt,
)
from app.ai.retriever import (
    RetrievedChunk,
    load_chapter_estimates,
    load_entities,
    load_sources,
    retrieve,
)
from app.config import settings
from app.models import Chapter, Entity
from app.schemas.chat import AnswerOut, CitationOut, RelatedEntityOut

logger = logging.getLogger(__name__)

# 回答层级 —— 界面据此标注，不得混淆
TIER_LIVE_RAG = "live_rag"
TIER_LOCAL_RETRIEVAL = "local_retrieval"
TIER_FAQ_FALLBACK = "faq_fallback"

# 状态机
STATUS_DONE = "DONE"
STATUS_NO_EVIDENCE = "NO_EVIDENCE"
STATUS_MODEL_TIMEOUT = "MODEL_TIMEOUT"
STATUS_VALIDATION_FAILED = "VALIDATION_FAILED"
STATUS_FALLBACK_DEMO = "FALLBACK_DEMO"

NO_EVIDENCE_MESSAGE = (
    "当前资料库中没有足够可靠的材料支持确定回答这个问题。"
    "你可以换个问法，或查看与本章相关的已核验资料。"
)

FALLBACK_MESSAGE = "当前启用演示保障模式，以下内容来自已审核的预设问答库。"


# ============================================================
# 主流程
# ============================================================


async def answer_question(
    db: Session,
    *,
    chapter_id: str | None,
    question: str,
    answer_mode: str = "narrative",
    character_id: str | None = None,
    current_entity_id: str | None = None,
) -> AnswerOut:
    """完整回答流程。任何异常都会被转成中文友好的结构化结果。"""
    question = (question or "").strip()
    if not question:
        return AnswerOut(
            answer_markdown="",
            status=STATUS_NO_EVIDENCE,
            response_tier=TIER_LOCAL_RETRIEVAL,
            uncertainty="high",
            message="请先输入你想了解的问题。",
        )

    provider = get_provider()

    # ---------- 无 LLM Key：直接走预审核问答库 ----------
    if not settings.llm_configured:
        return await _faq_fallback_answer(
            db,
            chapter_id=chapter_id,
            question=question,
            provider=provider,
            reason="no_key",
        )

    # ---------- 1) 问题改写（Prompt B） ----------
    rewritten = await _rewrite_question(db, question, chapter_id, current_entity_id)

    # ---------- 2) 检索 + 3) 重排 ----------
    try:
        candidates = await retrieve(db, rewritten, chapter_id or "", top_k=settings.retrieval_top_k)
    except Exception as exc:  # noqa: BLE001
        logger.warning("检索失败：%s", exc)
        candidates = []

    if not candidates:
        # No Context No Answer —— 不得凭常识补全
        return AnswerOut(
            answer_markdown="",
            status=STATUS_NO_EVIDENCE,
            response_tier=TIER_LOCAL_RETRIEVAL,
            uncertainty="high",
            message=NO_EVIDENCE_MESSAGE,
            model_name=None,
            prompt_version=PROMPT_VERSION,
        )

    try:
        chunks = await reranker.rerank(
            rewritten,
            candidates,
            chapter_id=chapter_id,
            top_n=settings.retrieval_final_k,
            provider=provider,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("重排失败，沿用检索顺序：%s", exc)
        chunks = candidates[: settings.retrieval_final_k]

    if not chunks:
        return AnswerOut(
            answer_markdown="",
            status=STATUS_NO_EVIDENCE,
            response_tier=TIER_LOCAL_RETRIEVAL,
            uncertainty="high",
            message=NO_EVIDENCE_MESSAGE,
            prompt_version=PROMPT_VERSION,
        )

    # ---------- 4) 生成（Prompt A） ----------
    try:
        parsed = await _generate(db, chunks, chapter_id, question, rewritten, answer_mode)
    except LlmTimeoutError:
        return await _faq_fallback_answer(
            db,
            chapter_id=chapter_id,
            question=question,
            provider=provider,
            reason="timeout",
            chunks=chunks,
        )
    except LlmError as exc:
        logger.warning("生成失败，降级到兜底问答库：%s", exc)
        return await _faq_fallback_answer(
            db,
            chapter_id=chapter_id,
            question=question,
            provider=provider,
            reason="unavailable",
            chunks=chunks,
        )

    answer = parsed.get("answer_markdown") or ""
    citation_ids = [c for c in (parsed.get("citation_ids") or []) if isinstance(c, str)]

    # ---------- 5) 护栏 + 6) 核验 ----------
    result = await validator.validate(
        answer,
        chunks,
        chapter_id=chapter_id,
        question=question,
        citation_ids=citation_ids,
        provider=provider,
    )

    # 命中护栏 → 带上违规原因重写一次
    if result.rewrite_required:
        rewritten_parsed = await _rewrite_answer(
            db, chunks, chapter_id, question, answer_mode, result.violation_text
        )
        if rewritten_parsed is not None:
            answer = rewritten_parsed.get("answer_markdown") or ""
            citation_ids = [
                c for c in (rewritten_parsed.get("citation_ids") or []) if isinstance(c, str)
            ]
            result = await validator.validate(
                answer,
                chunks,
                chapter_id=chapter_id,
                question=question,
                citation_ids=citation_ids,
                provider=provider,
            )

    if result.rewrite_required:
        # 重写后仍违规 → 降级为兜底回答，绝不把违规内容放出去
        logger.warning(
            "护栏重写后仍违规，降级为兜底回答：%s", [h.code for h in result.guard_hits]
        )
        fallback = await _faq_fallback_answer(
            db,
            chapter_id=chapter_id,
            question=question,
            provider=provider,
            reason="guard",
            chunks=chunks,
        )
        fallback.status = STATUS_VALIDATION_FAILED
        fallback.guard_hits = [f"{h.code}:{h.label}" for h in result.guard_hits]
        return fallback

    if not answer.strip():
        return AnswerOut(
            answer_markdown="",
            status=STATUS_NO_EVIDENCE,
            response_tier=TIER_LIVE_RAG,
            uncertainty="high",
            message=NO_EVIDENCE_MESSAGE,
            citations=_build_citations(chunks, []),
            prompt_version=PROMPT_VERSION,
            model_name=provider.model,
        )

    return _finalize(
        db,
        answer=answer,
        citation_ids=citation_ids,
        related_ids=list(parsed.get("related_entity_ids") or []),
        chunks=chunks,
        uncertainty=parsed.get("uncertainty") or "low",
        status=STATUS_DONE,
        tier=TIER_LIVE_RAG,
        guard_hits=[],
        message=None,
        model_name=provider.model,
    )


# ============================================================
# 各步骤
# ============================================================


async def _rewrite_question(
    db: Session, question: str, chapter_id: str | None, current_entity_id: str | None
) -> str:
    """Prompt B。失败时退回原问题，绝不因为改写失败而答不了。"""
    provider = get_provider()
    chapter = db.get(Chapter, chapter_id) if chapter_id else None
    entity = db.get(Entity, current_entity_id) if current_entity_id else None

    try:
        rewritten = await provider.complete(
            [
                {
                    "role": "system",
                    "content": "你是历史知识库检索查询改写器，只输出改写后的问题本身。",
                },
                {
                    "role": "user",
                    "content": build_rewrite_prompt(
                        question,
                        chapter.title if chapter else None,
                        (entity.display_name or entity.name) if entity else None,
                    ),
                },
            ],
            max_tokens=200,
            chapter_id=chapter_id,
            question=question,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Prompt B 改写失败，使用原问题：%s", exc)
        return question

    rewritten = _clean_rewrite(rewritten)
    return rewritten or question


def _clean_rewrite(raw: str) -> str:
    """清理改写结果：去引号、去前缀、限长。"""
    if not raw:
        return ""
    text = raw.strip().strip("`").strip()
    text = re.sub(r"^(输出|改写后的问题|问题)[:：]\s*", "", text)
    text = text.strip().strip('"').strip("“”").strip()
    if len(text) > 200:
        text = text[:200]
    return text


async def _generate(
    db: Session,
    chunks: list[RetrievedChunk],
    chapter_id: str | None,
    question: str,
    rewritten: str,
    answer_mode: str,
) -> dict:
    """Prompt A 生成。返回解析后的结构化字典。"""
    provider = get_provider()
    system_prompt = get_system_prompt(chapter_id)
    estimates = load_chapter_estimates(db, chapter_id or "") if chapter_id else []
    evidence_block = build_evidence_block(
        [chunk.to_evidence_dict() for chunk in chunks], estimates
    )

    user_content = "\n".join(
        [
            f"<ANSWER_MODE>{answer_mode}</ANSWER_MODE>",
            "",
            evidence_block,
            "",
            "用户问题：",
            question,
            "",
            "检索用问题（已改写）：",
            rewritten,
            "",
            "请严格按约定 JSON 结构输出，不要输出任何额外文字。",
        ]
    )

    raw = await provider.complete(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        max_tokens=settings.llm_max_tokens,
        json_mode=True,
        chapter_id=chapter_id,
        question=question,
        available_source_ids=[chunk.source_id for chunk in chunks if chunk.source_id],
    )

    parsed = _parse_answer(raw)
    parsed["_raw"] = raw
    return parsed


def _parse_answer(raw: str) -> dict:
    """解析模型输出。解析不出来就把原文当作 markdown 回答（不丢内容）。"""
    if not raw:
        return {"answer_markdown": "", "citation_ids": [], "related_entity_ids": []}

    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()

    data = None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
            except json.JSONDecodeError:
                data = None

    if not isinstance(data, dict):
        # 模型没按 JSON 输出，直接当作回答正文
        return {"answer_markdown": text, "citation_ids": [], "related_entity_ids": []}

    return {
        "answer_markdown": str(data.get("answer_markdown") or ""),
        "citation_ids": [str(c) for c in (data.get("citation_ids") or []) if c],
        "related_entity_ids": [str(e) for e in (data.get("related_entity_ids") or []) if e],
        "uncertainty": data.get("uncertainty") or "low",
    }


async def _rewrite_answer(
    db: Session,
    chunks: list[RetrievedChunk],
    chapter_id: str | None,
    question: str,
    answer_mode: str,
    violation_text: str,
) -> dict | None:
    """护栏命中后，带上违规原因再问一次。失败返回 None（走降级）。"""
    if not violation_text:
        return None
    provider = get_provider()
    system_prompt = get_system_prompt(chapter_id) + GUARD_REWRITE_SUFFIX.format(
        violations=violation_text
    )
    try:
        raw = await provider.complete(
            [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": "\n".join(
                        [
                            f"<ANSWER_MODE>{answer_mode}</ANSWER_MODE>",
                            "",
                            build_evidence_block([c.to_evidence_dict() for c in chunks]),
                            "",
                            "用户问题：",
                            question,
                            "",
                            "请重写回答。",
                        ]
                    ),
                },
            ],
            max_tokens=settings.llm_max_tokens,
            json_mode=True,
            chapter_id=chapter_id,
            question=question,
        )
    except LlmError as exc:
        logger.warning("护栏重写调用失败：%s", exc)
        return None
    except Exception as exc:  # noqa: BLE001
        logger.warning("护栏重写异常：%s", exc)
        return None
    return _parse_answer(raw)


async def _faq_fallback_answer(
    db: Session,
    *,
    chapter_id: str | None,
    question: str,
    provider,
    reason: str,
    chunks: list[RetrievedChunk] | None = None,
) -> AnswerOut:
    """兜底问答库作答。**必须如实标注，不得伪装成实时 AI。**"""
    from app.ai.llm.mock import MockProvider

    mock = provider if isinstance(provider, MockProvider) else MockProvider()

    try:
        raw = await mock.complete(
            [{"role": "user", "content": question}],
            question=question,
            chapter_id=chapter_id,
            available_source_ids=[c.source_id for c in (chunks or []) if c.source_id],
        )
        payload = json.loads(raw)
    except Exception as exc:  # noqa: BLE001 - 兜底都失败时给出最保守回答
        logger.warning("兜底问答库调用失败：%s", exc)
        payload = {"answer_markdown": "", "citation_ids": [], "related_entity_ids": [],
                   "_matched": False}

    matched = bool(payload.get("_matched"))
    citation_ids = list(payload.get("citation_ids") or [])
    related_ids = list(payload.get("related_entity_ids") or [])

    if not matched:
        return AnswerOut(
            answer_markdown="",
            status=STATUS_NO_EVIDENCE,
            response_tier=TIER_FAQ_FALLBACK,
            uncertainty="high",
            message=NO_EVIDENCE_MESSAGE,
            citations=_build_citations(chunks or [], []),
            prompt_version=PROMPT_VERSION,
            model_name=mock.model,
        )

    status = STATUS_FALLBACK_DEMO
    if reason == "timeout":
        status = STATUS_MODEL_TIMEOUT

    # 兜底回答的引用来自 FAQ 条目已审核的 source_ids，不依赖当次检索命中
    citations = _citations_from_source_ids(db, citation_ids)
    related = _build_related_entities(db, related_ids[:8])

    return AnswerOut(
        answer_markdown=payload.get("answer_markdown") or "",
        citation_ids=[c.source_id for c in citations],
        related_entity_ids=[e.id for e in related],
        uncertainty=payload.get("uncertainty") or "medium",
        status=status,
        response_tier=TIER_FAQ_FALLBACK,
        guard_hits=[],
        citations=citations,
        related_entities=related,
        message=FALLBACK_MESSAGE,
        model_name=mock.model,
        prompt_version=PROMPT_VERSION,
    )


# ============================================================
# 结果组装
# ============================================================


def _finalize(
    db: Session,
    *,
    answer: str,
    citation_ids: list[str],
    related_ids: list[str],
    chunks: list[RetrievedChunk],
    uncertainty: str,
    status: str,
    tier: str,
    guard_hits: list[str],
    message: str | None,
    model_name: str | None,
) -> AnswerOut:
    """把回答与引用组装成前端契约的结构。"""
    # 模型可能引用了不存在的编号 —— 这里做一次硬过滤
    citations = _build_citations(chunks, citation_ids)

    # 关联实体：优先用模型给的，缺失时用检索片段挂的实体
    if not related_ids:
        related_ids = []
        for chunk in chunks:
            for entity_id in chunk.entity_ids:
                if entity_id not in related_ids:
                    related_ids.append(entity_id)

    related = _build_related_entities(db, related_ids[:8])

    return AnswerOut(
        answer_markdown=answer,
        citation_ids=[c.source_id for c in citations],
        related_entity_ids=[e.id for e in related],
        uncertainty=uncertainty,
        status=status,
        response_tier=tier,
        guard_hits=guard_hits,
        citations=citations,
        related_entities=related,
        message=message,
        model_name=model_name,
        prompt_version=PROMPT_VERSION,
    )


def _build_citations(
    chunks: list[RetrievedChunk], citation_ids: list[str]
) -> list[CitationOut]:
    """按 citation_ids 组装引用。编号不存在时忽略；为空时回退到全部检索片段。

    引用必须带 claim_text（该来源支持的片段摘要），界面「史料依据」面板要用。
    """
    by_id = {chunk.id: chunk for chunk in chunks}
    selected = [by_id[cid] for cid in citation_ids if cid in by_id]
    if not selected:
        selected = chunks

    citations: list[CitationOut] = []
    seen_sources: set[str] = set()
    for chunk in selected:
        if not chunk.source_id or chunk.source_id in seen_sources:
            continue
        seen_sources.add(chunk.source_id)
        citations.append(
            CitationOut(
                source_id=chunk.source_id,
                title=chunk.source_title or chunk.title,
                institution=chunk.source_institution,
                source_level=chunk.source_level,
                public_url=chunk.public_url,
                claim_text=chunk.title or None,
                chunk_id=chunk.id,
            )
        )
        if len(citations) >= 5:
            break
    return citations


def _citations_from_source_ids(
    db: Session, source_ids: list[str], claim_text: str | None = None
) -> list[CitationOut]:
    """直接按来源 ID 组装引用。

    兜底问答库走的是这条路：FAQ 条目的 source_ids 已经过人工审核，
    不需要（也不应该）依赖当次检索命中了哪些 chunk。
    """
    if not source_ids:
        return []
    try:
        rows = load_sources(db, source_ids)
    except Exception as exc:  # noqa: BLE001
        # 不能静默返回空列表：那会让回答看起来「本来就没有来源」，
        # 实际却是数据库读取失败。必须留下日志，否则比赛现场无从排查。
        logger.warning("读取来源失败，本次回答将不带引用：%s", exc)
        return []

    citations: list[CitationOut] = []
    for source_id in source_ids:
        source = rows.get(source_id)
        if source is None:
            continue
        citations.append(
            CitationOut(
                source_id=source.id,
                title=source.title,
                institution=source.institution or "",
                source_level=source.source_level,
                public_url=source.public_url,
                claim_text=claim_text,
            )
        )
        if len(citations) >= 5:
            break
    return citations


def _build_related_entities(db: Session, entity_ids: list[str]) -> list[RelatedEntityOut]:
    """关联实体。实体不存在时跳过，不报错。"""
    if not entity_ids:
        return []
    entities = load_entities(db, entity_ids)
    return [
        RelatedEntityOut(
            id=entity.id,
            name=entity.name,
            display_name=entity.display_name,
            entity_type=entity.entity_type,
        )
        for entity in entities
    ]


# ============================================================
# 探索总结（Prompt E）
# ============================================================


async def summarize_exploration(
    chapter_id: str, visited_names: list[str], asked_count: int, next_entity_ids: list[str]
) -> str:
    """Prompt E。失败返回空串，调用方回退规则总结。"""
    if not settings.llm_configured or not visited_names:
        return ""

    provider = get_provider()
    user_content = "\n".join(
        [
            f"当前章节：{chapter_id}",
            "用户访问过的内容名称：",
            "、".join(visited_names[:20]),
            f"提问次数：{asked_count}",
            "候选下一批节点：" + "、".join(next_entity_ids[:6]),
            "",
            "请按要求输出 JSON。",
        ]
    )
    try:
        from app.ai.prompts.common import PROMPT_E_SUMMARY

        raw = await provider.complete(
            [
                {"role": "system", "content": PROMPT_E_SUMMARY},
                {"role": "user", "content": user_content},
            ],
            max_tokens=400,
            json_mode=True,
            chapter_id=chapter_id,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Prompt E 总结失败：%s", exc)
        return ""

    text = re.sub(r"^```(?:json)?\s*|\s*$$", "", (raw or "").strip(), flags=re.MULTILINE).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return ""
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return ""

    summary = str(data.get("summary") or "").strip()
    return summary if 20 <= len(summary) <= 200 else ""
