"""图谱出参模型。

关键约束：
- `GraphNode.type` 是实体类型（注意字段名是 type 而非 entity_type，
  与 frontend/src/types/index.ts 的 GraphNode 一致）。
- `GraphEdge.claim_type` 必须透传 fact / interpretation / curatorial /
  catalogue_fact，前端据此渲染实线 / 虚线 / 点划线。
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    """对应前端 `GraphNode`。"""

    id: str
    type: str = "Concept"
    name: str
    subtitle: str | None = None
    short_summary: str | None = None
    # 该探索会话是否访问过
    explored: bool = False
    # 是否中心节点（1.35× 尺寸）
    is_center: bool = False
    # ECharts 用的固定坐标（演示模式下固定布局，不使用随机）
    x: float | None = None
    y: float | None = None


class GraphEdge(BaseModel):
    """对应前端 `GraphEdge`。"""

    id: str
    source: str
    target: str
    relation_type: str = "RELATED_TO"
    display_label: str = "相关"
    claim_type: str = "fact"
    review_status: str = "approved"
    source_ids: list[str] = Field(default_factory=list)


class SubGraph(BaseModel):
    """对应前端 `SubGraph`。"""

    center_entity_id: str = ""
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    truncated: bool = False
    message: str | None = None


class RelationSourceOut(BaseModel):
    """关系证据里的来源摘要（前端只取这几项）。"""

    id: str
    title: str
    institution: str = ""
    source_level: str | None = None
    public_url: str | None = None


class RelationEvidenceOut(BaseModel):
    """对应前端 `RelationEvidence`。"""

    relation_id: str
    claim: str = ""
    claim_type: str = "fact"
    display_label: str | None = None
    subject_name: str | None = None
    object_name: str | None = None
    sources: list[RelationSourceOut] = Field(default_factory=list)
