"""内容查询服务：章节 / 实体 / 来源 / 场景 / 地图 / 时间轴 / 估算 / 对照证据。

所有函数在数据库为空时返回空列表或 None，绝不抛异常 —— 内容数据尚未生成
完成时，接口仍须正常响应。
"""

from __future__ import annotations

import logging

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import (
    Chapter,
    ChapterExtra,
    Character,
    Claim,
    ClaimSource,
    ComparisonGroup,
    Entity,
    EvidenceItem,
    FallbackFaq,
    HistoricalEstimate,
    HistoricalMap,
    MapNode,
    MapSegment,
    RagChunk,
    Relation,
    Scene,
    SceneHotspot,
    Source,
    TimelineEvent,
)
from app.services import content_loader
from app.schemas.chapter import ChapterOut, CharacterOut, RecommendedQuestionOut
from app.schemas.entity import ClaimOut, EntityOut, SourceClaimOut, SourceOut
from app.schemas.scene import (
    ComparisonGroupOut,
    ComparisonOut,
    EstimateGroupOut,
    EvidenceItemOut,
    HistoricalEstimateOut,
    HistoricalMapOut,
    HotspotOut,
    MapNodeOut,
    MapSegmentOut,
    SceneOut,
    TimelineEventOut,
)

logger = logging.getLogger(__name__)

# 早期返回用的空对象
EMPTY_SUBGRAPH_MESSAGE = "图谱数据尚未生成。"


# ============================================================
# 章节
# ============================================================


def list_chapters(db: Session, progress_map: dict[str, float] | None = None) -> list[ChapterOut]:
    """全部章节，按 sort_order 排序。"""
    rows = db.execute(select(Chapter).order_by(Chapter.sort_order, Chapter.id)).scalars().all()
    progress_map = progress_map or {}
    return [ChapterOut.from_orm_chapter(c, progress_map.get(c.id)) for c in rows]


def get_chapter(db: Session, chapter_id: str) -> ChapterOut | None:
    chapter = db.get(Chapter, chapter_id)
    if chapter is None:
        return None
    return ChapterOut.from_orm_chapter(chapter)


def chapter_exists(db: Session, chapter_id: str) -> bool:
    return db.get(Chapter, chapter_id) is not None


def get_narration(db: Session, chapter_id: str) -> str:
    """C01「听它讲述」固定文本，不走 LLM。章节不存在时返回空串而非 404。"""
    chapter = db.get(Chapter, chapter_id)
    if chapter is None or not chapter.narration:
        return ""
    return chapter.narration


def list_characters(db: Session, chapter_id: str | None = None) -> list[CharacterOut]:
    """AI 角色。可选按章节过滤。"""
    stmt = select(Character).where(Character.enabled.is_(True))
    if chapter_id:
        stmt = stmt.where(Character.chapter_id == chapter_id)
    rows = db.execute(stmt.order_by(Character.id)).scalars().all()
    return [
        CharacterOut(
            id=c.id,
            name=c.name,
            character_type=c.character_type or "narrator",
            base_entity_id=c.base_entity_id,
            chapter_id=c.chapter_id,
            subtitle=c.subtitle,
            disclaimer=c.disclaimer or "",
            image_url=c.image_url,
        )
        for c in rows
    ]


def get_character(db: Session, character_id: str) -> CharacterOut | None:
    row = db.get(Character, character_id)
    if row is None:
        return None
    return CharacterOut(
        id=row.id,
        name=row.name,
        character_type=row.character_type or "narrator",
        base_entity_id=row.base_entity_id,
        chapter_id=row.chapter_id,
        subtitle=row.subtitle,
        disclaimer=row.disclaimer or "",
        image_url=row.image_url,
    )


def list_recommended_questions(
    db: Session, chapter_id: str, character_id: str | None = None
) -> list[RecommendedQuestionOut]:
    """推荐问题。比赛版写数据库配置（fallback_faq 的 canonical_question），不用 LLM 生成。"""
    stmt = select(FallbackFaq).where(FallbackFaq.chapter_id == chapter_id)
    if character_id:
        # 角色专属问题优先，同时保留通用问题（character_id 为空的行）
        stmt = stmt.where(
            or_(FallbackFaq.character_id == character_id, FallbackFaq.character_id.is_(None))
        )
    rows = db.execute(stmt.order_by(FallbackFaq.id)).scalars().all()
    return [
        RecommendedQuestionOut(
            id=r.id,
            text=r.canonical_question,
            intent=r.intent,
        )
        for r in rows
        if r.canonical_question
    ]


