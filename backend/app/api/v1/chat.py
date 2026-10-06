"""AI 对话接口。

**采用「先校验后流式」**：先在服务端完成 检索 → 改写 → 生成 → 护栏 → 核验，
全部通过之后才通过 SSE 把答案分块吐出去。这样界面上永远不会先出现
未经验证的内容再被撤回。

SSE 事件格式严格对齐 `frontend/src/api/endpoints.ts` 的 `askQuestion` 解析逻辑：

    event: status\\n
    data: {"status":"retrieving"}

    event: token\\n
    data: {"text":"从"}

    event: final\\n
    data: {...}

每条 data 都是**单行 JSON**（前端按 `\\n\\n` 切帧、按 `data:` 拼接）。
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.service import STATUS_MODEL_TIMEOUT, answer_question
from app.db.postgres import SessionLocal, get_db
from app.services import exploration_service
from app.models import (
    ChatMessage,
    ChatMessageCitation,
    ChatMessageFeedback,
    ChatSession,
    Entity,
)
from app.schemas.chat import (
    AnswerOut,
    ChatSessionOut,
    FeedbackOut,
    RegenerateResultOut,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# 流式吐字的块大小与间隔（仅用于呈现节奏，不影响内容）
STREAM_CHUNK_SIZE = 12
STREAM_INTERVAL_SECONDS = 0.012

UNKNOWN_SESSION_MESSAGE = "这次对话的记录已经失效，请重新开始提问。"

# chat_message_citations 的主键含 chunk_id，该列不可为空。
# 引用只精确到来源时（兜底问答库）用这个占位符。
SOURCE_LEVEL_CHUNK = "__source_level__"


# ---------------- 请求体 ----------------


class CreateChatSessionRequest(BaseModel):
    chapter_id: str
    character_id: str | None = None


class AskRequest(BaseModel):
    session_id: str
    question: str
    current_entity_id: str | None = None


class RegenerateRequest(BaseModel):
    pass


class FeedbackRequest(BaseModel):
    kind: str
    note: str | None = None


# ---------------- SSE 工具 ----------------


def _frame(event: str, payload: dict) -> str:
    """构造一个 SSE 帧。data 必须是单行 JSON。"""
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _chunk_text(text: str, size: int = STREAM_CHUNK_SIZE) -> list[str]:
    """把答案切成小片。按字符切分，中文不受影响。"""
    if not text:
        return []
    return [text[i : i + size] for i in range(0, len(text), size)]


# ---------------- 会话 ----------------


@router.post("/chat/sessions", response_model=ChatSessionOut, summary="创建对话会话")
def create_chat_session(
    payload: CreateChatSessionRequest, db: Session = Depends(get_db)
) -> ChatSessionOut:
    """建立对话会话。章节 / 角色不存在也照常创建，不阻断提问。"""
    session_id = f"chat_{uuid.uuid4().hex[:16]}"
    character_id = payload.character_id or None

    # 角色 / 章节不存在时置空，避免外键报错（内容尚未入库时也会走到这里）
    if character_id:
        from app.models import Character

        if db.get(Character, character_id) is None:
            character_id = None

    chapter_id = exploration_service.resolve_chapter_id(db, payload.chapter_id)

    session = ChatSession(
        id=session_id,
        chapter_id=chapter_id,
        character_id=character_id,
    )
    db.add(session)
    db.commit()

    return ChatSessionOut(
        session_id=session_id,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


# ---------------- 提问（SSE） ----------------


@router.post("/chat/messages", summary="提问（SSE 流式）")
async def post_message(payload: AskRequest, db: Session = Depends(get_db)):
    """提问并按 SSE 返回。

    事件顺序：status(retrieving) → [服务端完成全部校验] → status(generating)
    → token* → final
    """
    question = (payload.question or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="请先输入你想了解的问题。")

    chat_session = db.get(ChatSession, payload.session_id)
    chapter_id = _resolve_chapter_id(db, chat_session, payload.current_entity_id)

    if chat_session is None:
        # 会话丢失时补建，保证提问路径不会被一个过期的 ID 卡死
        chat_session = ChatSession(
            id=payload.session_id or f"chat_{uuid.uuid4().hex[:16]}",
            chapter_id=exploration_service.resolve_chapter_id(db, chapter_id),
        )
        try:
            db.add(chat_session)
            db.commit()
        except Exception:  # noqa: BLE001
            db.rollback()

    # 只把「纯值」带进生成器。
    # FastAPI 会在响应体开始发送前关闭依赖里的 Session，生成器里再用 ORM 对象
    # 会触发 DetachedInstanceError。所以生成器自己开一个 Session。
    session_id = chat_session.id
    character_id = chat_session.character_id
    _save_message(
        db,
        session_id=session_id,
        role="user",
        content=question,
        status="DONE",
    )

    async def event_stream():
        yield _frame("status", {"status": "retrieving"})

        stream_db = SessionLocal()
        try:
            try:
                result = await answer_question(
                    stream_db,
                    chapter_id=chapter_id,
                    question=question,
                    character_id=character_id,
                    current_entity_id=payload.current_entity_id,
                )
            except Exception as exc:  # noqa: BLE001 - 任何异常都要转成中文提示
                logger.exception("回答流程异常：%s", exc)
                yield _frame("error", {"message": "服务暂时不可用，请稍后重试。"})
                yield _frame(
                    "final",
                    {
                        "message_id": "",
                        "citations": [],
                        "related_entities": [],
                        "uncertainty": "high",
                        "status": STATUS_MODEL_TIMEOUT,
                        "response_tier": "faq_fallback",
                        "message": "AI 讲述暂时没有完成。你可以重试，或先查看相关史料。",
                    },
                )
                return

            message_id = _persist_answer(
                stream_db, session_id=session_id, result=result, question=question
            )
        finally:
            stream_db.close()

        yield _frame("status", {"status": "generating"})

        # 校验已通过，开始吐字
        for piece in _chunk_text(result.answer_markdown):
            yield _frame("token", {"text": piece})
            await asyncio.sleep(STREAM_INTERVAL_SECONDS)

        yield _frame(
            "final",
            {
                "message_id": message_id,
                "citations": [c.model_dump() for c in result.citations],
                "related_entities": [e.model_dump() for e in result.related_entities],
                "uncertainty": result.uncertainty,
                "status": result.status,
                "response_tier": result.response_tier,
                "message": result.message,
            },
        )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            # Nginx 等反代下关闭缓冲，保证逐字效果
            "X-Accel-Buffering": "no",
        },
    )


def _resolve_chapter_id(
    db: Session, chat_session: ChatSession | None, current_entity_id: str | None
) -> str | None:
    """确定本次提问所属章节：会话 → 当前实体 → 空。"""
    if chat_session is not None and chat_session.chapter_id:
        return chat_session.chapter_id
    if current_entity_id:
        entity = db.get(Entity, current_entity_id)
        if entity is not None:
            return entity.chapter_id
    return None


def _save_message(
    db: Session,
    *,
    session_id: str,
    role: str,
    content: str,
    answer_mode: str | None = None,
    status: str = "DONE",
    uncertainty: str | None = None,
    response_tier: str | None = None,
    model_name: str | None = None,
    prompt_version: str | None = None,
    related_entity_ids: list[str] | None = None,
) -> str:
    """落库一条消息。失败只记日志 —— 不能因为存不上就不回答。"""
    message_id = f"msg_{uuid.uuid4().hex[:16]}"
    try:
        db.add(
            ChatMessage(
                id=message_id,
                session_id=session_id,
                role=role,
                content=content,
                answer_mode=answer_mode,
                status=status,
                uncertainty=uncertainty,
                response_tier=response_tier,
                model_name=model_name,
                prompt_version=prompt_version,
                related_entity_ids=related_entity_ids or [],
            )
        )
        db.commit()
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        logger.warning("对话消息落库失败（不影响回答）：%s", exc)
    return message_id


def _persist_answer(
    db: Session, *, session_id: str, result: AnswerOut, question: str
) -> str:
    """保存助手消息与引用。"""
    message_id = _save_message(
        db,
        session_id=session_id,
        role="assistant",
        content=result.answer_markdown,
        status=result.status,
        uncertainty=result.uncertainty,
        response_tier=result.response_tier,
        model_name=result.model_name,
        prompt_version=result.prompt_version,
        related_entity_ids=result.related_entity_ids,
    )

    # 联网搜索来源是本次请求动态生成的 `web:*` 标识，不存在于本地
    # sources 表；它们已经随 SSE 返回给前端展示，不能再写入带来源外键的
    # chat_message_citations。这里只持久化本地、可复用的来源引用。
    persistable_citations = [
        citation
        for citation in result.citations
        if not citation.source_id.startswith("web:")
    ]
    if not persistable_citations:
        return message_id

    try:
        for index, citation in enumerate(persistable_citations):
            db.add(
                ChatMessageCitation(
                    message_id=message_id,
                    source_id=citation.source_id,
                    # schema.sql 里 (message_id, source_id, chunk_id) 是主键，
                    # 主键列隐含 NOT NULL，因此这里必须给非空值。
                    # 兜底问答库只到来源粒度，用固定占位符表示「该来源级的引用」。
                    chunk_id=citation.chunk_id or SOURCE_LEVEL_CHUNK,
                    claim_id=None,
                    sort_order=index,
                )
            )
        db.commit()
    except Exception as exc:  # noqa: BLE001 - 引用存不上不影响回答本身
        db.rollback()
        logger.warning("引用落库失败（不影响回答）：%s", exc)
    return message_id


# ---------------- 重新生成 ----------------


@router.post(
    "/chat/messages/{message_id}/regenerate",
    response_model=RegenerateResultOut,
    summary="重新生成回答",
)
async def regenerate(
    message_id: str, payload: RegenerateRequest, db: Session = Depends(get_db)
) -> RegenerateResultOut:
    """基于该消息之前最近的一条用户提问重新生成，并保存为新消息。"""
    message = db.get(ChatMessage, message_id)
    if message is None:
        raise HTTPException(status_code=404, detail="这条回答已经不存在了，请重新提问。")

    question = _find_previous_question(db, message)
    if not question:
        raise HTTPException(status_code=400, detail="找不到可重新生成的问题，请重新提问。")

    chat_session = db.get(ChatSession, message.session_id)
    chapter_id = _resolve_chapter_id(db, chat_session, None)

    result = await answer_question(
        db,
        chapter_id=chapter_id,
        question=question,
        character_id=chat_session.character_id if chat_session else None,
    )

    new_id = _persist_answer(db, session_id=message.session_id, result=result, question=question)

    return RegenerateResultOut(
        message_id=new_id,
        citations=result.citations,
        related_entities=result.related_entities,
        uncertainty=result.uncertainty,
        status=result.status,
        response_tier=result.response_tier,
        message=result.message,
        answer_markdown=result.answer_markdown,
        answer_mode="factual",
    )


def _find_previous_question(db: Session, message: ChatMessage) -> str | None:
    """找该消息之前最近的一条用户提问。"""
    row = db.execute(
        select(ChatMessage.content)
        .where(
            ChatMessage.session_id == message.session_id,
            ChatMessage.role == "user",
            ChatMessage.created_at <= message.created_at,
        )
        .order_by(ChatMessage.created_at.desc())
        .limit(1)
    ).scalar()
    if row:
        return row
    # 兜底：该会话里任意一条用户提问
    return db.execute(
        select(ChatMessage.content)
        .where(ChatMessage.session_id == message.session_id, ChatMessage.role == "user")
        .order_by(ChatMessage.created_at.desc())
        .limit(1)
    ).scalar()


# ---------------- 反馈 ----------------


@router.post(
    "/chat/messages/{message_id}/feedback", response_model=FeedbackOut, summary="回答反馈"
)
def submit_feedback(
    message_id: str, payload: FeedbackRequest, db: Session = Depends(get_db)
) -> FeedbackOut:
    """记录点赞 / 点踩 / 报告问题。消息不存在时返回 ok=false 而不是 500。"""
    if db.get(ChatMessage, message_id) is None:
        return FeedbackOut(ok=False, message_id=message_id, kind=payload.kind)

    try:
        db.add(
            ChatMessageFeedback(
                id=f"fb_{uuid.uuid4().hex[:16]}",
                message_id=message_id,
                kind=payload.kind or "other",
                note=payload.note,
            )
        )
        db.commit()
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        logger.warning("反馈落库失败：%s", exc)
        return FeedbackOut(ok=False, message_id=message_id, kind=payload.kind)

    return FeedbackOut(ok=True, message_id=message_id, kind=payload.kind)
