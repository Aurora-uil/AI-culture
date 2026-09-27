"""图谱服务（Neo4j）。

设计约束（来自元代规格 §23 与前端 contracts）：
- 子图按「展开」逐跳查询，**单次展开新增节点硬上限 12 个**，depth 默认 1、最大 3。
- 每个节点带 `explored` 布尔（该探索会话是否访问过）。
- `claim_type` 必须透传（fact / interpretation / curatorial / catalogue_fact），
  前端据此渲染实线 / 虚线 / 点划线。
- `/graph/overview` 的中心「中华文化长期联系」是**策展节点，不是历史实体**。

Neo4j 不可用或图数据库为空时，回退到 PostgreSQL 的 relations / entities 表
（schema.sql 里写明 PostgreSQL 保存一份边数据「用于内容管理与兜底查询」）。
两者都为空时返回空子图，绝不 500。
"""

from __future__ import annotations

import logging
import math

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.neo4j import run_query
from app.models import Chapter, Claim, ClaimSource, Entity, Relation, Source
from app.schemas.graph import GraphEdge, GraphNode, RelationEvidenceOut, RelationSourceOut, SubGraph
from app.services import content_loader

logger = logging.getLogger(__name__)

# 单次展开新增节点硬上限 —— 保护前端渲染，避免一次点开就炸开上百个节点
EXPANSION_NODE_CAP = 12
MAX_DEPTH = 3
DEFAULT_NODE_LIMIT = 60

# 总览页中心的策展节点。它不是历史实体，claim_type 固定为 curatorial。
CURATORIAL_NODE_ID = "concept_chinese_culture_longterm_connection"
CURATORIAL_NODE_NAME = "中华文化长期联系"
CURATORIAL_NODE_SUBTITLE = "策展关联节点 · 非历史实体"
CURATORIAL_NODE_SUMMARY = (
    "这是展览设置的策展性关联，用来提示六个章节之间的长期联系。"
    "它不是一个历史实体，也不表示历史当事人具有这样的自觉目标。"
)

EMPTY_MESSAGE = "图谱数据尚未生成。请先运行 scripts/seed_neo4j.py 导入内容。"


# ============================================================
# 子图
# ============================================================


def get_subgraph(
    db: Session,
    center_entity_id: str,
    depth: int = 1,
    limit: int = DEFAULT_NODE_LIMIT,
    types: str | None = None,
    visited_ids: set[str] | None = None,
) -> SubGraph:
    """以 center_entity_id 为中心展开子图。

    depth：1–3，超出范围自动收敛。
    types：逗号分隔的实体类型白名单，如 "Script,Artifact"。
    visited_ids：该探索会话已访问的实体 ID，用于 explored 标记。
    """
    depth = max(1, min(int(depth or 1), MAX_DEPTH))
    limit = max(1, min(int(limit or DEFAULT_NODE_LIMIT), 200))
    type_filter = _parse_types(types)
    visited_ids = visited_ids or set()

    graph = _subgraph_from_neo4j(center_entity_id, depth, limit, type_filter, visited_ids)
    if graph is None:
        # Neo4j 不可用或没有该节点 → 用 PostgreSQL 兜底
        graph = _subgraph_from_postgres(db, center_entity_id, depth, limit, type_filter, visited_ids)

    if graph is None:
        return SubGraph(
            center_entity_id=center_entity_id,
            nodes=[],
            edges=[],
            truncated=False,
            message=EMPTY_MESSAGE,
        )
    return graph


def _parse_types(types: str | None) -> list[str] | None:
    if not types:
        return None
    parsed = [t.strip() for t in types.split(",") if t.strip()]
    return parsed or None


def _node_from_props(props: dict, visited_ids: set[str], is_center: bool = False) -> GraphNode:
    entity_id = props.get("id") or ""
    return GraphNode(
        id=entity_id,
        type=props.get("entity_type") or props.get("type") or "Concept",
        name=props.get("display_name") or props.get("name") or entity_id,
        subtitle=props.get("subtitle"),
        short_summary=props.get("short_summary"),
        explored=entity_id in visited_ids,
        is_center=is_center,
    )


def _edge_from_props(props: dict, source_id: str, target_id: str) -> GraphEdge:
    return GraphEdge(
        id=props.get("id") or f"{source_id}->{target_id}",
        source=source_id,
        target=target_id,
        relation_type=props.get("relation_type") or "RELATED_TO",
        display_label=props.get("display_label") or "相关",
        # claim_type 必须透传，前端据此决定线型
        claim_type=props.get("claim_type") or "fact",
        review_status=props.get("review_status") or "approved",
        source_ids=list(props.get("source_ids") or []),
    )


