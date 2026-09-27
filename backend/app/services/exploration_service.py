"""探索服务：会话、事件上报、加权进度、探索总结。

硬性要求：
- **事件上报必须容错**：重复上报不报错，未知 event_type 记日志但不 500。
  各章规格都写明「进度上报失败不能阻断内容浏览」。
- 无 LLM Key 时 `summary` 用规则生成（基于 visited 节点拼装 80–120 字），
  **不调用 LLM**。
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Chapter,
    Entity,
    ExplorationEvent,
    ExplorationNodeState,
    ExplorationSession,
    Relation,
    Source,
)
from app.schemas.exploration import (
    ChapterProgressOut,
    ExplorationProgressOut,
    ExplorationSummaryOut,
    ProgressTotalsOut,
)
from app.services import content_loader

logger = logging.getLogger(__name__)

# 已知事件类型（来自 frontend/src/types/index.ts 的 ExplorationEventType）
KNOWN_EVENT_TYPES = {
    "CHAPTER_ENTER",
    "SCENE_ENTER",
    "ENTITY_VIEW",
    "LENS_OPEN",
    "CHAT_ASK",
    "CHAT_SOURCE_VIEW",
    "GRAPH_OPEN",
    "GRAPH_NODE_EXPAND",
    "RELATION_EVIDENCE_VIEW",
    "SOURCE_VIEW",
    "CHAPTER_COMPLETE",
    "COCREATION_START",
    "COCREATION_COMPLETE",
    "ARTWORK_HOTSPOT_VIEW",
    "OUTSIDE_RELATION_EXPAND",
    "MIGRATION_SEGMENT_VIEW",
}

# 元代规格的进度权重（进入场景10 / 三个文字15 / 六个文字15 / 查看来源10 /
# 完成AI问答20 / 查看图谱10 / 展开关系10 / 查看证据10 = 100）。
# 各章可在 content/<dir>/extra.json 的 progress_weights 里按同名 key 覆盖。
DEFAULT_PROGRESS_WEIGHTS: dict[str, float] = {
    "SCENE_ENTER": 10,
    "ENTITY_VIEW_3": 15,
    "ENTITY_VIEW_ALL": 15,
    "SOURCE_VIEW": 10,
    "CHAT_ASK": 20,
    "GRAPH_OPEN": 10,
    "GRAPH_NODE_EXPAND": 10,
    "RELATION_EVIDENCE_VIEW": 10,
}

# 「打开任意 N 个文字」与「全部打开」的阈值
ENTITY_VIEW_PARTIAL_THRESHOLD = 3
ENTITY_VIEW_FULL_THRESHOLD = 6

# content/<章>/extra.json 里 progress_weights 的 key 是各章自定义的语义名，
# 需要映射到本模块的规则 key。映射不到时再按关键词猜一次。
WEIGHT_KEY_ALIASES: dict[str, str] = {
    "enter_scene": "SCENE_ENTER",
    "scene_enter": "SCENE_ENTER",
    "chapter_enter": "SCENE_ENTER",
    "open_any_three_scripts": "ENTITY_VIEW_3",
    "open_three_scripts": "ENTITY_VIEW_3",
    "entity_view_3": "ENTITY_VIEW_3",
    "open_all_six_scripts": "ENTITY_VIEW_ALL",
    "open_all_scripts": "ENTITY_VIEW_ALL",
    "entity_view_all": "ENTITY_VIEW_ALL",
    "view_yuntai_sources": "SOURCE_VIEW",
    "view_sources": "SOURCE_VIEW",
    "source_view": "SOURCE_VIEW",
    "complete_ai_qa": "CHAT_ASK",
    "complete_qa": "CHAT_ASK",
    "chat_ask": "CHAT_ASK",
    "view_graph": "GRAPH_OPEN",
    "graph_open": "GRAPH_OPEN",
    "expand_one_relation": "GRAPH_NODE_EXPAND",
    "expand_relation": "GRAPH_NODE_EXPAND",
    "graph_node_expand": "GRAPH_NODE_EXPAND",
    "view_relation_evidence": "RELATION_EVIDENCE_VIEW",
    "relation_evidence_view": "RELATION_EVIDENCE_VIEW",
}


def _alias_to_rule_key(raw_key: str) -> str | None:
    """语义 key → 规则 key。先查别名表，再按关键词猜。"""
    key = (raw_key or "").strip().lower()
    if not key:
        return None
    if key in WEIGHT_KEY_ALIASES:
        return WEIGHT_KEY_ALIASES[key]

    # 关键词兜底：不同章的 key 命名不完全一致
    if "evidence" in key and "relation" in key:
        return "RELATION_EVIDENCE_VIEW"
    if "expand" in key:
        return "GRAPH_NODE_EXPAND"
    if "graph" in key:
        return "GRAPH_OPEN"
    if "source" in key:
        return "SOURCE_VIEW"
    if "qa" in key or "chat" in key or "ask" in key:
        return "CHAT_ASK"
    if "script" in key or "character" in key or "entity" in key:
        if "all" in key or "six" in key or "6" in key:
            return "ENTITY_VIEW_ALL"
        return "ENTITY_VIEW_3"
    if "scene" in key or "enter" in key:
        return "SCENE_ENTER"
    return None


def _extract_weight_entries(raw) -> list[tuple[str, float]]:
    """把 progress_weights 归一化成 [(语义 key, 权重)]。

    内容层实际使用的是列表形式：
        [{"key": "enter_scene", "label": "进入场景", "weight": 10}, ...]
    这里同时兼容字典形式 `{"SCENE_ENTER": 10}`。
    """
    entries: list[tuple[str, float]] = []
    if isinstance(raw, dict):
        for key, value in raw.items():
            if isinstance(value, (int, float)):
                entries.append((str(key), float(value)))
    elif isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            key = item.get("key") or item.get("event_type") or item.get("id")
            weight = item.get("weight", item.get("value"))
            if key and isinstance(weight, (int, float)):
                entries.append((str(key), float(weight)))
    return entries


# ============================================================
# 会话
# ============================================================


def resolve_chapter_id(db: Session, chapter_id: str | None) -> str | None:
    """章节 ID 存在性校验。

    `exploration_sessions.chapter_id` / `chat_sessions.chapter_id` 都有外键约束，
    内容尚未入库时直接写入会触发 IntegrityError。这里统一收敛为 None ——
    接口照常返回，只是该会话暂时不归属任何章节。
    """
    if not chapter_id:
        return None
    try:
        if db.get(Chapter, chapter_id) is not None:
            return chapter_id
    except Exception:  # noqa: BLE001 - 数据库不可用时也不该让创建会话失败
        return None
    logger.info("章节 %s 尚不存在，会话暂不绑定章节", chapter_id)
    return None


def create_session(
    db: Session, chapter_id: str, anonymous_user_id: str | None = None
) -> ExplorationSession:
    """新建探索会话。会话 ID 前缀 exp_ 便于日志辨认。"""
    session = ExplorationSession(
        id=f"exp_{uuid.uuid4().hex[:16]}",
        anonymous_user_id=anonymous_user_id,
        chapter_id=resolve_chapter_id(db, chapter_id),
        progress=0,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session(db: Session, session_id: str | None) -> ExplorationSession | None:
    if not session_id:
        return None
    return db.get(ExplorationSession, session_id)


def latest_session(db: Session, chapter_id: str | None = None) -> ExplorationSession | None:
    """最近活跃的会话。前端未传 session_id 时用它兜底。"""
    stmt = select(ExplorationSession)
    if chapter_id:
        stmt = stmt.where(ExplorationSession.chapter_id == chapter_id)
    return db.execute(
        stmt.order_by(ExplorationSession.last_active_at.desc()).limit(1)
    ).scalars().first()


# ============================================================
# 事件上报
# ============================================================


def _event_chapter_filter(chapter_id: str):
    """事件表没有 chapter_id 列，章节归属存在 metadata.chapter_id。"""
    return ExplorationEvent.metadata_["chapter_id"].astext == chapter_id


def record_event(
    db: Session,
    *,
    session_id: str | None,
    chapter_id: str | None,
    event_type: str,
    entity_id: str | None = None,
    relation_id: str | None = None,
    source_id: str | None = None,
    metadata: dict | None = None,
) -> dict:
    """记录一条探索事件。

    容错策略（任何一条都不允许冒泡成 500）：
    - 未知 event_type：记日志，仍然入库，进度计算时自然忽略。
    - 会话不存在 / 未提供：丢弃该事件，返回 ok=True。
    - 重复上报：不重复入库，返回 duplicated=True。
    """
    metadata = dict(metadata or {})
    if chapter_id:
        metadata["chapter_id"] = chapter_id

    if event_type not in KNOWN_EVENT_TYPES:
        logger.info("收到未知探索事件类型（已忽略计入进度）：%s", event_type)

    session = get_session(db, session_id)
    if session is None:
        # 没有会话就不落库：事件表有外键约束，硬插会 500
        logger.info("探索事件缺少有效会话，已忽略：session=%s type=%s", session_id, event_type)
        return {"ok": True, "duplicated": False, "progress": 0.0}

    # 重复上报检测：同一会话 + 同类型 + 同对象视为重复
    duplicate = db.execute(
        select(ExplorationEvent.id).where(
            ExplorationEvent.session_id == session.id,
            ExplorationEvent.event_type == event_type,
            ExplorationEvent.entity_id.is_(entity_id) if entity_id is None else ExplorationEvent.entity_id == entity_id,
            ExplorationEvent.relation_id.is_(relation_id) if relation_id is None else ExplorationEvent.relation_id == relation_id,
            ExplorationEvent.source_id.is_(source_id) if source_id is None else ExplorationEvent.source_id == source_id,
        ).limit(1)
    ).scalar()

    if duplicate:
        return {"ok": True, "duplicated": True, "progress": float(session.progress or 0)}

    try:
        db.add(
            ExplorationEvent(
                session_id=session.id,
                event_type=event_type,
                entity_id=entity_id,
                relation_id=relation_id,
                source_id=source_id,
                metadata_=metadata,
            )
        )
        session.last_active_at = func.now()

        # 维护节点访问状态（图谱 explored 标记的来源）
        if entity_id:
            state = db.get(ExplorationNodeState, (session.id, entity_id))
            if state is None:
                db.add(ExplorationNodeState(session_id=session.id, entity_id=entity_id, view_count=1))
            else:
                state.view_count = int(state.view_count or 1) + 1

        db.commit()
    except Exception as exc:  # noqa: BLE001 - 上报失败绝不能影响内容浏览
        db.rollback()
        logger.warning("探索事件入库失败（已忽略）：%s", exc)
        return {"ok": True, "duplicated": False, "progress": float(session.progress or 0)}

    progress = _recompute_progress(db, session)
    return {"ok": True, "duplicated": False, "progress": progress}


# ============================================================
# 进度
# ============================================================


def _aggregate(db: Session, session_id: str, chapter_id: str) -> dict:
    """聚合某会话在某章的探索行为。"""
    rows = db.execute(
        select(
            ExplorationEvent.event_type,
            ExplorationEvent.entity_id,
            ExplorationEvent.relation_id,
            ExplorationEvent.source_id,
        ).where(
            ExplorationEvent.session_id == session_id,
            _event_chapter_filter(chapter_id),
        )
    ).all()

    event_types: set[str] = set()
    entity_ids: set[str] = set()
    relation_ids: set[str] = set()
    source_ids: set[str] = set()
    chat_count = 0

    for event_type, entity_id, relation_id, source_id in rows:
        event_types.add(event_type)
        if entity_id:
            entity_ids.add(entity_id)
        if relation_id:
            relation_ids.add(relation_id)
        if source_id:
            source_ids.add(source_id)
        if event_type == "CHAT_ASK":
            chat_count += 1

    return {
        "event_types": event_types,
        "entity_ids": entity_ids,
        "relation_ids": relation_ids,
        "source_ids": source_ids,
        "chat_count": chat_count,
    }


def _weights_for(db: Session, chapter_id: str) -> dict[str, float]:
    """进度权重。

    优先读 `content/<目录>/extra.json` 的 `progress_weights`（内容目录是
    单一事实源），其次读数据库 `chapter_extras`。两者都没有时用默认权重
    （元代规格：10/15/15/10/20/10/10/10，合计 100）。
    """
    weights = dict(DEFAULT_PROGRESS_WEIGHTS)

    candidates: list = []
    extra_file = content_loader.load_chapter_extra(chapter_id)
    if isinstance(extra_file, dict) and extra_file.get("progress_weights"):
        candidates.append(extra_file["progress_weights"])

    try:
        from app.models import ChapterExtra

        row = db.get(ChapterExtra, chapter_id)
        if row is not None and isinstance(row.data, dict) and row.data.get("progress_weights"):
            candidates.append(row.data["progress_weights"])
    except Exception:  # noqa: BLE001
        pass

    for candidate in candidates:
        for raw_key, weight in _extract_weight_entries(candidate):
            rule_key = _alias_to_rule_key(raw_key)
            if rule_key:
                weights[rule_key] = weight
        # 第一个可用的来源即生效，不做叠加
        break

    return weights


def _recompute_progress(db: Session, session: ExplorationSession) -> float:
    """重算并写回会话进度。任何异常都吞掉，返回当前已存进度。"""
    try:
        chapter_id = session.chapter_id or ""
        if not chapter_id:
            return float(session.progress or 0)
        agg = _aggregate(db, session.id, chapter_id)
        progress = _progress_from_agg(db, chapter_id, agg)
        session.progress = progress
        db.commit()
        return progress
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        logger.warning("进度重算失败（保留原值）：%s", exc)
        return float(session.progress or 0)


def _progress_from_agg(db: Session, chapter_id: str, agg: dict) -> float:
    """按各章 progress_weights 加权计算 0–100。"""
    weights = _weights_for(db, chapter_id)
    event_types = agg["event_types"]
    entity_views = len(agg["entity_ids"])

    earned = 0.0
    if event_types & {"SCENE_ENTER", "CHAPTER_ENTER", "ARTWORK_HOTSPOT_VIEW"}:
        earned += weights.get("SCENE_ENTER", 0)
    if entity_views >= ENTITY_VIEW_PARTIAL_THRESHOLD:
        earned += weights.get("ENTITY_VIEW_3", 0)
    if entity_views >= ENTITY_VIEW_FULL_THRESHOLD:
        earned += weights.get("ENTITY_VIEW_ALL", 0)
    if (event_types & {"SOURCE_VIEW", "CHAT_SOURCE_VIEW"}) or agg["source_ids"]:
        earned += weights.get("SOURCE_VIEW", 0)
    if agg["chat_count"] > 0:
        earned += weights.get("CHAT_ASK", 0)
    if "GRAPH_OPEN" in event_types:
        earned += weights.get("GRAPH_OPEN", 0)
    if event_types & {"GRAPH_NODE_EXPAND", "OUTSIDE_RELATION_EXPAND"}:
        earned += weights.get("GRAPH_NODE_EXPAND", 0)
    if "RELATION_EVIDENCE_VIEW" in event_types:
        earned += weights.get("RELATION_EVIDENCE_VIEW", 0)

    return round(min(100.0, max(0.0, earned)), 2)


def get_progress(
    db: Session, chapter_id: str | None = None, session_id: str | None = None
) -> ExplorationProgressOut:
    """探索进度。无会话 / 无数据时返回全 0 而非报错。"""
    session = get_session(db, session_id) or latest_session(db, chapter_id)
    if session is None:
        return ExplorationProgressOut(
            session_id="",
            chapter_id=chapter_id or "",
            progress=0,
            chapters=_chapter_progress_list(db, None),
            totals=_totals(db),
        )

    target_chapter = chapter_id or session.chapter_id or ""
    agg = _aggregate(db, session.id, target_chapter) if target_chapter else _empty_agg()

    return ExplorationProgressOut(
        session_id=session.id,
        chapter_id=target_chapter,
        progress=_progress_from_agg(db, target_chapter, agg) if target_chapter else 0,
        visited_entity_ids=sorted(agg["entity_ids"]),
        visited_relation_ids=sorted(agg["relation_ids"]),
        viewed_source_ids=sorted(agg["source_ids"]),
        asked_question_count=agg["chat_count"],
        chapters=_chapter_progress_list(db, session),
        totals=_totals(db),
    )


def _empty_agg() -> dict:
    return {
        "event_types": set(),
        "entity_ids": set(),
        "relation_ids": set(),
        "source_ids": set(),
        "chat_count": 0,
    }


def _chapter_progress_list(db: Session, session: ExplorationSession | None) -> list[ChapterProgressOut]:
    """六章各自的完成度。"""
    chapters = db.execute(select(Chapter).order_by(Chapter.sort_order, Chapter.id)).scalars().all()
    if not chapters:
        return []

    result: list[ChapterProgressOut] = []
    for chapter in chapters:
        if session is None:
            result.append(ChapterProgressOut(chapter_id=chapter.id, progress=0, status="not_started"))
            continue
        agg = _aggregate(db, session.id, chapter.id)
        progress = _progress_from_agg(db, chapter.id, agg)
        if progress >= 100:
            status = "completed"
        elif progress > 0:
            status = "in_progress"
        else:
            status = "not_started"
        result.append(ChapterProgressOut(chapter_id=chapter.id, progress=progress, status=status))
    return result


def _totals(db: Session) -> ProgressTotalsOut:
    def _count(model, *criteria) -> int:
        try:
            stmt = select(func.count()).select_from(model)
            for criterion in criteria:
                stmt = stmt.where(criterion)
            return int(db.execute(stmt).scalar() or 0)
        except Exception:  # noqa: BLE001
            return 0

    return ProgressTotalsOut(
        entities=_count(Entity),
        artifacts=_count(
            Entity, Entity.entity_type.in_(["Artifact", "Artwork", "HeritageStructure"])
        ),
        places=_count(Entity, Entity.entity_type.in_(["Place", "Region", "Site"])),
        relations=_count(Relation),
        sources=_count(Source),
    )


# ============================================================
# 探索总结
# ============================================================


async def generate_summary(
    db: Session, chapter_id: str, session_id: str | None = None
) -> ExplorationSummaryOut:
    """探索总结。

    无 LLM Key 时用规则生成（基于 visited 节点拼装 80–120 字），不调用 LLM。
    有 Key 时由 ai.service 用 Prompt E 生成，失败自动回退到规则结果。
    """
    session = get_session(db, session_id) or latest_session(db, chapter_id)
    if session is None:
        return ExplorationSummaryOut(
            summary="你还没有开始探索这一章。进入场景后，这里会记录你关注过的内容。",
            next_entity_ids=_chapter_core_entities(db, chapter_id),
            cached=False,
        )

    agg = _aggregate(db, session.id, chapter_id)
    visited_ids = sorted(agg["entity_ids"])

    entities = []
    if visited_ids:
        entities = list(
            db.execute(select(Entity).where(Entity.id.in_(visited_ids))).scalars().all()
        )
    names = [(e.display_name or e.name) for e in entities if (e.display_name or e.name)]

    summary = _rule_based_summary(db, chapter_id, names, agg)
    next_ids = _next_entities(db, chapter_id, set(visited_ids))

    # 有 LLM 时尝试用 Prompt E 润色；失败或超时一律回退到规则结果
    from app.config import settings

    if settings.llm_configured and names:
        try:
            from app.ai.service import summarize_exploration

            polished = await summarize_exploration(
                chapter_id, names, agg["chat_count"], next_ids
            )
            if polished:
                summary = polished
        except Exception as exc:  # noqa: BLE001
            logger.warning("LLM 总结失败，回退规则总结：%s", exc)

    return ExplorationSummaryOut(summary=summary, next_entity_ids=next_ids, cached=False)


def _rule_based_summary(db: Session, chapter_id: str, names: list[str], agg: dict) -> str:
    """规则总结：只描述用户关注了什么，不新增用户没探索过的历史事实。

    长度控制在 80–120 字。
    """
    chapter = db.get(Chapter, chapter_id)
    chapter_title = chapter.title if chapter else "这一章"

    if not names:
        # 内容尚未入库时 chapter_title 会退化为「本章」，避免出现《这一章》这种别扭文案
        where = f"《{chapter_title}》" if chapter is not None else "本章"
        return (
            f"你刚刚进入{where}，还没有展开具体内容。"
            "可以从场景中的热点开始，或直接向 AI 角色提问，你的探索轨迹会在这里汇总。"
        )

    shown = names[:6]
    joined = "、".join(shown)
    tail = f"等 {len(names)} 处内容" if len(names) > len(shown) else ""

    parts = [f"你重点查看了{joined}{tail}。"]
    if agg["relation_ids"]:
        parts.append(f"并沿图谱展开了 {len(agg['relation_ids'])} 条关系。")
    if agg["source_ids"]:
        parts.append(f"查阅了 {len(agg['source_ids'])} 条史料来源。")
    if agg["chat_count"]:
        parts.append(f"提出了 {agg['chat_count']} 个问题。")
    parts.append("整体上，你的关注点集中在这些内容之间的联系上。")

    summary = "".join(parts)
    if len(summary) < 80:
        summary += "继续展开其它节点，可以看到更完整的关联脉络。"
    if len(summary) > 120:
        summary = summary[:118] + "。"
    return summary


def _chapter_core_entities(db: Session, chapter_id: str) -> list[str]:
    chapter = db.get(Chapter, chapter_id)
    if chapter and chapter.core_entity_ids:
        return list(chapter.core_entity_ids)[:4]
    return []


def _next_entities(db: Session, chapter_id: str, visited: set[str]) -> list[str]:
    """推荐下一个可看节点：优先当前节点的邻居，其次该章核心实体。"""
    if visited:
        rows = db.execute(
            select(Relation.source_entity_id, Relation.target_entity_id).where(
                Relation.chapter_id == chapter_id
            )
        ).all()
        neighbours: list[str] = []
        for src, tgt in rows:
            if src in visited and tgt not in visited:
                neighbours.append(tgt)
            elif tgt in visited and src not in visited:
                neighbours.append(src)
        if neighbours:
            seen: set[str] = set()
            ordered = [n for n in neighbours if not (n in seen or seen.add(n))]
            return ordered[:4]

    core = _chapter_core_entities(db, chapter_id)
    return [eid for eid in core if eid not in visited][:4]
