"""图谱接口。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import degrade_to, get_exploration_session_id
from app.db.postgres import get_db
from app.models import ExplorationNodeState
from app.schemas.graph import RelationEvidenceOut, SubGraph
from app.services import graph_service

router = APIRouter()

NOT_FOUND_MESSAGE = "这条关系暂时没有完成数字化整理。"
# 数据库 / 图数据库不可用时的降级提示，界面可直接展示给用户
UNAVAILABLE_MESSAGE = "图谱数据暂时不可用，请确认已执行 docker compose up -d，然后重试。"


def _visited_ids(db: Session, session_id: str | None) -> set[str]:
    """该探索会话访问过的实体 ID，用于图谱 explored 标记。

    会话不存在时返回空集合 —— 图谱仍可正常渲染，只是没有「已探索」高亮。
    """
    if not session_id:
        return set()
    try:
        rows = db.execute(
            select(ExplorationNodeState.entity_id).where(
                ExplorationNodeState.session_id == session_id
            )
        ).all()
        return {row[0] for row in rows if row[0]}
    except Exception:  # noqa: BLE001 - 图谱不能因为探索状态查不到就报错
        return set()


@router.get("/graph/subgraph", response_model=SubGraph, summary="子图展开")
@degrade_to(SubGraph(message=UNAVAILABLE_MESSAGE))
def get_subgraph(
    center_entity_id: str = Query(..., description="中心实体 ID"),
    depth: int = Query(default=1, description="展开深度，最大 3"),
    limit: int = Query(default=60, description="节点数上限"),
    types: str | None = Query(default=None, description="实体类型白名单，逗号分隔"),
    session_id: str | None = Depends(get_exploration_session_id),
    db: Session = Depends(get_db),
) -> SubGraph:
    """以 center_entity_id 为中心展开。

    **单次展开新增节点硬上限 12 个**（见 graph_service.EXPANSION_NODE_CAP），
    超出时 `truncated=true`。中心实体不存在或图谱为空时返回空子图而不是 404。
    """
    return graph_service.get_subgraph(
        db,
        center_entity_id,
        depth=depth,
        limit=limit,
        types=types,
        visited_ids=_visited_ids(db, session_id),
    )


@router.get(
    "/graph/relations/{relation_id}/evidence",
    response_model=RelationEvidenceOut,
    summary="关系的证据明细",
)
def get_relation_evidence(
    relation_id: str, db: Session = Depends(get_db)
) -> RelationEvidenceOut:
    """返回 claim、claim_type、两端实体名与来源列表。

    前端据 claim_type 渲染实线 / 虚线 / 点划线，因此必须原样透传。
    """
    evidence = graph_service.get_relation_evidence(db, relation_id)
    if evidence is None:
        raise HTTPException(status_code=404, detail=NOT_FOUND_MESSAGE)
    return evidence


@router.get("/graph/overview", response_model=SubGraph, summary="图谱总览")
@degrade_to(SubGraph(message=UNAVAILABLE_MESSAGE))
def get_overview(
    session_id: str | None = Depends(get_exploration_session_id),
    db: Session = Depends(get_db),
) -> SubGraph:
    """六章 + 每章 3–5 个核心节点 + 中心「中华文化长期联系」策展节点。

    中心节点是**策展关联，不是历史实体**：它的关联边 claim_type 固定为
    `curatorial`，前端渲染为点划线。
    """
    return graph_service.get_overview(db, visited_ids=_visited_ids(db, session_id))


@router.get("/graph/explored", response_model=list[str], summary="已探索实体 ID")
@degrade_to([])
def get_explored(
    session_id: str | None = Depends(get_exploration_session_id),
    db: Session = Depends(get_db),
) -> list[str]:
    """便捷接口：只取已探索 ID 列表。会话不存在时返回空数组。"""
    if not session_id:
        return []
    return sorted(_visited_ids(db, session_id))