def _subgraph_from_neo4j(
    center_entity_id: str,
    depth: int,
    limit: int,
    type_filter: list[str] | None,
    visited_ids: set[str],
) -> SubGraph | None:
    """逐跳 BFS 展开。每一跳是一次「展开」，新增节点数受 EXPANSION_NODE_CAP 限制。

    返回 None 表示 Neo4j 不可用或中心节点不存在，交由调用方回退。
    """
    center_rows = run_query(
        "MATCH (c:Entity {id: $cid}) RETURN properties(c) AS node LIMIT 1",
        cid=center_entity_id,
    )
    if not center_rows:
        return None

    center_node = _node_from_props(center_rows[0]["node"] or {}, visited_ids, is_center=True)
    nodes: dict[str, GraphNode] = {center_node.id: center_node}
    edges: dict[str, GraphEdge] = {}
    frontier = [center_entity_id]
    truncated = False

    for _hop in range(depth):
        if not frontier:
            break
        # 每次展开最多带回 EXPANSION_NODE_CAP 个新节点
        remaining = limit - len(nodes)
        if remaining <= 0:
            truncated = True
            break
        cap = min(EXPANSION_NODE_CAP, remaining)

        cypher, params = _expansion_query(frontier, list(nodes.keys()), type_filter, cap)
        rows = run_query(cypher, **params)

        new_frontier: list[str] = []
        for row in rows:
            props = row.get("node") or {}
            node_id = props.get("id")
            if not node_id:
                continue
            src = row.get("source_id")
            tgt = row.get("target_id")
            if not src or not tgt:
                continue
            if node_id not in nodes:
                nodes[node_id] = _node_from_props(props, visited_ids)
                new_frontier.append(node_id)
            edge = _edge_from_props(row.get("rel") or {}, src, tgt)
            edges[edge.id] = edge

        if len(rows) >= cap:
            truncated = True
        frontier = new_frontier

    return SubGraph(
        center_entity_id=center_entity_id,
        nodes=list(nodes.values()),
        edges=list(edges.values()),
        truncated=truncated,
        message=None,
    )


def _expansion_query(
    frontier: list[str], seen: list[str], type_filter: list[str] | None, cap: int
) -> tuple[str, dict]:
    """构造单跳展开 Cypher。类型过滤条件按需拼接，避免 `IN null` 报错。"""
    type_clause = ""
    params: dict = {"frontier": frontier, "seen": seen, "cap": cap}
    if type_filter:
        type_clause = "AND n.entity_type IN $types "
        params["types"] = type_filter

    cypher = (
        "MATCH (c:Entity)-[r]-(n:Entity) "
        "WHERE c.id IN $frontier "
        "AND NOT n.id IN $seen "
        f"{type_clause}"
        "RETURN properties(n) AS node, properties(r) AS rel, "
        "startNode(r).id AS source_id, endNode(r).id AS target_id "
        "LIMIT $cap"
    )
    return cypher, params


# ---------- PostgreSQL 兜底 ----------


def _subgraph_from_postgres(
    db: Session,
    center_entity_id: str,
    depth: int,
    limit: int,
    type_filter: list[str] | None,
    visited_ids: set[str],
) -> SubGraph | None:
    """Neo4j 不可用时的兜底：用 relations 表做同样的逐跳展开。"""
    center = db.get(Entity, center_entity_id)
    if center is None:
        return None

    nodes: dict[str, GraphNode] = {
        center.id: _entity_to_node(center, visited_ids, is_center=True)
    }
    edges: dict[str, GraphEdge] = {}
    frontier = {center_entity_id}
    truncated = False

    for _hop in range(depth):
        if not frontier or len(nodes) >= limit:
            truncated = len(nodes) >= limit
            break
        cap = min(EXPANSION_NODE_CAP, limit - len(nodes))

        rows = db.execute(
            select(Relation)
            .where(
                or_(
                    Relation.source_entity_id.in_(frontier),
                    Relation.target_entity_id.in_(frontier),
                )
            )
            .limit(cap * 4)
        ).scalars().all()

        neighbour_ids: list[str] = []
        collected: list[Relation] = []
        for relation in rows:
            other = (
                relation.target_entity_id
                if relation.source_entity_id in frontier
                else relation.source_entity_id
            )
            if other in nodes:
                edges[relation.id] = _relation_to_edge(relation)
                continue
            if len(neighbour_ids) >= cap:
                truncated = True
                break
            neighbour_ids.append(other)
            collected.append(relation)

        neighbours = {
            e.id: e
            for e in db.execute(select(Entity).where(Entity.id.in_(neighbour_ids))).scalars().all()
        }
        for relation in collected:
            other = (
                relation.target_entity_id
                if relation.source_entity_id in frontier
                else relation.source_entity_id
            )
            entity = neighbours.get(other)
            if entity is None:
                continue
            if type_filter and entity.entity_type not in type_filter:
                continue
            nodes[entity.id] = _entity_to_node(entity, visited_ids)
            edges[relation.id] = _relation_to_edge(relation)

        frontier = set(neighbour_ids) & set(nodes.keys())

    return SubGraph(
        center_entity_id=center_entity_id,
        nodes=list(nodes.values()),
        edges=list(edges.values()),
        truncated=truncated,
        message=None,
    )


