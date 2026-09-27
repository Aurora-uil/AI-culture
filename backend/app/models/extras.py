"""章节专属内容 ORM 模型：场景 / 热点 / 地图 / 时间轴 / 历史数字 / 证据对照。"""

from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Integer,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime, Numeric

from app.models.content import Base


class Scene(Base):
    """场景：元代券洞、北魏双石窟、唐代画卷、汉代地图、清代地图、当代工坊。"""

    __tablename__ = "scenes"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    chapter_id: Mapped[str | None] = mapped_column(Text, ForeignKey("chapters.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(Text, nullable=False)
    scene_kind: Mapped[str | None] = mapped_column(Text, default="image")
    background_asset_id: Mapped[str | None] = mapped_column(Text)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    # 例如「历史迁徙路线示意，并非现代GPS轨迹」
    disclaimer: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int | None] = mapped_column(Integer, default=1)
    status: Mapped[str | None] = mapped_column(Text, default="approved")


class SceneHotspot(Base):
    """预标注热点。坐标 0–1 归一化，不使用任何视觉识别算法。"""

    __tablename__ = "scene_hotspots"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    scene_id: Mapped[str] = mapped_column(Text, ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(Text, ForeignKey("entities.id", ondelete="CASCADE"))
    shape: Mapped[str | None] = mapped_column(Text, default="polygon")
    normalized_points: Mapped[object] = mapped_column(JSONB, nullable=False)
    label: Mapped[str | None] = mapped_column(Text)
    certainty: Mapped[str | None] = mapped_column(Text)
    route_scope: Mapped[str | None] = mapped_column(Text)
    group_key: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int | None] = mapped_column(Integer, default=0)
    enabled: Mapped[bool | None] = mapped_column(Boolean, default=True)


class HistoricalMap(Base):
    """历史地图（汉代丝路、清代迁徙）。"""

    __tablename__ = "historical_maps"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    chapter_id: Mapped[str | None] = mapped_column(Text, ForeignKey("chapters.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(Text, nullable=False)
    background_asset_id: Mapped[str | None] = mapped_column(Text)
    coordinate_system: Mapped[str | None] = mapped_column(Text, default="normalized_canvas")
    disclaimer: Mapped[str | None] = mapped_column(Text)


class MapNode(Base):
    """地图节点。certainty 决定图例样式，不得高于证据精度。"""

    __tablename__ = "map_nodes"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    map_id: Mapped[str] = mapped_column(Text, ForeignKey("historical_maps.id", ondelete="CASCADE"), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(Text, ForeignKey("entities.id", ondelete="SET NULL"))
    label: Mapped[str] = mapped_column(Text, nullable=False)
    x: Mapped[float] = mapped_column(Float, nullable=False)
    y: Mapped[float] = mapped_column(Float, nullable=False)
    certainty: Mapped[str | None] = mapped_column(Text, default="confirmed_region")
    route_scope: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int | None] = mapped_column(Integer, default=0)


class MapSegment(Base):
    """地图区段。证据不足时宁可 geometry 为空，也不虚构精度。"""

    __tablename__ = "map_segments"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    map_id: Mapped[str] = mapped_column(Text, ForeignKey("historical_maps.id", ondelete="CASCADE"), nullable=False)
    from_node_id: Mapped[str] = mapped_column(Text, nullable=False)
    to_node_id: Mapped[str] = mapped_column(Text, nullable=False)
    label: Mapped[str | None] = mapped_column(Text)
    geometry: Mapped[list | None] = mapped_column(JSONB, default=list)
    certainty: Mapped[str | None] = mapped_column(Text, default="approximate")
    route_scope: Mapped[str | None] = mapped_column(Text, default="MASS_MIGRATION")
    source_ids: Mapped[list | None] = mapped_column(JSONB, default=list)
    claim_ids: Mapped[list | None] = mapped_column(JSONB, default=list)
    review_status: Mapped[str | None] = mapped_column(Text, default="approved")


class TimelineEvent(Base):
    """证据时间轴。display_date 保留原始精度（如「1771年夏季」）。"""

    __tablename__ = "timeline_events"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    chapter_id: Mapped[str | None] = mapped_column(Text, ForeignKey("chapters.id", ondelete="CASCADE"))
    entity_id: Mapped[str | None] = mapped_column(Text, ForeignKey("entities.id", ondelete="SET NULL"))
    display_date: Mapped[str] = mapped_column(Text, nullable=False)
    date_precision: Mapped[str | None] = mapped_column(Text)
    sort_value: Mapped[float | None] = mapped_column(Numeric)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    entity_ids: Mapped[list | None] = mapped_column(JSONB, default=list)
    claim_ids: Mapped[list | None] = mapped_column(JSONB, default=list)
    source_ids: Mapped[list | None] = mapped_column(JSONB, default=list)
    sort_order: Mapped[int | None] = mapped_column(Integer, default=0)


class HistoricalEstimate(Base):
    """历史数字：多来源并列，绝不求平均，绝不输出唯一「精确值」。"""

    __tablename__ = "historical_estimates"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    chapter_id: Mapped[str | None] = mapped_column(Text, ForeignKey("chapters.id", ondelete="CASCADE"))
    entity_id: Mapped[str | None] = mapped_column(Text, ForeignKey("entities.id", ondelete="SET NULL"))
    metric: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    value_text: Mapped[str] = mapped_column(Text, nullable=False)
    numeric_value: Mapped[float | None] = mapped_column(Float)
    numeric_min: Mapped[float | None] = mapped_column(Float)
    numeric_max: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(Text)
    source_id: Mapped[str | None] = mapped_column(Text, ForeignKey("sources.id", ondelete="SET NULL"))
    claim_id: Mapped[str | None] = mapped_column(Text, ForeignKey("claims.id", ondelete="SET NULL"))
    scope_note: Mapped[str | None] = mapped_column(Text)
    estimate_type: Mapped[str | None] = mapped_column(Text, default="source_reported")
    display_policy: Mapped[str | None] = mapped_column(Text, default="show_all_approved")
    review_status: Mapped[str | None] = mapped_column(Text, default="approved")


class ComparisonGroup(Base):
    """北魏证据对照分组：服饰 / 雕塑 / 音乐 / 建筑。"""

    __tablename__ = "comparison_groups"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    chapter_id: Mapped[str | None] = mapped_column(Text, ForeignKey("chapters.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int | None] = mapped_column(Integer, default=0)


class EvidenceItem(Base):
    """证据对照条目，固定四层：看到什么 / 来源如何描述 / 能支持什么 / 不能推出什么。"""

    __tablename__ = "evidence_items"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    chapter_id: Mapped[str | None] = mapped_column(Text, ForeignKey("chapters.id", ondelete="CASCADE"))
    entity_id: Mapped[str | None] = mapped_column(Text, ForeignKey("entities.id", ondelete="SET NULL"))
    group_key: Mapped[str | None] = mapped_column(Text, ForeignKey("comparison_groups.id", ondelete="SET NULL"))
    site_key: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    observed: Mapped[str | None] = mapped_column(Text)
    described_by_source: Mapped[str | None] = mapped_column(Text)
    supports: Mapped[str | None] = mapped_column(Text)
    does_not_support: Mapped[str | None] = mapped_column(Text)
    caveat: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text)
    claim_ids: Mapped[list | None] = mapped_column(JSONB, default=list)
    source_ids: Mapped[list | None] = mapped_column(JSONB, default=list)
    review_status: Mapped[str | None] = mapped_column(Text, default="approved")


class ChapterExtra(Base):
    """章节额外数据（progress_weights / flow_items 等），alters.sql 补充表。"""

    __tablename__ = "chapter_extras"

    chapter_id: Mapped[str] = mapped_column(Text, ForeignKey("chapters.id", ondelete="CASCADE"), primary_key=True)
    data: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    updated_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
