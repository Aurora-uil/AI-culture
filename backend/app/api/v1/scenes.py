"""场景 / 地图 / 时间轴接口。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import degrade_to
from app.db.postgres import get_db
from app.schemas.scene import HistoricalMapOut, SceneOut, TimelineEventOut
from app.services import content_service

router = APIRouter()

NOT_FOUND_MESSAGE = "这段内容暂时没有完成数字化整理。"


@router.get("/scenes/{scene_id}", response_model=SceneOut, summary="场景详情（含热点）")
def get_scene(scene_id: str, db: Session = Depends(get_db)) -> SceneOut:
    """热点全部为预标注坐标，不使用任何视觉识别算法。"""
    scene = content_service.get_scene(db, scene_id)
    if scene is None:
        raise HTTPException(status_code=404, detail=NOT_FOUND_MESSAGE)
    return scene


@router.get("/map/{map_id}", response_model=HistoricalMapOut, summary="历史地图")
def get_map(map_id: str, db: Session = Depends(get_db)) -> HistoricalMapOut:
    """certainty 决定图例样式，路线精度不得高于证据精度。"""
    historical_map = content_service.get_map(db, map_id)
    if historical_map is None:
        raise HTTPException(status_code=404, detail=NOT_FOUND_MESSAGE)
    return historical_map


@router.get(
    "/timeline/{chapter_id}",
    response_model=list[TimelineEventOut],
    summary="证据时间轴",
)
@degrade_to([])
def get_timeline(chapter_id: str, db: Session = Depends(get_db)) -> list[TimelineEventOut]:
    """display_date 保留原始精度（如「1771年夏季」）。无数据时返回空数组。"""
    return content_service.get_timeline(db, chapter_id)