def _entity_to_node(entity: Entity, visited_ids: set[str], is_center: bool = False) -> GraphNode:
    return GraphNode(
        id=entity.id,
        type=entity.entity_type,
        name=entity.display_name or entity.name,
        subtitle=entity.subtitle,
        short_summary=entity.short_summary,
        explored=entity.id in visited_ids,
        is_center=is_center,
    )


def _relation_to_edge(relation: Relation) -> GraphEdge:
    return GraphEdge(
        id=relation.id,
        source=relation.source_entity_id,
        target=relation.target_entity_id,
        relation_type=relation.relation_type,
        display_label=relation.display_label,
        claim_type=relation.claim_type or "fact",
        review_status=relation.review_status or "approved",
        source_ids=list(relation.source_ids or []),
    )


# ============================================================
# 关系证据
# ============================================================


def get_relation_evidence(db: Session, relation_id: str) -> RelationEvidenceOut | None:
    """关系的证据明细。

    claim 文本与 claim→source 映射都存在 PostgreSQL，因此这里以 PostgreSQL
    为准（Neo4j 只保存拓扑与 claim_type / display_label 属性）。
    关系不存在时返回 None。
    """
    relation = db.get(Relation, relation_id)
    if relation is None:
        return None

    subject = db.get(Entity, relation.source_entity_id)
    obj = db.get(Entity, relation.target_entity_id)

    # 优先取该边直接挂的 claim
    claim = db.execute(
        select(Claim).where(Claim.relation_id == relation_id).order_by(Claim.id).limit(1)
    ).scalars().first()
    # 其次取两端实体上、claim_ids 明确列出的 claim
    claim_ids = list(relation.claim_ids or [])
    if claim is None and claim_ids:
        claim = db.get(Claim, claim_ids[0])

    claim_type = relation.claim_type or "fact"
    claim_text = claim.claim_text if claim is not None else ""
    if claim is not None and claim.claim_type:
        claim_type = claim.claim_type

    # 来源：claim_sources 优先，relation.source_ids 兜底
    source_ids: list[str] = []
    if claim is not None:
        source_ids = [
            row[0]
            for row in db.execute(
                select(ClaimSource.source_id).where(ClaimSource.claim_id == claim.id)
            ).all()
        ]
    if not source_ids:
        source_ids = list(relation.source_ids or [])

    sources: list[RelationSourceOut] = []
    if source_ids:
        rows = db.execute(select(Source).where(Source.id.in_(source_ids))).scalars().all()
        # 按 source_level 排（S 在前），保证界面优先展示最权威来源
        rows = sorted(rows, key=lambda s: (s.source_level or "C", s.id))
        sources = [
            RelationSourceOut(
                id=s.id,
                title=s.title,
                institution=s.institution or "",
                source_level=s.source_level,
                public_url=s.public_url,
            )
            for s in rows
        ]

    return RelationEvidenceOut(
        relation_id=relation.id,
        claim=claim_text,
        claim_type=claim_type,
        display_label=relation.display_label,
        subject_name=(subject.display_name or subject.name) if subject else None,
        object_name=(obj.display_name or obj.name) if obj else None,
        sources=sources,
    )


# ============================================================
# 总览
# ============================================================