# ============================================================
# 实体
# ============================================================


def _entity_out(
    entity: Entity, source_count: int = 0, related_count: int = 0
) -> EntityOut:
    return EntityOut(
        id=entity.id,
        entity_type=entity.entity_type,
        name=entity.name,
        display_name=entity.display_name,
        subtitle=entity.subtitle,
        era=entity.era,
        chapter_id=entity.chapter_id,
        short_summary=entity.short_summary,
        body_markdown=entity.body_markdown,
        image_url=entity.image_url,
        verification_label=entity.verification_label or "historical_fact",
        review_status=entity.review_status or "approved",
        sort_order=int(entity.sort_order or 0),
        extra=entity.extra or {},
        source_count=source_count,
        related_entity_count=related_count,
        chapter_ids=list(entity.chapter_ids or ([entity.chapter_id] if entity.chapter_id else [])),
    )


def _source_counts(db: Session, entity_ids: list[str]) -> dict[str, int]:
    """每个实体通过 claim_sources 关联到的去重来源数。"""
    if not entity_ids:
        return {}
    rows = db.execute(
        select(Claim.entity_id, func.count(func.distinct(ClaimSource.source_id)))
        .join(ClaimSource, ClaimSource.claim_id == Claim.id)
        .where(Claim.entity_id.in_(entity_ids))
        .group_by(Claim.entity_id)
    ).all()
    return {entity_id: int(count or 0) for entity_id, count in rows if entity_id}


def _related_counts(db: Session, entity_ids: list[str]) -> dict[str, int]:
    """每个实体的相邻实体数（出边 + 入边去重）。"""
    if not entity_ids:
        return {}
    counts: dict[str, set[str]] = {eid: set() for eid in entity_ids}
    rows = db.execute(
        select(Relation.source_entity_id, Relation.target_entity_id).where(
            or_(
                Relation.source_entity_id.in_(entity_ids),
                Relation.target_entity_id.in_(entity_ids),
            )
        )
    ).all()
    for src, tgt in rows:
        if src in counts and tgt:
            counts[src].add(tgt)
        if tgt in counts and src:
            counts[tgt].add(src)
    return {eid: len(peers) for eid, peers in counts.items()}


def list_entities(
    db: Session,
    chapter_id: str | None = None,
    entity_type: str | None = None,
    review_status: str | None = None,
) -> list[EntityOut]:
    """实体列表。可按章节 / 类型过滤。"""
    stmt = select(Entity)
    if chapter_id:
        # 跨章共用实体（如「长安」同属汉代与唐代）在任一所属章节下都应能查到
        stmt = stmt.where(
            or_(Entity.chapter_id == chapter_id, Entity.chapter_ids.contains([chapter_id]))
        )
    if entity_type:
        stmt = stmt.where(Entity.entity_type == entity_type)
    if review_status:
        stmt = stmt.where(Entity.review_status == review_status)
    rows = db.execute(stmt.order_by(Entity.chapter_id, Entity.sort_order, Entity.id)).scalars().all()
    ids = [e.id for e in rows]
    src_counts = _source_counts(db, ids)
    rel_counts = _related_counts(db, ids)
    return [_entity_out(e, src_counts.get(e.id, 0), rel_counts.get(e.id, 0)) for e in rows]


def get_entity(db: Session, entity_id: str) -> EntityOut | None:
    entity = db.get(Entity, entity_id)
    if entity is None:
        return None
    return _entity_out(
        entity,
        _source_counts(db, [entity_id]).get(entity_id, 0),
        _related_counts(db, [entity_id]).get(entity_id, 0),
    )


def get_entities_by_ids(db: Session, entity_ids: list[str]) -> list[Entity]:
    """按 ID 批量取实体（返回 ORM 对象，供图谱等服务内部使用）。"""
    if not entity_ids:
        return []
    return list(db.execute(select(Entity).where(Entity.id.in_(entity_ids))).scalars().all())


