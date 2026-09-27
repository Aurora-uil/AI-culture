"""内容层 ORM 模型：chapters / sources / entities / claims / relations / rag_chunks。

主键一律为稳定业务 ID（text），与图谱、前端共用同一套 ID。
"""

from __future__ import annotations

from sqlalchemy import (
    ARRAY,
    Boolean,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import DateTime


class Base(DeclarativeBase):
    """所有 ORM 模型的公共基类。"""


class Chapter(Base):
    """章节配置。见 content/chapters.json 与 schema.sql 的 chapters 表。"""

    __tablename__ = "chapters"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    era: Mapped[str] = mapped_column(Text, nullable=False)
    theme: Mapped[str] = mapped_column(Text, nullable=False)  # 关键词：相遇/交融/交流/共存/归属/传承
    title: Mapped[str] = mapped_column(Text, nullable=False)
    date_label: Mapped[str | None] = mapped_column(Text)
    guiding_question: Mapped[str] = mapped_column(Text, nullable=False)
    display_question: Mapped[str | None] = mapped_column(Text)
    hero_asset: Mapped[str | None] = mapped_column(Text)
    accent: Mapped[str | None] = mapped_column(Text)
    primary_interaction: Mapped[str | None] = mapped_column(Text)
    ai_character_id: Mapped[str | None] = mapped_column(Text)
    core_entity_ids: Mapped[list | None] = mapped_column(JSONB, default=list)
    narration: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int | None] = mapped_column(Integer, default=0)
    status: Mapped[str | None] = mapped_column(Text, default="approved")
    # alters.sql 补充：前端路由用 slug（han / northern-wei / ...）
    slug: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Source(Base):
    """来源表。source_level 绝不能为空，否则该来源的 chunk 永远检索不到。"""

    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str | None] = mapped_column(Text)
    institution: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    source_level: Mapped[str] = mapped_column(Text, nullable=False)
    publication_year: Mapped[int | None] = mapped_column(Integer)
    public_url: Mapped[str | None] = mapped_column(Text)
    bibliography: Mapped[str | None] = mapped_column(Text)
    license_note: Mapped[str | None] = mapped_column(Text)
    # 清代章节要求：qing_court / museum_curatorial / modern_scholarship / ...
    source_perspective: Mapped[str | None] = mapped_column(Text)
    review_status: Mapped[str] = mapped_column(Text, nullable=False, default="approved")


class Entity(Base):
    """实体。类型专属字段放 extra（jsonb），避免为每种类型建表。"""

    __tablename__ = "entities"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    entity_type: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str | None] = mapped_column(Text)
    subtitle: Mapped[str | None] = mapped_column(Text)
    era: Mapped[str | None] = mapped_column(Text)
    chapter_id: Mapped[str | None] = mapped_column(Text, ForeignKey("chapters.id", ondelete="CASCADE"))
    # alters.sql 补充：跨章共用实体记录全部所属章节
    chapter_ids: Mapped[list | None] = mapped_column(JSONB, default=list)
    short_summary: Mapped[str | None] = mapped_column(Text)
    body_markdown: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text)
    verification_label: Mapped[str] = mapped_column(Text, nullable=False, default="historical_fact")
    review_status: Mapped[str] = mapped_column(Text, nullable=False, default="approved")
    sort_order: Mapped[int | None] = mapped_column(Integer, default=0)
    extra: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    created_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Claim(Base):
    """Claim 是溯源的最小单位：不是「实体挂来源」，而是「具体事实主张挂来源」。"""

    __tablename__ = "claims"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    entity_id: Mapped[str | None] = mapped_column(Text, ForeignKey("entities.id", ondelete="CASCADE"))
    relation_id: Mapped[str | None] = mapped_column(Text)
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    claim_type: Mapped[str] = mapped_column(Text, nullable=False, default="fact")
    controversy_status: Mapped[str] = mapped_column(Text, nullable=False, default="stable")
    review_status: Mapped[str] = mapped_column(Text, nullable=False, default="approved")


