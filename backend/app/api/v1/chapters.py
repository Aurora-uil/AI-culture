"""章节相关接口。

约定：列表类接口在数据库为空时返回空数组；详情类接口找不到资源时返回
中文 404，而不是 500。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import degrade_to
from app.db.postgres import get_db
from app.schemas.chapter import ChapterOut, CharacterOut, NarrationOut, RecommendedQuestionOut
from app.schemas.cocreation import CocreationElementOut
from app.schemas.scene import ComparisonOut, EstimateGroupOut, FlowItemOut, SceneOut
from app.services import cocreation_service, content_service, exploration_service

router = APIRouter()

NOT_FOUND_MESSAGE = "这段内容暂时没有完成数字化整理。"


@router.get("/chapters", response_model=list[ChapterOut], summary="全部章节")
@degrade_to([])
def list_chapters(db: Session = Depends(get_db)) -> list[ChapterOut]:
    """六章配置。数据库为空时返回空数组。"""
    return content_service.list_chapters(db)


@router.get("/chapters/{chapter_id}", response_model=ChapterOut, summary="章节详情")
def get_chapter(chapter_id: str, db: Session = Depends(get_db)) -> ChapterOut:
    chapter = content_service.get_chapter(db, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=404, detail=NOT_FOUND_MESSAGE)
    return chapter


@router.get(
    "/chapters/{chapter_id}/narration", response_model=NarrationOut, summary="C01 听它讲述"
)
@degrade_to(NarrationOut())
def get_narration(chapter_id: str, db: Session = Depends(get_db)) -> NarrationOut:
    """固定文本，不走 LLM。章节不存在或无文本时返回空串。"""
    return NarrationOut(narration=content_service.get_narration(db, chapter_id))


@router.get(
    "/chapters/{chapter_id}/recommended-questions",
    response_model=list[RecommendedQuestionOut],
    summary="推荐问题",
)
@degrade_to([])
def get_recommended_questions(
    chapter_id: str,
    character_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[RecommendedQuestionOut]:
    """比赛版写数据库配置，不用 LLM 生成。无数据时返回空数组。"""
    return content_service.list_recommended_questions(db, chapter_id, character_id)


@router.get("/chapters/{chapter_id}/scene", response_model=SceneOut, summary="章节场景")
def get_chapter_scene(chapter_id: str, db: Session = Depends(get_db)) -> SceneOut:
    scene = content_service.get_chapter_scene(db, chapter_id)
    if scene is None:
        raise HTTPException(status_code=404, detail=NOT_FOUND_MESSAGE)
    return scene


@router.get(
    "/chapters/{chapter_id}/estimates",
    response_model=list[EstimateGroupOut],
    summary="历史数字（多来源并列）",
)
@degrade_to([])
def get_estimates(
    chapter_id: str,
    metric: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[EstimateGroupOut]:
    """绝不求平均、绝不输出唯一「精确值」。无数据时返回空数组。"""
    return content_service.get_estimates(db, chapter_id, metric)


@router.get(
    "/chapters/{chapter_id}/comparison", response_model=ComparisonOut, summary="证据对照"
)
@degrade_to(ComparisonOut())
def get_comparison(chapter_id: str, db: Session = Depends(get_db)) -> ComparisonOut:
    """北魏证据对照。无数据时返回空 groups / items。"""
    return content_service.get_comparison(db, chapter_id)


@router.get(
    "/chapters/{chapter_id}/flow-items",
    response_model=list[FlowItemOut],
    summary="物品流动（汉代丝路）",
)
@degrade_to([])
def get_flow_items(chapter_id: str, db: Session = Depends(get_db)) -> list[FlowItemOut]:
    """无数据时返回空数组。字段做宽松透传，避免内容层微调导致 500。"""
    items = content_service.get_flow_items(db, chapter_id)
    result: list[FlowItemOut] = []
    for item in items:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        result.append(
            FlowItemOut(
                id=str(item["id"]),
                name=str(item.get("name") or ""),
                category=item.get("category"),
                direction=item.get("direction"),
                description=item.get("description"),
                entity_ids=list(item.get("entity_ids") or []),
                path_node_ids=list(item.get("path_node_ids") or []),
                source_ids=list(item.get("source_ids") or []),
            )
        )
    return result


@router.get(
    "/chapters/{chapter_id}/cocreation-elements",
    response_model=list[CocreationElementOut],
    summary="共创元素（当代）",
)
@degrade_to([])
def get_cocreation_elements(
    chapter_id: str, db: Session = Depends(get_db)
) -> list[CocreationElementOut]:
    """无数据时返回空数组。"""
    return cocreation_service.list_cocreation_elements(db, chapter_id)


@router.get("/characters", response_model=list[CharacterOut], summary="AI 角色")
@degrade_to([])
def list_characters(
    chapter_id: str | None = Query(default=None), db: Session = Depends(get_db)
) -> list[CharacterOut]:
    """disclaimer 必须在界面固定显示。无数据时返回空数组。"""
    return content_service.list_characters(db, chapter_id)


@router.get(
    "/chapters/{chapter_id}/progress", response_model=dict, summary="章节进度（预留）"
)
@degrade_to({"chapter_id": "", "progress": 0})
def get_chapter_progress(chapter_id: str, db: Session = Depends(get_db)) -> dict:
    """便捷接口：直接返回该章进度数值，避免前端为了一个数字拉全量进度。"""
    progress = exploration_service.get_progress(db, chapter_id)
    return {"chapter_id": chapter_id, "progress": progress.progress}