def get_entity_sources(db: Session, entity_id: str) -> list[SourceOut]:
    """实体关联的来源，附带「该来源支持了哪些具体 claim」。

    路径：entity → claims → claim_sources → sources。
    设计系统 §36 要求不能只列参考文献名，所以 claims 一定要带上。
    """
    rows = db.execute(
        select(Source, Claim.id, Claim.claim_text)
        .join(ClaimSource, ClaimSource.source_id == Source.id)
        .join(Claim, Claim.id == ClaimSource.claim_id)
        .where(Claim.entity_id == entity_id)
        .order_by(Source.source_level, Source.id)
    ).all()

    grouped: dict[str, SourceOut] = {}
    for source, claim_id, claim_text in rows:
        out = grouped.get(source.id)
        if out is None:
            out = SourceOut(
                id=source.id,
                title=source.title,
                author=source.author,
                institution=source.institution,
                source_type=source.source_type,
                source_level=source.source_level,
                publication_year=source.publication_year,
                public_url=source.public_url,
                bibliography=source.bibliography,
                license_note=source.license_note,
                source_perspective=source.source_perspective,
                review_status=source.review_status or "approved",
            )
            grouped[source.id] = out
        if claim_id and claim_text:
            out.claims.append(SourceClaimOut(claim_id=claim_id, text=claim_text))

    return list(grouped.values())


def get_sources_by_ids(db: Session, source_ids: list[str]) -> dict[str, Source]:
    """按 ID 批量取来源 ORM 对象，返回 {id: Source}。"""
    if not source_ids:
        return {}
    rows = db.execute(select(Source).where(Source.id.in_(source_ids))).scalars().all()
    return {s.id: s for s in rows}


def get_entity_claims(db: Session, entity_id: str) -> list[ClaimOut]:
    """实体的 claim 列表（含通过 claim_sources 关联的 source_ids）。"""
    rows = db.execute(select(Claim).where(Claim.entity_id == entity_id)).scalars().all()
    if not rows:
        return []
    claim_ids = [c.id for c in rows]
    src_rows = db.execute(
        select(ClaimSource.claim_id, ClaimSource.source_id).where(
            ClaimSource.claim_id.in_(claim_ids)
        )
    ).all()
    by_claim: dict[str, list[str]] = {}
    for claim_id, source_id in src_rows:
        by_claim.setdefault(claim_id, []).append(source_id)

    return [
        ClaimOut(
            id=c.id,
            entity_id=c.entity_id,
            relation_id=c.relation_id,
            claim_text=c.claim_text,
            claim_type=c.claim_type or "fact",
            controversy_status=c.controversy_status or "stable",
            review_status=c.review_status or "approved",
            source_ids=by_claim.get(c.id, []),
        )
        for c in rows
    ]


# ============================================================
# 场景与热点
# ============================================================


def _hotspot_out(hotspot: SceneHotspot) -> HotspotOut:
    return HotspotOut(
        id=hotspot.id,
        entity_id=hotspot.entity_id,
        shape=hotspot.shape or "polygon",
        normalized_points=hotspot.normalized_points or [],
        label=hotspot.label,
        group_key=hotspot.group_key,
        certainty=hotspot.certainty,
        route_scope=hotspot.route_scope,
        sort_order=int(hotspot.sort_order or 0),
    )


def get_scene(db: Session, scene_id: str) -> SceneOut | None:
    """按场景 ID 取场景（含热点）。不存在时返回 None。"""
    scene = db.get(Scene, scene_id)
    if scene is None:
        return None
    return _scene_out(db, scene)


def get_chapter_scene(db: Session, chapter_id: str) -> SceneOut | None:
    """按章节取首个场景。该章没有场景时返回 None。"""
    scene = db.execute(
        select(Scene).where(Scene.chapter_id == chapter_id).order_by(Scene.id).limit(1)
    ).scalars().first()
    if scene is None:
        return None
    return _scene_out(db, scene)