class ClaimSource(Base):
    """Claim ↔ Source 多对多，带 locator（页码 / 段落）。"""

    __tablename__ = "claim_sources"

    claim_id: Mapped[str] = mapped_column(
        Text, ForeignKey("claims.id", ondelete="CASCADE"), primary_key=True
    )
    source_id: Mapped[str] = mapped_column(
        Text, ForeignKey("sources.id", ondelete="CASCADE"), primary_key=True
    )
    locator: Mapped[str | None] = mapped_column(Text)
    support_type: Mapped[str | None] = mapped_column(Text, default="direct")
    note: Mapped[str | None] = mapped_column(Text)


class Relation(Base):
    """图谱边。同时写入 Neo4j；PostgreSQL 保存一份用于内容管理与兜底查询。"""

    __tablename__ = "relations"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    source_entity_id: Mapped[str] = mapped_column(
        Text, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False
    )
    target_entity_id: Mapped[str] = mapped_column(
        Text, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False
    )
    relation_type: Mapped[str] = mapped_column(Text, nullable=False)
    display_label: Mapped[str] = mapped_column(Text, nullable=False)
    claim_type: Mapped[str] = mapped_column(Text, nullable=False, default="fact")
    review_status: Mapped[str] = mapped_column(Text, nullable=False, default="approved")
    source_ids: Mapped[list | None] = mapped_column(JSONB, default=list)
    claim_ids: Mapped[list | None] = mapped_column(JSONB, default=list)
    time_scope: Mapped[str | None] = mapped_column(Text)
    route_scope: Mapped[str | None] = mapped_column(Text)
    certainty: Mapped[str | None] = mapped_column(Text)
    source_perspective: Mapped[str | None] = mapped_column(Text)
    chapter_id: Mapped[str | None] = mapped_column(Text, ForeignKey("chapters.id", ondelete="CASCADE"))


class RagChunk(Base):
    """RAG 切片。向量以 double precision[] 存储，换供应商不会全表报错。"""

    __tablename__ = "rag_chunks"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    source_id: Mapped[str | None] = mapped_column(Text, ForeignKey("sources.id", ondelete="CASCADE"))
    chapter_ids: Mapped[list | None] = mapped_column(JSONB, default=list)
    entity_ids: Mapped[list | None] = mapped_column(JSONB, default=list)
    claim_ids: Mapped[list | None] = mapped_column(JSONB, default=list)
    title: Mapped[str | None] = mapped_column(Text)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer)
    source_level: Mapped[str | None] = mapped_column(Text)
    meaning_status: Mapped[str | None] = mapped_column(Text)
    review_status: Mapped[str] = mapped_column(Text, nullable=False, default="approved")
    embedding: Mapped[list | None] = mapped_column(ARRAY(Float))
    embedding_dim: Mapped[int | None] = mapped_column(Integer)


class Character(Base):
    """AI 角色配置。disclaimer 必须在界面固定显示。"""

    __tablename__ = "characters"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    character_type: Mapped[str] = mapped_column(Text, nullable=False)
    base_entity_id: Mapped[str | None] = mapped_column(Text, ForeignKey("entities.id", ondelete="SET NULL"))
    chapter_id: Mapped[str | None] = mapped_column(Text, ForeignKey("chapters.id", ondelete="CASCADE"))
    subtitle: Mapped[str | None] = mapped_column(Text)
    disclaimer: Mapped[str] = mapped_column(Text, nullable=False)
    system_prompt_version: Mapped[str | None] = mapped_column(Text, default="v1")
    enabled: Mapped[bool | None] = mapped_column(Boolean, default=True)
    # alters.sql 补充
    image_url: Mapped[str | None] = mapped_column(Text)


class FallbackFaq(Base):
    """演示保障问答库：断网 / 无 Key / 超时时使用。"""

    __tablename__ = "fallback_faq"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    chapter_id: Mapped[str | None] = mapped_column(Text, ForeignKey("chapters.id", ondelete="CASCADE"))
    character_id: Mapped[str | None] = mapped_column(Text)
    canonical_question: Mapped[str] = mapped_column(Text, nullable=False)
    keywords: Mapped[list | None] = mapped_column(JSONB, default=list)
    intent: Mapped[str | None] = mapped_column(Text)
    answer_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    source_ids: Mapped[list | None] = mapped_column(JSONB, default=list)
    related_entity_ids: Mapped[list | None] = mapped_column(JSONB, default=list)
    review_status: Mapped[str] = mapped_column(Text, nullable=False, default="approved")
