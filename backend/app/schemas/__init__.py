"""Pydantic 出参模型。

字段名一律 snake_case，与 `frontend/src/types/index.ts` 完全对应。
凡前端标为可选的字段，这里一律给默认值，保证数据库为空时也能正常序列化。
"""

from app.schemas.chapter import ChapterOut, CharacterOut, RecommendedQuestionOut
from app.schemas.chat import (
    ChatSessionOut,
    CitationOut,
    RelatedEntityOut,
    RegenerateResultOut,
)
from app.schemas.cocreation import (
    CocreationValidationOut,
    GenerationResultOut,
    ProvenanceOut,
)
from app.schemas.entity import ClaimOut, EntityOut, SourceClaimOut, SourceOut
from app.schemas.exploration import (
    ExplorationProgressOut,
    ExplorationSummaryOut,
    SessionCreatedOut,
)
from app.schemas.graph import GraphEdge, GraphNode, RelationEvidenceOut, SubGraph
from app.schemas.health import HealthOut
from app.schemas.scene import (
    ComparisonOut,
    EvidenceItemOut,
    EstimateGroupOut,
    HistoricalEstimateOut,
    HistoricalMapOut,
    HotspotOut,
    MapNodeOut,
    MapSegmentOut,
    SceneOut,
    TimelineEventOut,
)

__all__ = [
    "ChapterOut",
    "CharacterOut",
    "RecommendedQuestionOut",
    "EntityOut",
    "SourceOut",
    "SourceClaimOut",
    "ClaimOut",
    "GraphNode",
    "GraphEdge",
    "SubGraph",
    "RelationEvidenceOut",
    "SceneOut",
    "HotspotOut",
    "HistoricalMapOut",
    "MapNodeOut",
    "MapSegmentOut",
    "TimelineEventOut",
    "HistoricalEstimateOut",
    "EstimateGroupOut",
    "ComparisonOut",
    "EvidenceItemOut",
    "ChatSessionOut",
    "CitationOut",
    "RelatedEntityOut",
    "RegenerateResultOut",
    "ExplorationProgressOut",
    "ExplorationSummaryOut",
    "SessionCreatedOut",
    "CocreationValidationOut",
    "GenerationResultOut",
    "ProvenanceOut",
    "HealthOut",
]
