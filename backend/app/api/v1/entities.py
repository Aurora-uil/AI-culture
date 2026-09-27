"""实体相关接口。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import degrade_to
from app.db.postgres import get_db
from app.schemas.entity import EntityOut, EntitySourcesOut
from app.schemas.graph import SubGraph
from app.services import content_service, graph_service

router = APIRouter()

NOT_FOUND_MESSAGE = "这段内容暂时没有完成数字化整理。"


@router.get("/entities", response_model=list[EntityOut], summary="实体列表")
@degrade_to([])
def list_entities(
    chapter_id: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[EntityOut]:
    """可按章节 / 类型过滤。数据库为空时返回空数组。"""
    return content_service.list_entities(db, chapter_id, entity_type)


@router.get("/entities/{entity_id}", response_model=EntityOut, summary="实体详情")
def get_entity(entity_id: str, db: Session = Depends(get_db)) -> EntityOut:
    entity = content_service.get_entity(db, entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail=NOT_FOUND_MESSAGE)
    return entity


@router.get(
    "/entities/{entity_id}/sources",
    response_model=EntitySourcesOut,
    summary="实体来源（含具体支持的 claim）",
)
@degrade_to(EntitySourcesOut(entity_id=""))
def get_entity_sources(entity_id: str, db: Session = Depends(get_db)) -> EntitySourcesOut:
    """设计系统 §36：不能只列参考文献名，必须说明该来源支持了哪些具体事实。

    实体不存在时同样返回空数组，避免界面因单个实体缺来源而报错。
    """
    return EntitySourcesOut(
        entity_id=entity_id, sources=content_service.get_entity_sources(db, entity_id)
    )


@router.get(
    "/entities/{entity_id}/relations", response_model=SubGraph, summary="实体的一跳关系"
)
@degrade_to(SubGraph(message="图谱数据暂时不可用，请确认已执行 docker compose up -d，然后重试。"))
def get_entity_relations(entity_id: str, db: Session = Depends(get_db)) -> SubGraph:
    """等价于 depth=1 的子图。实体不存在时返回空子图而不是 404。"""
    return graph_service.get_subgraph(db, entity_id, depth=1)
