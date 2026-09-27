"""SQLAlchemy ORM 模型，与 app/db/schema.sql 一一对应。

按域拆分为四个模块，全部在此汇总导出，便于 `from app.models import Entity`。
"""

from app.models.aigc import (
    CreationBasket,
    CreationBasketItem,
    GeneratedAsset,
    GenerationJob,
    GenerationPolicy,
    GenerationProvenance,
    RightsRecord,
)
from app.models.content import (
    Chapter,
    Character,
    Claim,
    ClaimSource,
    Entity,
    FallbackFaq,
    RagChunk,
    Relation,
    Source,
)
from app.models.extras import (
    ComparisonGroup,
    EvidenceItem,
    HistoricalEstimate,
    HistoricalMap,
    MapNode,
    MapSegment,
    Scene,
    SceneHotspot,
    TimelineEvent,
    ChapterExtra,
)
from app.models.session import (
    ChatMessage,
    ChatMessageCitation,
    ChatMessageFeedback,
    ChatSession,
    ExplorationEvent,
    ExplorationNodeState,
    ExplorationSession,
)

__all__ = [
    # content
    "Chapter",
    "Source",
    "Entity",
    "Claim",
    "ClaimSource",
    "Relation",
    "RagChunk",
    "Character",
    "FallbackFaq",
    # extras
    "Scene",
    "SceneHotspot",
    "HistoricalMap",
    "MapNode",
    "MapSegment",
    "TimelineEvent",
    "HistoricalEstimate",
    "ComparisonGroup",
    "EvidenceItem",
    "ChapterExtra",
    # aigc
    "RightsRecord",
    "GenerationPolicy",
    "CreationBasket",
    "CreationBasketItem",
    "GenerationJob",
    "GeneratedAsset",
    "GenerationProvenance",
    # session
    "ExplorationSession",
    "ExplorationEvent",
    "ExplorationNodeState",
    "ChatSession",
    "ChatMessage",
    "ChatMessageCitation",
    "ChatMessageFeedback",
]
