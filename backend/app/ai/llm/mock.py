"""兜底 Provider —— 无 LLM Key 时使用。

从 `content/<章>/faq.json`（或数据库 `fallback_faq` 表）按关键词 + 字符
bigram 相似度匹配答案。匹配不到时返回统一的「资料不足」回答。

**绝不伪装成实时 AI**：返回体里带 `_fallback: true`，上层据此把
`response_tier` 标为 `faq_fallback`，界面会显示「演示保障模式」。
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from typing import Any

from app.ai.llm.base import last_user_message
from app.ai.text_utils import jaccard, normalize
from app.config import settings
from app.services import content_loader

logger = logging.getLogger(__name__)

# 检索不到足够材料时的统一回答（各章规格 §13 NO_EVIDENCE 文案）
NO_EVIDENCE_ANSWER = "当前资料库中没有足够可靠的材料支持确定回答这个问题。"

# 兜底回答的固定前缀，界面会额外标注「演示保障模式」
FALLBACK_PREFIX = ""

# 相似度阈值：低于该值认为没有匹配到预审核问答，改为如实拒答。
#
# 这个值是标定出来的，不是拍的：对 165 条标准问法原样提问，得分中位数 0.70，
# 仅 3% 低于 0.35；而对 12 条「资料库确实没有」的问题，最高分只有 0.345。
# 取 0.42 可以把这 12 条全部挡住，同时不误伤真实命中。
#
# 阈值放宽会让「唐太宗对禄东赞说了什么」这类无证据问题被一条只提到
# 唐太宗和禄东赞的旁支条目接住 —— 答案本身没错，但它没有回答问题，
# 等于用「有来源」掩盖了「无证据」。这正是 No Context No Answer 要防的。
MATCH_THRESHOLD = 0.42

# 一次兜底回答最多引用多少条来源
MAX_CITATIONS = 3


class MockProvider:
    """预审核问答库 Provider。"""

    name = "mock"
    model = "fallback_faq"

    # ---------- FAQ 数据源 ----------

    @staticmethod
    def _load_faq(chapter_id: str | None) -> list[dict]:
        """优先读数据库 fallback_faq，库为空时读 content/<章>/faq.json。"""
        entries: list[dict] = []

        try:
            from sqlalchemy import select

            from app.db.postgres import SessionLocal
            from app.models import FallbackFaq

            with SessionLocal() as db:
                stmt = select(FallbackFaq).where(FallbackFaq.review_status == "approved")
                if chapter_id:
                    stmt = stmt.where(FallbackFaq.chapter_id == chapter_id)
                rows = db.execute(stmt).scalars().all()
                entries = [
                    {
                        "id": row.id,
                        "chapter_id": row.chapter_id,
                        "character_id": row.character_id,
                        "canonical_question": row.canonical_question,
                        "keywords": list(row.keywords or []),
                        "intent": row.intent,
                        "answer_markdown": row.answer_markdown,
                        "source_ids": list(row.source_ids or []),
                        "related_entity_ids": list(row.related_entity_ids or []),
                    }
                    for row in rows
                ]
        except Exception as exc:  # noqa: BLE001 - 数据库不可用不应阻断兜底
            logger.warning("读取 fallback_faq 失败，改用内容目录：%s", exc)

        if not entries:
            all_faq = content_loader.load_all_faq()
            entries = [
                faq
                for faq in all_faq
                if not chapter_id or faq.get("chapter_id") == chapter_id
            ]
            if not entries:
                # 章节不匹配时退回全部条目，至少能答上通用问题
                entries = all_faq

        return [e for e in entries if e.get("answer_markdown")]

    # ---------- 匹配 ----------

    @staticmethod
    def _score(question: str, entry: dict) -> float:
        """综合打分：关键词命中率 + 与标准问法的 bigram 相似度。"""
        normalized_question = normalize(question)
        if not normalized_question:
            return 0.0

        canonical = normalize(entry.get("canonical_question") or "")

        # 用户原样（或几乎原样）提了这条标准问法 —— 直接判定命中。
        # 推荐问题按钮走的就是这条路径，不能因为该条目 keywords 没覆盖自身
        # 问法就被阈值挡掉。
        if canonical and (
            normalized_question == canonical or normalized_question in canonical
        ):
            return 1.0

        keywords = [str(k) for k in (entry.get("keywords") or []) if k]
        keyword_hit = 0.0
        if keywords:
            hits = sum(1 for k in keywords if normalize(k) and normalize(k) in normalized_question)
            keyword_hit = hits / len(keywords)

        canonical_sim = jaccard(question, entry.get("canonical_question") or "")
        return round(0.6 * keyword_hit + 0.4 * canonical_sim, 4)

    def match(self, question: str, chapter_id: str | None) -> tuple[dict | None, float]:
        """返回最匹配的 FAQ 条目与得分。没有匹配时返回 (None, 最高分)。"""
        entries = self._load_faq(chapter_id)
        best: dict | None = None
        best_score = 0.0
        for entry in entries:
            score = self._score(question, entry)
            if score > best_score:
                best, best_score = entry, score
        if best_score < MATCH_THRESHOLD:
            return None, best_score
        return best, best_score

    # ---------- Provider 接口 ----------

    async def complete(self, messages: list[dict], **kw: Any) -> str:
        question = kw.get("question") or last_user_message(messages)
        chapter_id = kw.get("chapter_id")
        available_source_ids = set(kw.get("available_source_ids") or [])

        entry, score = self.match(question, chapter_id)

        if entry is None:
            payload = {
                "answer_markdown": NO_EVIDENCE_ANSWER,
                "citation_ids": [],
                "related_entity_ids": [],
                "uncertainty": "high",
                "_fallback": True,
                "_matched": False,
                "_score": score,
                "_faq_id": None,
            }
            return json.dumps(payload, ensure_ascii=False)

        source_ids = [s for s in (entry.get("source_ids") or []) if s]
        # 只保留调用方确认可用的来源，避免引用到未检索到的材料
        if available_source_ids:
            filtered = [s for s in source_ids if s in available_source_ids]
            source_ids = filtered or source_ids

        payload = {
            "answer_markdown": FALLBACK_PREFIX + (entry.get("answer_markdown") or ""),
            "citation_ids": source_ids[:MAX_CITATIONS],
            "related_entity_ids": list(entry.get("related_entity_ids") or []),
            "uncertainty": "low" if score >= 0.4 else "medium",
            "_fallback": True,
            "_matched": True,
            "_score": score,
            "_faq_id": entry.get("id"),
        }
        return json.dumps(payload, ensure_ascii=False)

    async def stream(self, messages: list[dict], **kw: Any) -> AsyncIterator[str]:
        """把兜底答案分块吐出，模拟流式体验。"""
        text = await self.complete(messages, **kw)
        try:
            answer = json.loads(text).get("answer_markdown") or ""
        except json.JSONDecodeError:
            answer = text

        step = 12
        for index in range(0, len(answer), step):
            yield answer[index : index + step]


def is_mock_provider() -> bool:
    """当前是否处于演示保障模式。"""
    return not settings.llm_configured