def get_overview(db: Session, visited_ids: set[str] | None = None) -> SubGraph:
    """六章 + 每章 3–5 个核心节点 + 中心「中华文化长期联系」策展节点。

    数据库为空时退回读 content/chapters.json，保证全新克隆下总览页仍有结构。
    """
    visited_ids = visited_ids or set()

    chapters = db.execute(select(Chapter).order_by(Chapter.sort_order, Chapter.id)).scalars().all()
    if chapters:
        chapter_specs = [
            {
                "id": c.id,
                "title": c.title,
                "era": c.era,
                "theme": c.theme,
                "core_entity_ids": list(c.core_entity_ids or []),
            }
            for c in chapters
        ]
    else:
        chapter_specs = [
            {
                "id": c["id"],
                "title": c.get("title", ""),
                "era": c.get("era", ""),
                "theme": c.get("keyword", ""),
                "core_entity_ids": list(c.get("core_entity_ids") or []),
            }
            for c in content_loader.load_chapters_config()
        ]

    nodes: dict[str, GraphNode] = {}
    edges: dict[str, GraphEdge] = {}

    # 中心策展节点：不是历史实体
    nodes[CURATORIAL_NODE_ID] = GraphNode(
        id=CURATORIAL_NODE_ID,
        type="Concept",
        name=CURATORIAL_NODE_NAME,
        subtitle=CURATORIAL_NODE_SUBTITLE,
        short_summary=CURATORIAL_NODE_SUMMARY,
        explored=False,
        is_center=True,
    )

    # 各章核心实体。数据库为空时只画章节层（章节本身作为策展节点）。
    all_core_ids: list[str] = []
    for spec in chapter_specs:
        all_core_ids.extend(spec["core_entity_ids"])

    entity_map: dict[str, Entity] = {}
    if all_core_ids:
        entity_map = {
            e.id: e
            for e in db.execute(select(Entity).where(Entity.id.in_(all_core_ids))).scalars().all()
        }

    for index, spec in enumerate(chapter_specs):
        # 每章 3–5 个核心节点
        core_ids = [eid for eid in spec["core_entity_ids"] if eid in entity_map][:5]
        chapter_node_id = f"chapter_{spec['id']}"

        nodes[chapter_node_id] = GraphNode(
            id=chapter_node_id,
            type="Period",
            name=spec["title"] or spec["id"],
            subtitle=f"{spec['era']}·{spec['theme']}" if spec.get("era") else None,
            short_summary=None,
            explored=False,
            is_center=False,
        )

        for entity_id in core_ids:
            entity = entity_map[entity_id]
            nodes[entity_id] = _entity_to_node(entity, visited_ids)

        for entity_id in core_ids:
            edge_id = f"edge_overview_{spec['id']}_{entity_id}"
            edges[edge_id] = GraphEdge(
                id=edge_id,
                source=chapter_node_id,
                target=entity_id,
                relation_type="CHAPTER_CORE_ENTITY",
                display_label="核心内容",
                claim_type="fact",
                review_status="approved",
            )

        # 章节 → 中心策展节点：策展关联，点划线
        curatorial_edge_id = f"edge_overview_curatorial_{spec['id']}"
        edges[curatorial_edge_id] = GraphEdge(
            id=curatorial_edge_id,
            source=chapter_node_id,
            target=CURATORIAL_NODE_ID,
            relation_type="CURATORIAL_LONGTERM_CONNECTION",
            display_label="策展关联",
            claim_type="curatorial",
            review_status="approved",
        )

    _apply_overview_layout(list(nodes.values()), len(chapter_specs))

    message = None
    if len(nodes) <= 1:
        message = EMPTY_MESSAGE

    return SubGraph(
        center_entity_id=CURATORIAL_NODE_ID,
        nodes=list(nodes.values()),
        edges=list(edges.values()),
        truncated=False,
        message=message,
    )


def _apply_overview_layout(nodes: list[GraphNode], chapter_count: int) -> None:
    """总览固定布局：中心节点在原点，章节均匀分布在外圈，核心实体再外一圈。

    演示模式必须固定布局，不使用随机坐标。
    """
    chapter_nodes = [n for n in nodes if n.id.startswith("chapter_")]
    entity_nodes = [n for n in nodes if not n.id.startswith("chapter_") and not n.is_center]
    chapter_count = max(len(chapter_nodes), 1)

    for node in nodes:
        if node.is_center:
            node.x, node.y = 0.0, 0.0

    for index, node in enumerate(chapter_nodes):
        angle = 2 * math.pi * index / chapter_count - math.pi / 2
        node.x = round(420 * math.cos(angle), 2)
        node.y = round(420 * math.sin(angle), 2)

    # 核心实体挂到所属章节节点的外侧
    chapter_positions = {n.id: (n.x or 0.0, n.y or 0.0) for n in chapter_nodes}
    grouped: dict[str, list[GraphNode]] = {}
    for node in entity_nodes:
        parent = node.id.rsplit("_", 1)[0]
        grouped.setdefault(parent, []).append(node)

    for parent_id, children in grouped.items():
        # 找出真正以该前缀命名的章节节点；找不到就落在内圈
        base = None
        for chapter_node in chapter_nodes:
            if parent_id and parent_id in chapter_node.id:
                base = chapter_positions[chapter_node.id]
                break
        base = base or (0.0, 0.0)
        radius = math.hypot(*base)
        angle = math.atan2(base[1], base[0]) if radius else 0.0
        width = max(len(children), 1)
        for offset, child in enumerate(children):
            spread = angle + (offset - (width - 1) / 2) * 0.26
            child.x = round(base[0] + 190 * math.cos(spread), 2)
            child.y = round(base[1] + 190 * math.sin(spread), 2)


def overview_neighbours(db: Session) -> list[Entity]:
    """总览页可以点开的候选实体（按章节核心实体去重）。"""
    rows = db.execute(select(Entity).order_by(Entity.sort_order, Entity.id).limit(200)).scalars().all()
    return list(rows)
