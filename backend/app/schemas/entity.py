"""实体 / 来源 / Claim 出参模型。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SourceClaimOut(BaseModel):
    """设计系统 §36：来源必须说明它支持了哪些具体事实，不能只列参考文献名。"""

    claim_id: str
    text: str


class SourceOut(BaseModel):
    """对应前端 `Source`。"""

    id: str
    title: str
    author: str | None = None
    institution: str = ""
    source_type: str = "official"
    source_level: str = "C"
    publication_year: int | None = None
    public_url: str | None = None
    bibliography: str | None = None
    license_note: str | None = None
    source_perspective: str | None = None
    review_status: str = "approved"
    claims: list[SourceClaimOut] = Field(default_factory=list)


class ClaimOut(BaseModel):
    """对应前端 `Claim`。"""

    id: str
    entity_id: str | None = None
    relation_id: str | None = None
    claim_text: str = ""
    claim_type: str = "fact"
    controversy_status: str = "stable"
    review_status: str = "approved"
    source_ids: list[str] = Field(default_factory=list)


class EntityOut(BaseModel):
    """对应前端 `Entity`。"""

    id: str
    entity_type: str
    name: str
    display_name: str | None = None
    subtitle: str | None = None
    era: str | None = None
    chapter_id: str | None = None
    # 跨章共用实体（如「长安」同属汉代与唐代）的全部所属章节
    chapter_ids: list[str] = Field(default_factory=list)
    short_summary: str | None = None
    body_markdown: str | None = None
    image_url: str | None = None
    verification_label: str = "historical_fact"
    review_status: str = "approved"
    sort_order: int = 0
    extra: dict = Field(default_factory=dict)
    source_count: int = 0
    related_entity_count: int = 0


class EntitySourcesOut(BaseModel):
    """`GET /entities/{id}/sources` 的返回体。"""

    entity_id: str
    sources: list[SourceOut] = Field(default_factory=list)
