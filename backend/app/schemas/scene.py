"""场景 / 地图 / 时间轴 / 历史数字 / 证据对照 出参模型。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class HotspotOut(BaseModel):
    """对应前端 `Hotspot`。坐标为 0–1 归一化，全部预先标注。"""

    id: str
    entity_id: str | None = None
    shape: str = "polygon"
    # 允许 [[x,y],...] 或 [x,y]
    normalized_points: object = Field(default_factory=list)
    label: str | None = None
    group_key: str | None = None
    certainty: str | None = None
    route_scope: str | None = None
    sort_order: int = 0


class SceneOut(BaseModel):
    """对应前端 `Scene`。"""

    id: str
    chapter_id: str | None = None
    name: str = ""
    scene_kind: str = "image"
    background_asset_id: str | None = None
    width: int | None = None
    height: int | None = None
    disclaimer: str | None = None
    hotspots: list[HotspotOut] = Field(default_factory=list)
    # 当代工坊形态：无空间场景，改为元素集合
    workbench: dict | None = None
    # 地图形态（汉代丝路 / 清代迁徙）：节点与区段随场景一并返回。
    # 前端一次请求即可完整渲染，不需要再发一次 /map/{id}，
    # 也就不会出现「场景已渲染、路线还没到」的中间态。
    map: "HistoricalMapOut | None" = None


class MapNodeOut(BaseModel):
    """对应前端 `MapNode`。certainty 决定图例，不得高于证据精度。"""

    id: str
    entity_id: str | None = None
    label: str
    x: float
    y: float
    certainty: str = "confirmed_region"
    route_scope: str = "MASS_MIGRATION"
    sort_order: int = 0


class MapSegmentOut(BaseModel):
    """对应前端 `MapSegment`。证据不足时 geometry 为空数组，不虚构精度。"""

    id: str
    from_node_id: str
    to_node_id: str
    label: str | None = None
    geometry: list = Field(default_factory=list)
    certainty: str = "approximate_corridor"
    route_scope: str = "MASS_MIGRATION"
    source_ids: list[str] = Field(default_factory=list)
    claim_ids: list[str] = Field(default_factory=list)


class HistoricalMapOut(BaseModel):
    """对应前端 `HistoricalMap`。"""

    id: str
    name: str = ""
    coordinate_system: str = "normalized_canvas"
    disclaimer: str | None = None
    nodes: list[MapNodeOut] = Field(default_factory=list)
    segments: list[MapSegmentOut] = Field(default_factory=list)


class TimelineEventOut(BaseModel):
    """对应前端 `TimelineEvent`。display_date 保留原始精度。"""

    id: str
    entity_id: str | None = None
    display_date: str = ""
    date_precision: str = "year"
    title: str = ""
    summary: str | None = None
    entity_ids: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)


class HistoricalEstimateOut(BaseModel):
    """对应前端 `HistoricalEstimate`。多来源并列，绝不合并为唯一精确值。"""

    id: str
    metric: str = ""
    display_name: str = ""
    value_text: str = ""
    source_id: str | None = None
    source_title: str | None = None
    source_institution: str | None = None
    scope_note: str | None = None
    estimate_type: str | None = None


class EstimateGroupOut(BaseModel):
    """对应前端 `EstimateGroup`。"""

    metric: str
    display_name: str
    estimates: list[HistoricalEstimateOut] = Field(default_factory=list)
    display_policy: str = "show_all_approved"


class EvidenceItemOut(BaseModel):
    """对应前端 `EvidenceItem`。固定四层 + caveat。"""

    id: str
    entity_id: str | None = None
    group_key: str = ""
    site_key: str = ""
    title: str = ""
    observed: str = ""
    described_by_source: str = ""
    supports: str = ""
    does_not_support: str = ""
    caveat: str | None = None
    image_url: str | None = None
    source_ids: list[str] = Field(default_factory=list)


class ComparisonGroupOut(BaseModel):
    """对应前端 `ComparisonGroup`。"""

    id: str
    name: str = ""
    description: str | None = None
    sort_order: int = 0


class ComparisonOut(BaseModel):
    """`GET /chapters/{id}/comparison` 的返回体。"""

    groups: list[ComparisonGroupOut] = Field(default_factory=list)
    items: list[EvidenceItemOut] = Field(default_factory=list)


class FlowItemOut(BaseModel):
    """汉代 flow_items：物品的传播路径。字段由内容层决定，做宽松透传。"""

    id: str
    name: str = ""
    category: str | None = None
    direction: str | None = None
    description: str | None = None
    entity_ids: list[str] = Field(default_factory=list)
    path_node_ids: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)


# SceneOut.map 引用了在同一文件后面才定义的 HistoricalMapOut，
# 因此需要在这里补一次 rebuild，让 Pydantic 解析这个前向引用。
SceneOut.model_rebuild()
