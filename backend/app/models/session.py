"""会话与探索 ORM 模型。

匿名用户，不采集身份证 / 手机号 / 敏感个人信息。
"""

from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime, Numeric

from app.models.content import Base


class ExplorationSession(Base):
    """探索会话。progress 为 0–100 的加权完成度。"""

    __tablename__ = "exploration_sessions"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    anonymous_user_id: Mapped[str | None] = mapped_column(Text)
    chapter_id: Mapped[str | None] = mapped_column(Text, ForeignKey("chapters.id", ondelete="CASCADE"))
    started_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_active_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    progress: Mapped[float | None] = mapped_column(Numeric, default=0)


class ExplorationEvent(Base):
    """探索事件。重复上报不报错，未知 event_type 记日志但不 500。"""

    __tablename__ = "exploration_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[str | None] = mapped_column(Text, ForeignKey("exploration_sessions.id", ondelete="CASCADE"))
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    entity_id: Mapped[str | None] = mapped_column(Text)
    relation_id: Mapped[str | None] = mapped_column(Text)
    source_id: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ExplorationNodeState(Base):
    """会话已访问节点。用于图谱 explored 标记。"""

    __tablename__ = "exploration_node_state"

    session_id: Mapped[str] = mapped_column(
        Text, ForeignKey("exploration_sessions.id", ondelete="CASCADE"), primary_key=True
    )
    entity_id: Mapped[str] = mapped_column(Text, primary_key=True)
    first_seen_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    view_count: Mapped[int | None] = mapped_column(Integer, default=1)


class ChatSession(Base):
    """对话会话。"""

    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    exploration_session_id: Mapped[str | None] = mapped_column(Text)
    chapter_id: Mapped[str | None] = mapped_column(Text, ForeignKey("chapters.id", ondelete="CASCADE"))
    character_id: Mapped[str | None] = mapped_column(Text, ForeignKey("characters.id", ondelete="SET NULL"))
    created_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ChatMessage(Base):
    """对话消息。status / response_tier 必须如实记录，界面据此标注。"""

    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    session_id: Mapped[str] = mapped_column(Text, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    answer_mode: Mapped[str | None] = mapped_column(Text, default="narrative")
    # DONE | NO_EVIDENCE | MODEL_TIMEOUT | VALIDATION_FAILED | FALLBACK_DEMO
    status: Mapped[str | None] = mapped_column(Text, default="DONE")
    uncertainty: Mapped[str | None] = mapped_column(Text)
    # live_rag | local_retrieval | faq_fallback
    response_tier: Mapped[str | None] = mapped_column(Text)
    model_name: Mapped[str | None] = mapped_column(Text)
    prompt_version: Mapped[str | None] = mapped_column(Text)
    # alters.sql 补充
    related_entity_ids: Mapped[list | None] = mapped_column(JSONB, default=list)
    created_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ChatMessageCitation(Base):
    """回答引用。界面「史料依据」面板据此展示。"""

    __tablename__ = "chat_message_citations"

    message_id: Mapped[str] = mapped_column(
        Text, ForeignKey("chat_messages.id", ondelete="CASCADE"), primary_key=True
    )
    source_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("sources.id", ondelete="SET NULL"), primary_key=True
    )
    chunk_id: Mapped[str | None] = mapped_column(Text, primary_key=True)
    claim_id: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int | None] = mapped_column(Integer, default=0)


class ChatMessageFeedback(Base):
    """回答反馈，alters.sql 补充表。"""

    __tablename__ = "chat_message_feedback"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    message_id: Mapped[str] = mapped_column(
        Text, ForeignKey("chat_messages.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
