"""章节 / AI 角色 / 推荐问题 出参模型。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChapterOut(BaseModel):
    """对应前端 `Chapter`。

    注意 `theme` 在数据库里叫 theme，前端字段名是 `keyword`，此处做映射；
    `slug` 为 alters.sql 补充字段（han / northern-wei / ...）。
    """

    id: str
    slug: str | None = None
    era: str
    keyword: str = ""  # ← chapters.theme
    title: str
    date_label: str | None = None
    guiding_question: str = ""
    display_question: str | None = None
    hero_asset: str | None = None
    accent: str | None = None
    primary_interaction: str | None = None
    ai_character_id: str | None = None
    core_entity_ids: list[str] = Field(default_factory=list)
    narration: str | None = None
    sort_order: int = 0
    status: str | None = None
    # 该章探索进度 0–100（传了 session 才有值）
    progress: float | None = None

    @classmethod
    def from_orm_chapter(cls, chapter, progress: float | None = None) -> "ChapterOut":
        return cls(
            id=chapter.id,
            slug=chapter.slug,
            era=chapter.era,
            keyword=chapter.theme or "",
            title=chapter.title,
            date_label=chapter.date_label,
            guiding_question=chapter.guiding_question or "",
            display_question=chapter.display_question,
            hero_asset=chapter.hero_asset,
            accent=chapter.accent,
            primary_interaction=chapter.primary_interaction,
            ai_character_id=chapter.ai_character_id,
            core_entity_ids=list(chapter.core_entity_ids or []),
            narration=chapter.narration,
            sort_order=int(chapter.sort_order or 0),
            status=chapter.status,
            progress=progress,
        )


class CharacterOut(BaseModel):
    """对应前端 `Character`。disclaimer 必须在界面固定显示。"""

    id: str
    name: str
    character_type: str = "narrator"
    base_entity_id: str | None = None
    chapter_id: str | None = None
    subtitle: str | None = None
    disclaimer: str = ""
    image_url: str | None = None


class RecommendedQuestionOut(BaseModel):
    """对应前端 `RecommendedQuestion`。比赛版写数据库配置，不用 LLM 生成。"""

    id: str
    text: str
    intent: str | None = None


class NarrationOut(BaseModel):
    """C01「听它讲述」固定文本，不走 LLM。"""

    narration: str = ""
