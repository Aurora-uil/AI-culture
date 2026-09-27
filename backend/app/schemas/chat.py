"""对话相关出参模型。

`final` 事件必须带：message_id, citations[], related_entities[], uncertainty,
status, response_tier。界面据此标注是实时 AI 还是兜底演示。
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatSessionOut(BaseModel):
    """`POST /chat/sessions` 返回体。"""

    session_id: str
    created_at: str = ""


class CitationOut(BaseModel):
    """对应前端 `Citation`。

    `chunk_id` 是本项目内部字段（前端忽略），用于 chat_message_citations 落库：
    该表主键为 (message_id, source_id, chunk_id)，chunk_id 不能为空。
    """

    source_id: str
    title: str = ""
    institution: str = ""
    source_level: str | None = None
    public_url: str | None = None
    claim_text: str | None = None
    chunk_id: str | None = None


class RelatedEntityOut(BaseModel):
    """对应前端 `ChatMessage.related_entities` 的元素。"""

    id: str
    name: str = ""
    display_name: str | None = None
    entity_type: str = "Concept"


class AnswerOut(BaseModel):
    """AI 层编排的结构化结果（app/ai/service.py 的返回类型）。"""

    answer_markdown: str = ""
    citation_ids: list[str] = Field(default_factory=list)
    related_entity_ids: list[str] = Field(default_factory=list)
    uncertainty: str = "low"
    status: str = "DONE"
    response_tier: str = "faq_fallback"
    # 护栏命中说明（内部诊断用，不直接展示给用户）
    guard_hits: list[str] = Field(default_factory=list)
    # 已展开的引用与关联实体，便于路由层直接使用
    citations: list[CitationOut] = Field(default_factory=list)
    related_entities: list[RelatedEntityOut] = Field(default_factory=list)
    # 面向用户的提示语（NO_EVIDENCE / FALLBACK_DEMO 场景）
    message: str | None = None
    model_name: str | None = None
    prompt_version: str | None = None


class FinalEventOut(BaseModel):
    """SSE `final` 事件载荷。"""

    message_id: str
    citations: list[CitationOut] = Field(default_factory=list)
    related_entities: list[RelatedEntityOut] = Field(default_factory=list)
    uncertainty: str = "low"
    status: str = "DONE"
    response_tier: str = "faq_fallback"
    message: str | None = None


class RegenerateResultOut(FinalEventOut):
    """`POST /chat/messages/{id}/regenerate` 返回体（非流式，直接给完整结果）。"""

    answer_markdown: str = ""
    answer_mode: str = "narrative"


class FeedbackOut(BaseModel):
    """`POST /chat/messages/{id}/feedback` 返回体。"""

    ok: bool = True
    message_id: str = ""
    kind: str = ""