def _scene_out(db: Session, scene: Scene) -> SceneOut:
    hotspots = db.execute(
        select(SceneHotspot)
        .where(SceneHotspot.scene_id == scene.id, SceneHotspot.enabled.is_(True))
        .order_by(SceneHotspot.sort_order, SceneHotspot.id)
    ).scalars().all()

    workbench = None
    if (scene.scene_kind or "") == "workbench" and scene.chapter_id:
        extra = db.get(ChapterExtra, scene.chapter_id)
        if extra is not None and isinstance(extra.data, dict):
            workbench = extra.data.get("workbench")
        if not workbench:
            # 工坊配置定义在 content/<章>/scene.json 的 workbench 字段，
            # 而 chapter_extras 表存的是 extra.json。两者不是同一个文件，
            # 所以这里回退到内容目录，避免数据库漏存导致工坊渲染不出来。
            try:
                workbench = content_loader.load_scene_config(scene.chapter_id).get("workbench")
            except Exception as exc:  # noqa: BLE001
                logger.warning("读取工坊配置失败 %s：%s", scene.chapter_id, exc)
                workbench = None

    # 地图形态随场景一并返回。地图 id 与场景 id 同名（如 qing_torghut_return_map），
    # 取不到时留空，前端会回退到自己的兜底渲染，不会崩。
    historical_map = None
    if (scene.scene_kind or "") == "map":
        try:
            historical_map = get_map(db, scene.id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("读取地图 %s 失败：%s", scene.id, exc)
            historical_map = None

    return SceneOut(
        id=scene.id,
        chapter_id=scene.chapter_id,
        name=scene.name,
        scene_kind=scene.scene_kind or "image",
        background_asset_id=scene.background_asset_id,
        width=scene.width,
        height=scene.height,
        disclaimer=scene.disclaimer,
        hotspots=[_hotspot_out(h) for h in hotspots],
        workbench=workbench,
        map=historical_map,
    )


# ============================================================
# 地图
# ============================================================


def get_map(db: Session, map_id: str) -> HistoricalMapOut | None:
    """历史地图（含节点与区段）。不存在时返回 None。"""
    historical_map = db.get(HistoricalMap, map_id)
    if historical_map is None:
        return None

    nodes = db.execute(
        select(MapNode).where(MapNode.map_id == map_id).order_by(MapNode.sort_order, MapNode.id)
    ).scalars().all()
    segments = db.execute(
        select(MapSegment).where(MapSegment.map_id == map_id).order_by(MapSegment.id)
    ).scalars().all()

    return HistoricalMapOut(
        id=historical_map.id,
        name=historical_map.name,
        coordinate_system=historical_map.coordinate_system or "normalized_canvas",
        disclaimer=historical_map.disclaimer,
        nodes=[
            MapNodeOut(
                id=n.id,
                entity_id=n.entity_id,
                label=n.label,
                x=float(n.x or 0.0),
                y=float(n.y or 0.0),
                certainty=n.certainty or "confirmed_region",
                route_scope=n.route_scope or "MASS_MIGRATION",
                sort_order=int(n.sort_order or 0),
            )
            for n in nodes
        ],
        segments=[
            MapSegmentOut(
                id=s.id,
                from_node_id=s.from_node_id,
                to_node_id=s.to_node_id,
                label=s.label,
                geometry=s.geometry or [],
                certainty=s.certainty or "approximate_corridor",
                route_scope=s.route_scope or "MASS_MIGRATION",
                source_ids=s.source_ids or [],
                claim_ids=s.claim_ids or [],
            )
            for s in segments
        ],
    )


def get_chapter_map_id(db: Session, chapter_id: str) -> str | None:
    """该章的地图 ID（首页「进入地图」按钮用）。"""
    row = db.execute(
        select(HistoricalMap.id).where(HistoricalMap.chapter_id == chapter_id).limit(1)
    ).scalar()
    return row


# ============================================================
# 时间轴
# ============================================================


def get_timeline(db: Session, chapter_id: str) -> list[TimelineEventOut]:
    """证据时间轴。display_date 原样保留精度，不格式化。"""
    rows = db.execute(
        select(TimelineEvent)
        .where(TimelineEvent.chapter_id == chapter_id)
        .order_by(TimelineEvent.sort_value, TimelineEvent.sort_order, TimelineEvent.id)
    ).scalars().all()
    return [
        TimelineEventOut(
            id=e.id,
            entity_id=e.entity_id,
            display_date=e.display_date,
            date_precision=e.date_precision or "year",
            title=e.title,
            summary=e.summary,
            entity_ids=e.entity_ids or [],
            source_ids=e.source_ids or [],
        )
        for e in rows
    ]


# ============================================================
# 历史数字（估算）
# ============================================================


def get_estimates(db: Session, chapter_id: str, metric: str | None = None) -> list[EstimateGroupOut]:
    """按 metric 分组的历史数字。多来源并列，绝不求平均。

    没有 metric 参数时返回该章全部指标的分组。
    """
    stmt = select(HistoricalEstimate).where(HistoricalEstimate.chapter_id == chapter_id)
    if metric:
        stmt = stmt.where(HistoricalEstimate.metric == metric)
    rows = db.execute(stmt.order_by(HistoricalEstimate.metric, HistoricalEstimate.id)).scalars().all()
    if not rows:
        return []

    source_map = get_sources_by_ids(db, [r.source_id for r in rows if r.source_id])

    groups: dict[str, EstimateGroupOut] = {}
    for row in rows:
        group = groups.get(row.metric)
        if group is None:
            group = EstimateGroupOut(
                metric=row.metric,
                display_name=row.display_name,
                display_policy=row.display_policy or "show_all_approved",
            )
            groups[row.metric] = group
        source = source_map.get(row.source_id or "")
        group.estimates.append(
            HistoricalEstimateOut(
                id=row.id,
                metric=row.metric,
                display_name=row.display_name,
                value_text=row.value_text,
                source_id=row.source_id,
                source_title=source.title if source else None,
                source_institution=source.institution if source else None,
                scope_note=row.scope_note,
                estimate_type=row.estimate_type,
            )
        )
    return list(groups.values())


# ============================================================
# 证据对照（北魏）
# ============================================================


def get_comparison(db: Session, chapter_id: str) -> ComparisonOut:
    """证据对照分组与条目。数据库为空时返回空 groups / items。"""
    groups = db.execute(
        select(ComparisonGroup)
        .where(ComparisonGroup.chapter_id == chapter_id)
        .order_by(ComparisonGroup.sort_order, ComparisonGroup.id)
    ).scalars().all()

    items = db.execute(
        select(EvidenceItem)
        .where(EvidenceItem.chapter_id == chapter_id)
        .order_by(EvidenceItem.group_key, EvidenceItem.site_key, EvidenceItem.id)
    ).scalars().all()

    return ComparisonOut(
        groups=[
            ComparisonGroupOut(
                id=g.id, name=g.name, description=g.description, sort_order=int(g.sort_order or 0)
            )
            for g in groups
        ],
        items=[
            EvidenceItemOut(
                id=i.id,
                entity_id=i.entity_id,
                group_key=i.group_key or "",
                site_key=i.site_key or "",
                title=i.title,
                observed=i.observed or "",
                described_by_source=i.described_by_source or "",
                supports=i.supports or "",
                does_not_support=i.does_not_support or "",
                caveat=i.caveat,
                image_url=i.image_url,
                source_ids=i.source_ids or [],
            )
            for i in items
        ],
    )


# ============================================================
# 物品流动（汉代）
# ============================================================


def get_flow_items(db: Session, chapter_id: str) -> list[dict]:
    """物品流动列表（汉代丝路）。数据存在 chapter_extras.data.flow_items。

    数据库无数据时返回空列表 —— 前端渲染为空态而不是报错。
    """
    extra = db.get(ChapterExtra, chapter_id)
    if extra is not None and isinstance(extra.data, dict):
        items = extra.data.get("flow_items")
        if isinstance(items, list) and items:
            return items
    return []


# ============================================================
# 统计
# ============================================================


def content_totals(db: Session) -> dict[str, int]:
    """站内内容总量，用于 /health 与主页展示。空库时全为 0。"""
    def _count(model, *criteria) -> int:
        try:
            stmt = select(func.count()).select_from(model)
            for criterion in criteria:
                stmt = stmt.where(criterion)
            return int(db.execute(stmt).scalar() or 0)
        except Exception:  # noqa: BLE001
            return 0

    return {
        "chapters": _count(Chapter),
        "entities": _count(Entity),
        "artifacts": _count(Entity, Entity.entity_type.in_(["Artifact", "Artwork", "HeritageStructure"])),
        "places": _count(Entity, Entity.entity_type.in_(["Place", "Region", "Site"])),
        "relations": _count(Relation),
        "sources": _count(Source),
        "claims": _count(Claim),
        "chunks": _count(RagChunk),
        "faq": _count(FallbackFaq),
        "characters": _count(Character),
    }
