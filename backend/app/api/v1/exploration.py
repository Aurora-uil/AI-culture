"""探索接口：会话、事件上报、进度、总结。

**进度上报失败不能阻断内容浏览** —— 所有写入路径都容错，
未知事件类型与重复上报一律返回 ok。
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import degrade_to, get_exploration_session_id
from app.db.postgres import get_db
from app.schemas.exploration import (
    EventAckOut,
    ExplorationProgressOut,
    ExplorationSummaryOut,
    SessionCreatedOut,
)
from app.services import exploration_service

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------- 请求体 ----------------


class CreateSessionRequest(BaseModel):
    chapter_id: str
    anonymous_user_id: str | None = None


class EventRequest(BaseModel):
    session_id: str | None = None
    chapter_id: str | None = None
    event_type: str
    entity_id: str | None = None
    relation_id: str | None = None
    source_id: str | None = None
    metadata: dict = Field(default_factory=dict)


class SummaryRequest(BaseModel):
    chapter_id: str
    session_id: str | None = None


# ---------------- 接口 ----------------


@router.post(
    "/exploration/sessions", response_model=SessionCreatedOut, summary="创建探索会话"
)
def create_session(
    payload: CreateSessionRequest, db: Session = Depends(get_db)
) -> SessionCreatedOut:
    """匿名会话，不采集身份证 / 手机号 / 敏感个人信息。"""
    session = exploration_service.create_session(
        db, payload.chapter_id, payload.anonymous_user_id
    )
    return SessionCreatedOut(session_id=session.id, chapter_id=session.chapter_id or "")


@router.post("/exploration/events", response_model=EventAckOut, summary="上报探索事件")
def record_event(
    payload: EventRequest,
    header_session: str | None = Depends(get_exploration_session_id),
    db: Session = Depends(get_db),
) -> EventAckOut:
    """容错上报。

    - 重复上报：不重复入库，返回 `duplicated=true`，HTTP 200。
    - 未知 event_type：记日志、仍返回 200，但不会计入进度。
    - 会话无效：丢弃该事件并返回 200。

    总之这里**永远不会**因为上报数据有问题而返回 4xx / 5xx。
    """
    result = exploration_service.record_event(
        db,
        session_id=payload.session_id or header_session,
        chapter_id=payload.chapter_id,
        event_type=payload.event_type,
        entity_id=payload.entity_id,
        relation_id=payload.relation_id,
        source_id=payload.source_id,
        metadata=payload.metadata,
    )
    return EventAckOut(
        ok=bool(result.get("ok", True)),
        duplicated=bool(result.get("duplicated", False)),
        progress=float(result.get("progress") or 0),
    )


@router.get(
    "/exploration/progress", response_model=ExplorationProgressOut, summary="探索进度"
)
@degrade_to(ExplorationProgressOut())
def get_progress(
    chapter_id: str | None = Query(default=None),
    session_id: str | None = Depends(get_exploration_session_id),
    db: Session = Depends(get_db),
) -> ExplorationProgressOut:
    """按各章 `progress_weights` 加权计算的 0–100 进度。

    没有会话 / 没有数据时返回全 0，而不是报错。
    """
    return exploration_service.get_progress(db, chapter_id, session_id)


@router.post(
    "/exploration/summary", response_model=ExplorationSummaryOut, summary="探索总结"
)
async def generate_summary(
    payload: SummaryRequest,
    header_session: str | None = Depends(get_exploration_session_id),
    db: Session = Depends(get_db),
) -> ExplorationSummaryOut:
    """只根据用户访问过的节点生成总结，不新增用户没探索过的事实。

    无 LLM Key 时用规则拼装 80–120 字，**不调用 LLM**。
    """
    return await exploration_service.generate_summary(
        db, payload.chapter_id, payload.session_id or header_session
    )
