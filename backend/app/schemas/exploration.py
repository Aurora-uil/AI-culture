"""探索进度与总结出参模型。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SessionCreatedOut(BaseModel):
    """`POST /exploration/sessions` 返回体。"""

    session_id: str
    chapter_id: str = ""


class ChapterProgressOut(BaseModel):
    """六章各自的完成度。"""

    chapter_id: str
    progress: float = 0
    status: str = "in_progress"


class ProgressTotalsOut(BaseModel):
    """站内内容总量，用于主页展示。"""

    entities: int = 0
    artifacts: int = 0
    places: int = 0
    relations: int = 0
    sources: int = 0


class ExplorationProgressOut(BaseModel):
    """对应前端 `ExplorationProgress`。"""

    session_id: str = ""
    chapter_id: str = ""
    progress: float = 0
    visited_entity_ids: list[str] = Field(default_factory=list)
    visited_relation_ids: list[str] = Field(default_factory=list)
    viewed_source_ids: list[str] = Field(default_factory=list)
    asked_question_count: int = 0
    chapters: list[ChapterProgressOut] = Field(default_factory=list)
    totals: ProgressTotalsOut | None = None


class ExplorationSummaryOut(BaseModel):
    """对应前端 `ExplorationSummary`。"""

    summary: str = ""
    next_entity_ids: list[str] = Field(default_factory=list)
    cached: bool = False


class EventAckOut(BaseModel):
    """事件上报回执。重复上报返回 duplicated=true，不报错。"""

    ok: bool = True
    duplicated: bool = False
    progress: float = 0
