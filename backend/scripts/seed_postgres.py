#!/usr/bin/env python
"""把 `content/` 写入 PostgreSQL。

用法：

    cd backend
    .venv/Scripts/python.exe scripts/seed_postgres.py          # 幂等写入
    .venv/Scripts/python.exe scripts/seed_postgres.py --reset  # 先清空内容表再写入

**幂等**：所有写入使用 `INSERT ... ON CONFLICT (id) DO UPDATE`，
可以反复执行，不会产生重复数据，也不会因为已存在而报错。

内容只改 `content/`，不要在数据库里手改 —— 数据库随时可以被本脚本重建。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Windows 控制台默认 GBK，中文报告会变成乱码。强制 UTF-8 输出。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except Exception:
        pass

from sqlalchemy import text  # noqa: E402
from sqlalchemy.dialects.postgresql import insert as pg_insert  # noqa: E402

from app.db.postgres import SessionLocal, apply_alters, engine  # noqa: E402
from app.services import content_loader  # noqa: E402

# ---------------- 章节 → AI 角色 ----------------
# 角色的 id 取自 chapters.json 的 ai_character_id；这里补上名称、类型与免责声明。
# 免责声明必须在界面固定显示。
CHARACTER_META: dict[str, dict] = {
    "person_zhang_qian": {
        "name": "张骞",
        "character_type": "person",
        "subtitle": "汉代·相遇",
    },
    "person_emperor_xiaowen": {
        "name": "孝文帝",
        "character_type": "person",
        "subtitle": "北魏·交融",
    },
    "artifact_bunian_tu": {
        "name": "《步辇图》",
        "character_type": "artifact",
        "subtitle": "唐代·交流",
    },
    "artifact_yuntai": {
        "name": "居庸关云台",
        "character_type": "artifact",
        "subtitle": "元代·共存",
    },
    "person_ubashi": {
        "name": "渥巴锡",
        "character_type": "person",
        "subtitle": "清代·归属",
    },
    "qiang_workshop_narrator": {
        "name": "羌绣数字工坊讲述者",
        "character_type": "narrator",
        "subtitle": "当代·传承",
    },
}

DEFAULT_DISCLAIMER = (
    "这是 AI 数字叙事角色，不是历史人物本人，也不具有真实意识与完整记忆。"
    "回答只依据已审核的史料，并标注可核查的来源。"
)

# 需要被清空的内容表（--reset 时按外键顺序倒序删除）
RESET_ORDER = [
    "chat_message_feedback", "chat_message_citations", "chat_messages", "chat_sessions",
    "exploration_node_state", "exploration_events", "exploration_sessions",
    "generation_provenance", "generated_assets", "generation_jobs",
    "creation_basket_items", "creation_baskets", "generation_policies", "rights_records",
    "evidence_items", "comparison_groups", "historical_estimates", "timeline_events",
    "map_segments", "map_nodes", "historical_maps", "scene_hotspots", "scenes",
    "fallback_faq", "characters", "rag_chunks", "relations", "claim_sources",
    "claims", "entities", "sources", "chapter_extras", "chapters",
]

stats: dict[str, int] = {}
skipped: list[str] = []


def bump(key: str, count: int = 1) -> None:
    stats[key] = stats.get(key, 0) + count


def upsert_rows(db, model, rows: list[dict], conflict_cols: tuple[str, ...] = ("id",)) -> int:
    """逐行 `INSERT ... ON CONFLICT DO UPDATE`，保证幂等。"""
    if not rows:
        return 0
    table = model.__table__
    written = 0
    for row in rows:
        stmt = pg_insert(table).values(**row)
        update_set = {
            key: stmt.excluded[key] for key in row if key not in conflict_cols
        }
        if update_set:
            stmt = stmt.on_conflict_do_update(
                index_elements=list(conflict_cols), set_=update_set
            )
        else:
            stmt = stmt.on_conflict_do_nothing(index_elements=list(conflict_cols))
        db.execute(stmt)
        written += 1
    return written


def safe_enum(value, allowed: set[str], default: str, label: str) -> str:
    """把违反 CHECK 约束的值收敛到合法值，并记录告警。

    数据库有 CHECK 约束，脏数据会直接让整批 seed 失败。这里宁可降级 + 告警，
    也不让 seed 中断 —— 具体问题由 validate_content.py 报错。
    """
    if isinstance(value, str) and value in allowed:
        return value
    if value not in (None, ""):
        skipped.append(f"{label} 取值非法（{value}），已收敛为 {default}")
    return default


def reset_content(db) -> None:
    """清空内容表。用于内容结构大幅调整后的重建。"""
    # 会话与事件表也一并清掉（它们引用 chapters）
    for table in RESET_ORDER:
        try:
            db.execute(text(f"DELETE FROM {table}"))
        except Exception as exc:  # noqa: BLE001 - 表不存在时忽略
            db.rollback()
            skipped.append(f"清空 {table} 失败（可能表不存在）：{exc}")
    db.commit()


def seed_chapters(db, chapters: list[dict]) -> list[str]:
    from app.models import Chapter

    rows = []
    for chapter in chapters:
        rows.append(
            {
                "id": chapter["id"],
                "slug": chapter.get("slug") or content_loader.slug_for_chapter_id(chapter["id"]),
                "era": chapter.get("era") or "",
                "theme": chapter.get("keyword") or chapter.get("theme") or "",
                "title": chapter.get("title") or "",
                "date_label": chapter.get("date_label"),
                "guiding_question": chapter.get("guiding_question") or "",
                "display_question": chapter.get("display_question"),
                "hero_asset": chapter.get("hero_asset"),
                "accent": chapter.get("accent"),
                "primary_interaction": chapter.get("primary_interaction"),
                "ai_character_id": chapter.get("ai_character_id"),
                "core_entity_ids": list(chapter.get("core_entity_ids") or []),
                "narration": chapter.get("narration"),
                "sort_order": int(chapter.get("sort_order") or 0),
                "status": "approved",
            }
        )
    count = upsert_rows(db, Chapter, rows)
    db.commit()
    bump("chapters", count)
    return [c["id"] for c in chapters]


def seed_sources(db, sources: dict[str, dict]) -> dict[str, dict]:
    from app.models import Source

    rows = []
    for source_id, source in sources.items():
        rows.append(
            {
                "id": source_id,
                "title": source.get("title") or source_id,
                "author": source.get("author"),
                "institution": source.get("institution") or "未标注机构",
                "source_type": safe_enum(
                    source.get("source_type"),
                    {"official", "academic", "book", "professional"},
                    "professional",
                    f"来源 {source_id} 的 source_type",
                ),
                # source_level 绝不能为空，否则该来源的 chunk 永远检索不到
                "source_level": safe_enum(
                    source.get("source_level"),
                    {"S", "A", "B", "C"},
                    "C",
                    f"来源 {source_id} 的 source_level",
                ),
                "publication_year": source.get("publication_year"),
                "public_url": source.get("public_url"),
                "bibliography": source.get("bibliography"),
                "license_note": source.get("license_note"),
                "source_perspective": source.get("source_perspective"),
                "review_status": safe_enum(
                    source.get("review_status"),
                    {"draft", "review", "approved"},
                    "approved",
                    f"来源 {source_id} 的 review_status",
                ),
            }
        )
    count = upsert_rows(db, Source, rows)
    db.commit()
    bump("sources", count)
    return sources


def seed_entities(db, chapter_ids: list[str]) -> dict[str, str]:
    """写入实体，返回 {entity_id: chapter_id}。

    同一个实体 ID 出现在多章时（如「长安」同属汉代与唐代），**合并成一行**：
    `chapter_id` 记首个出现的章（主归属），`chapter_ids` 记全部所属章节。
    这样总图谱才能把跨时代的历史对象连成一个节点。
    """
    from app.models import Entity

    known = set(chapter_ids)
    rows: list[dict] = []
    entity_chapter: dict[str, str] = {}
    # entity_id -> {"row": row, "chapters": [chapter_id, ...], "seen": [dir, ...]}
    merged: dict[str, dict] = {}

    for dir_name in content_loader.available_chapter_dirs():
        derived_chapter = content_loader.chapter_id_for_dir(dir_name, content_loader.load_chapters_config())
        for item in content_loader.load_chapter_file(dir_name, "entities", default=[]) or []:
            if not isinstance(item, dict) or not item.get("id"):
                continue
            entity_id = item["id"]
            # 章节归属以目录为准；文件里写的 chapter_id 必须是已知章节才采纳
            file_chapter = item.get("chapter_id")
            chapter_id = file_chapter if file_chapter in known else derived_chapter
            if chapter_id not in known:
                chapter_id = None
            extra = item.get("extra") if isinstance(item.get("extra"), dict) else {}

            row = {
                "id": entity_id,
                "entity_type": item.get("entity_type") or "Concept",
                "name": item.get("name") or entity_id,
                "display_name": item.get("display_name"),
                "subtitle": item.get("subtitle"),
                "era": item.get("era"),
                "chapter_id": chapter_id,
                "chapter_ids": [chapter_id] if chapter_id else [],
                "short_summary": item.get("short_summary"),
                "body_markdown": item.get("body_markdown"),
                "image_url": item.get("image_url"),
                "verification_label": safe_enum(
                    item.get("verification_label"),
                    {
                        "historical_fact", "scholarly_view", "digital_reconstruction",
                        "ai_narrative", "curatorial", "disputed",
                    },
                    "historical_fact",
                    f"实体 {entity_id} 的 verification_label",
                ),
                "review_status": safe_enum(
                    item.get("review_status"),
                    {"draft", "review", "approved"},
                    "approved",
                    f"实体 {entity_id} 的 review_status",
                ),
                "sort_order": int(item.get("sort_order") or 0),
                "extra": extra,
            }

            if entity_id not in merged:
                merged[entity_id] = {"row": row, "chapters": [], "seen": []}
                entity_chapter[entity_id] = chapter_id or ""
                rows.append(row)
            else:
                # 跨章共用：合并章节列表，保留首个定义的完整内容
                shared = merged[entity_id]["row"]["chapter_ids"]
                if chapter_id and chapter_id not in shared:
                    shared.append(chapter_id)
                shared.sort()

            if chapter_id and chapter_id not in merged[entity_id]["chapters"]:
                merged[entity_id]["chapters"].append(chapter_id)
            merged[entity_id]["seen"].append(dir_name)

    shared_count = sum(1 for m in merged.values() if len(m["chapters"]) > 1)
    if shared_count:
        print(f"  跨章共用实体 {shared_count} 个（已合并为单节点，chapter_ids 记录全部归属）")

    count = upsert_rows(db, Entity, rows)
    db.commit()
    bump("entities", count)
    return entity_chapter


def seed_claims(db, entity_ids: set[str], source_ids: set[str]) -> dict[str, list[str]]:
    from app.models import Claim, ClaimSource

    claim_rows = []
    link_rows: list[tuple[str, str]] = []
    claim_sources: dict[str, list[str]] = {}

    for dir_name in content_loader.available_chapter_dirs():
        for item in content_loader.load_chapter_file(dir_name, "claims", default=[]) or []:
            if not isinstance(item, dict) or not item.get("id"):
                continue
            claim_id = item["id"]
            entity_id = item.get("entity_id")
            if entity_id and entity_id not in entity_ids:
                skipped.append(f"Claim {claim_id} 引用了不存在的实体 {entity_id}，已跳过该关联")
                entity_id = None

            links = [s for s in (item.get("source_ids") or []) if s in source_ids]
            missing = [s for s in (item.get("source_ids") or []) if s not in source_ids]
            for source_id in missing:
                skipped.append(f"Claim {claim_id} 引用了不存在的来源 {source_id}，已跳过")

            claim_rows.append(
                {
                    "id": claim_id,
                    "entity_id": entity_id,
                    "relation_id": item.get("relation_id"),
                    "claim_text": item.get("claim_text") or "",
                    "claim_type": safe_enum(
                        item.get("claim_type"),
                        {"fact", "interpretation", "curatorial", "catalogue_fact"},
                        "fact",
                        f"Claim {claim_id} 的 claim_type",
                    ),
                    "controversy_status": safe_enum(
                        item.get("controversy_status"),
                        {"stable", "disputed"},
                        "stable",
                        f"Claim {claim_id} 的 controversy_status",
                    ),
                    "review_status": safe_enum(
                        item.get("review_status"),
                        {"draft", "review", "approved"},
                        "approved",
                        f"Claim {claim_id} 的 review_status",
                    ),
                }
            )
            claim_sources[claim_id] = links
            for source_id in links:
                link_rows.append((claim_id, source_id))

    bump("claims", upsert_rows(db, Claim, claim_rows))
    db.commit()

    link_dicts = [
        {"claim_id": claim_id, "source_id": source_id, "locator": None,
         "support_type": "direct", "note": None}
        for claim_id, source_id in link_rows
    ]
    bump(
        "claim_sources",
        upsert_rows(db, ClaimSource, link_dicts, conflict_cols=("claim_id", "source_id")),
    )
    db.commit()
    return claim_sources


def seed_relations(db, entity_ids: set[str], source_ids: set[str], claim_ids: set[str]) -> int:
    from app.models import Relation

    rows = []
    chapters = content_loader.load_chapters_config()

    for dir_name in content_loader.available_chapter_dirs():
        chapter_id = content_loader.chapter_id_for_dir(dir_name, chapters)
        for item in content_loader.data_entries(
            content_loader.load_chapter_file(dir_name, "relations", default=[])
        ):
            if not item.get("id"):
                continue
            relation_id = item["id"]
            source_entity = item.get("source_entity_id")
            target_entity = item.get("target_entity_id")
            if source_entity not in entity_ids or target_entity not in entity_ids:
                skipped.append(
                    f"关系 {relation_id} 的端点实体不存在"
                    f"（{source_entity} → {target_entity}），已跳过"
                )
                continue

            link_sources = [s for s in (item.get("source_ids") or []) if s in source_ids]
            link_claims = [c for c in (item.get("claim_ids") or []) if c in claim_ids]

            rows.append(
                {
                    "id": relation_id,
                    "source_entity_id": source_entity,
                    "target_entity_id": target_entity,
                    "relation_type": item.get("relation_type") or "RELATED_TO",
                    "display_label": item.get("display_label") or "相关",
                    "claim_type": safe_enum(
                        item.get("claim_type"),
                        {"fact", "interpretation", "curatorial", "catalogue_fact"},
                        "fact",
                        f"关系 {relation_id} 的 claim_type",
                    ),
                    "review_status": safe_enum(
                        item.get("review_status"),
                        {"draft", "review", "approved"},
                        "approved",
                        f"关系 {relation_id} 的 review_status",
                    ),
                    "source_ids": link_sources,
                    "claim_ids": link_claims,
                    "time_scope": item.get("time_scope"),
                    "route_scope": item.get("route_scope"),
                    "certainty": item.get("certainty"),
                    "source_perspective": item.get("source_perspective"),
                    "chapter_id": chapter_id,
                }
            )

    count = upsert_rows(db, Relation, rows)
    db.commit()
    bump("relations", count)
    return count


def seed_chunks(db, source_ids: set[str], entity_ids: set[str], claim_ids: set[str]) -> int:
    from app.models import RagChunk

    rows = []
    for dir_name in content_loader.available_chapter_dirs():
        for item in content_loader.load_chapter_file(dir_name, "chunks", default=[]) or []:
            if not isinstance(item, dict) or not item.get("id"):
                continue
            chunk_id = item["id"]
            source_id = item.get("source_id")
            if source_id and source_id not in source_ids:
                skipped.append(f"chunk {chunk_id} 引用了不存在的来源 {source_id}，已置空")
                source_id = None

            text_body = item.get("text") or ""
            rows.append(
                {
                    "id": chunk_id,
                    "source_id": source_id,
                    "chapter_ids": list(item.get("chapter_ids") or []),
                    "entity_ids": [e for e in (item.get("entity_ids") or []) if e in entity_ids],
                    "claim_ids": [c for c in (item.get("claim_ids") or []) if c in claim_ids],
                    "title": item.get("title"),
                    "text": text_body,
                    "token_count": len(text_body),
                    "source_level": item.get("source_level"),
                    "meaning_status": item.get("meaning_status"),
                    "review_status": safe_enum(
                        item.get("review_status"),
                        {"draft", "review", "approved"},
                        "approved",
                        f"chunk {chunk_id} 的 review_status",
                    ),
                    # 向量由 build_vectors.py 单独写入，这里不动，避免重复 seed 覆盖掉
                }
            )

    count = upsert_rows(db, RagChunk, rows)
    db.commit()
    bump("chunks", count)
    return count


def seed_characters(db, chapters: list[dict], entity_ids: set[str]) -> int:
    from app.models import Character

    rows = []
    for chapter in chapters:
        character_id = chapter.get("ai_character_id")
        if not character_id:
            continue
        meta = CHARACTER_META.get(character_id, {})
        base_entity_id = character_id if character_id in entity_ids else None
        rows.append(
            {
                "id": character_id,
                "name": meta.get("name") or chapter.get("title") or character_id,
                "character_type": meta.get("character_type") or "narrator",
                "base_entity_id": base_entity_id,
                "chapter_id": chapter["id"],
                "subtitle": meta.get("subtitle") or chapter.get("title"),
                "disclaimer": meta.get("disclaimer") or DEFAULT_DISCLAIMER,
                "system_prompt_version": "v1.0",
                "enabled": True,
                "image_url": meta.get("image_url"),
            }
        )

    count = upsert_rows(db, Character, rows)
    db.commit()
    bump("characters", count)
    return count


def seed_faq(db, chapter_ids: list[str], source_ids: set[str], entity_ids: set[str]) -> int:
    from app.models import FallbackFaq

    known = set(chapter_ids)
    rows = []
    for dir_name in content_loader.available_chapter_dirs():
        chapter_id = content_loader.chapter_id_for_dir(dir_name, content_loader.load_chapters_config())
        if chapter_id not in known:
            chapter_id = None
        for item in content_loader.load_chapter_file(dir_name, "faq", default=[]) or []:
            if not isinstance(item, dict) or not item.get("id"):
                continue
            faq_id = item["id"]
            file_chapter = item.get("chapter_id")
            resolved = file_chapter if file_chapter in known else chapter_id
            rows.append(
                {
                    "id": faq_id,
                    "chapter_id": resolved,
                    "character_id": item.get("character_id"),
                    "canonical_question": item.get("canonical_question") or "",
                    "keywords": list(item.get("keywords") or []),
                    "intent": item.get("intent"),
                    "answer_markdown": item.get("answer_markdown") or "",
                    "source_ids": [s for s in (item.get("source_ids") or []) if s in source_ids],
                    "related_entity_ids": [
                        e for e in (item.get("related_entity_ids") or []) if e in entity_ids
                    ],
                    "review_status": safe_enum(
                        item.get("review_status"),
                        {"draft", "review", "approved"},
                        "approved",
                        f"FAQ {faq_id} 的 review_status",
                    ),
                }
            )

    count = upsert_rows(db, FallbackFaq, rows)
    db.commit()
    bump("faq", count)
    return count


def seed_scenes(db, entity_ids: set[str]) -> None:
    from app.models import HistoricalMap, MapNode, MapSegment, Scene, SceneHotspot

    scene_rows = []
    hotspot_rows = []
    map_rows = []
    node_rows = []
    segment_rows = []

    for chapter_id, data in content_loader.iter_scene_configs():
        scene = data.get("scene") or {}
        scene_id = scene.get("id") or f"{chapter_id}_scene"
        scene_rows.append(
            {
                "id": scene_id,
                "chapter_id": chapter_id,
                "name": scene.get("name") or scene_id,
                "scene_kind": scene.get("scene_kind") or "image",
                "background_asset_id": scene.get("background_asset_id"),
                "width": scene.get("width"),
                "height": scene.get("height"),
                "disclaimer": scene.get("disclaimer"),
                "version": int(scene.get("version") or 1),
                "status": scene.get("status") or "approved",
            }
        )

        for index, hotspot in enumerate(data.get("hotspots") or []):
            if not isinstance(hotspot, dict) or not hotspot.get("id"):
                continue
            entity_id = hotspot.get("entity_id")
            if entity_id and entity_id not in entity_ids:
                skipped.append(
                    f"热点 {hotspot['id']} 指向不存在的实体 {entity_id}，已置空"
                )
                entity_id = None
            hotspot_rows.append(
                {
                    "id": hotspot["id"],
                    "scene_id": scene_id,
                    "entity_id": entity_id,
                    "shape": hotspot.get("shape") or "polygon",
                    "normalized_points": hotspot.get("normalized_points") or [],
                    "label": hotspot.get("label"),
                    "certainty": hotspot.get("certainty"),
                    "route_scope": hotspot.get("route_scope"),
                    "group_key": hotspot.get("group_key"),
                    "sort_order": int(hotspot.get("sort_order") if hotspot.get("sort_order") is not None else index),
                    "enabled": hotspot.get("enabled", True),
                }
            )

        historical_map = data.get("map")
        if isinstance(historical_map, dict) and historical_map.get("id"):
            map_id = historical_map["id"]
            map_rows.append(
                {
                    "id": map_id,
                    "chapter_id": chapter_id,
                    "name": historical_map.get("name") or map_id,
                    "background_asset_id": historical_map.get("background_asset_id"),
                    "coordinate_system": historical_map.get("coordinate_system")
                    or "normalized_canvas",
                    "disclaimer": historical_map.get("disclaimer"),
                }
            )

            node_ids = set()
            for index, node in enumerate(historical_map.get("nodes") or []):
                if not isinstance(node, dict) or not node.get("id"):
                    continue
                node_ids.add(node["id"])
                entity_id = node.get("entity_id")
                if entity_id and entity_id not in entity_ids:
                    skipped.append(
                        f"地图节点 {node['id']} 指向不存在的实体 {entity_id}，已置空"
                    )
                    entity_id = None
                node_rows.append(
                    {
                        "id": node["id"],
                        "map_id": map_id,
                        "entity_id": entity_id,
                        "label": node.get("label") or node["id"],
                        "x": float(node.get("x") or 0.0),
                        "y": float(node.get("y") or 0.0),
                        "certainty": node.get("certainty") or "confirmed_region",
                        "route_scope": node.get("route_scope"),
                        "sort_order": int(node.get("sort_order") if node.get("sort_order") is not None else index),
                    }
                )

            for segment in historical_map.get("segments") or []:
                if not isinstance(segment, dict) or not segment.get("id"):
                    continue
                if (
                    segment.get("from_node_id") not in node_ids
                    or segment.get("to_node_id") not in node_ids
                ):
                    skipped.append(
                        f"地图区段 {segment['id']} 的端点节点不存在，已跳过"
                    )
                    continue
                segment_rows.append(
                    {
                        "id": segment["id"],
                        "map_id": map_id,
                        "from_node_id": segment["from_node_id"],
                        "to_node_id": segment["to_node_id"],
                        "label": segment.get("label"),
                        # 证据不足时保持空数组，绝不虚构精度
                        "geometry": segment.get("geometry") or [],
                        "certainty": segment.get("certainty") or "approximate_corridor",
                        "route_scope": segment.get("route_scope") or "MASS_MIGRATION",
                        "source_ids": list(segment.get("source_ids") or []),
                        "claim_ids": list(segment.get("claim_ids") or []),
                        "review_status": "approved",
                    }
                )

    bump("scenes", upsert_rows(db, Scene, scene_rows))
    db.commit()
    bump("scene_hotspots", upsert_rows(db, SceneHotspot, hotspot_rows))
    db.commit()
    bump("historical_maps", upsert_rows(db, HistoricalMap, map_rows))
    db.commit()
    bump("map_nodes", upsert_rows(db, MapNode, node_rows))
    db.commit()
    bump("map_segments", upsert_rows(db, MapSegment, segment_rows))
    db.commit()


def seed_chapter_extras(db, entity_ids: set[str], source_ids: set[str], claim_ids: set[str]) -> None:
    from app.models import (
        ChapterExtra,
        ComparisonGroup,
        EvidenceItem,
        HistoricalEstimate,
        TimelineEvent,
    )

    extra_rows = []
    group_rows = []
    evidence_rows = []
    timeline_rows = []
    estimate_rows = []

    for dir_name in content_loader.available_chapter_dirs():
        chapter_id = content_loader.chapter_id_for_dir(
            dir_name, content_loader.load_chapters_config()
        )
        extra = content_loader.load_chapter_file(dir_name, "extra", default=None)
        if not isinstance(extra, dict) or not extra or not chapter_id:
            continue

        extra_rows.append({"chapter_id": chapter_id, "data": extra})

        for index, group in enumerate(extra.get("comparison_groups") or []):
            if not isinstance(group, dict) or not group.get("id"):
                continue
            group_rows.append(
                {
                    "id": group["id"],
                    "chapter_id": chapter_id,
                    "name": group.get("name") or group["id"],
                    "description": group.get("description"),
                    "sort_order": int(group.get("sort_order") if group.get("sort_order") is not None else index),
                }
            )

        for item in extra.get("evidence_items") or []:
            if not isinstance(item, dict) or not item.get("id"):
                continue
            entity_id = item.get("entity_id")
            if entity_id and entity_id not in entity_ids:
                entity_id = None
            group_key = item.get("group_key")
            evidence_rows.append(
                {
                    "id": item["id"],
                    "chapter_id": chapter_id,
                    "entity_id": entity_id,
                    "group_key": group_key,
                    "site_key": item.get("site_key"),
                    "title": item.get("title") or item["id"],
                    "observed": item.get("observed"),
                    "described_by_source": item.get("described_by_source"),
                    "supports": item.get("supports"),
                    "does_not_support": item.get("does_not_support"),
                    "caveat": item.get("caveat"),
                    "image_url": item.get("image_url"),
                    "claim_ids": [c for c in (item.get("claim_ids") or []) if c in claim_ids],
                    "source_ids": [s for s in (item.get("source_ids") or []) if s in source_ids],
                    "review_status": "approved",
                }
            )

        for index, event in enumerate(extra.get("timeline_events") or []):
            if not isinstance(event, dict) or not event.get("id"):
                continue
            entity_id = event.get("entity_id")
            if entity_id and entity_id not in entity_ids:
                entity_id = None
            timeline_rows.append(
                {
                    "id": event["id"],
                    "chapter_id": chapter_id,
                    "entity_id": entity_id,
                    "display_date": event.get("display_date") or "",
                    "date_precision": event.get("date_precision"),
                    "sort_value": event.get("sort_value"),
                    "title": event.get("title") or event["id"],
                    "summary": event.get("summary"),
                    "entity_ids": [e for e in (event.get("entity_ids") or []) if e in entity_ids],
                    "claim_ids": [c for c in (event.get("claim_ids") or []) if c in claim_ids],
                    "source_ids": [s for s in (event.get("source_ids") or []) if s in source_ids],
                    "sort_order": int(event.get("sort_order") if event.get("sort_order") is not None else index),
                }
            )

        for item in extra.get("historical_estimates") or []:
            if not isinstance(item, dict) or not item.get("id"):
                continue
            entity_id = item.get("entity_id")
            if entity_id and entity_id not in entity_ids:
                entity_id = None
            source_id = item.get("source_id")
            if source_id and source_id not in source_ids:
                skipped.append(
                    f"历史数字 {item['id']} 引用了不存在的来源 {source_id}，已置空"
                )
                source_id = None
            claim_id = item.get("claim_id")
            if claim_id and claim_id not in claim_ids:
                claim_id = None
            estimate_rows.append(
                {
                    "id": item["id"],
                    "chapter_id": chapter_id,
                    "entity_id": entity_id,
                    "metric": item.get("metric") or "unknown",
                    "display_name": item.get("display_name") or item.get("metric") or "",
                    # value_text 原样保留，不格式化、不换算
                    "value_text": item.get("value_text") or "",
                    "numeric_value": item.get("numeric_value"),
                    "numeric_min": item.get("numeric_min"),
                    "numeric_max": item.get("numeric_max"),
                    "unit": item.get("unit"),
                    "source_id": source_id,
                    "claim_id": claim_id,
                    "scope_note": item.get("scope_note"),
                    "estimate_type": item.get("estimate_type") or "source_reported",
                    "display_policy": item.get("display_policy") or "show_all_approved",
                    "review_status": "approved",
                }
            )

    bump("chapter_extras", upsert_rows(db, ChapterExtra, extra_rows, conflict_cols=("chapter_id",)))
    db.commit()
    bump("comparison_groups", upsert_rows(db, ComparisonGroup, group_rows))
    db.commit()
    bump("evidence_items", upsert_rows(db, EvidenceItem, evidence_rows))
    db.commit()
    bump("timeline_events", upsert_rows(db, TimelineEvent, timeline_rows))
    db.commit()
    bump("historical_estimates", upsert_rows(db, HistoricalEstimate, estimate_rows))
    db.commit()


def seed_rights_and_policies(db, entity_ids: set[str]) -> None:
    from app.models import GenerationPolicy, RightsRecord

    rights_rows = []
    policy_rows = []

    for dir_name in content_loader.available_chapter_dirs():
        extra = content_loader.load_chapter_file(dir_name, "extra", default=None)
        if not isinstance(extra, dict):
            continue

        for item in extra.get("rights_records") or []:
            if not isinstance(item, dict) or not item.get("id"):
                continue
            entity_id = item.get("entity_id")
            if entity_id and entity_id not in entity_ids:
                entity_id = None
            rights_rows.append(
                {
                    "id": item["id"],
                    "asset_id": item.get("asset_id") or item["id"],
                    "entity_id": entity_id,
                    "rights_holder": item.get("rights_holder"),
                    "rights_basis": item.get("rights_basis"),
                    "license_document_ref": item.get("license_document_ref"),
                    # 未明确写明的权利一律按「不允许」处理
                    "can_display": bool(item.get("can_display", False)),
                    "can_crop": bool(item.get("can_crop", False)),
                    "can_transform": bool(item.get("can_transform", False)),
                    "can_use_for_generation": bool(item.get("can_use_for_generation", False)),
                    "can_use_for_training": bool(item.get("can_use_for_training", False)),
                    "can_download_original": bool(item.get("can_download_original", False)),
                    "commercial_use": bool(item.get("commercial_use", False)),
                    "attribution_required": bool(item.get("attribution_required", False)),
                    "attribution_text": item.get("attribution_text"),
                    "valid_from": item.get("valid_from"),
                    "valid_until": item.get("valid_until"),
                    "territory": item.get("territory"),
                    "notes": item.get("notes"),
                    "review_status": safe_enum(
                        item.get("review_status"),
                        {"draft", "review", "approved"},
                        "approved",
                        f"权利记录 {item['id']} 的 review_status",
                    ),
                }
            )

        for item in extra.get("generation_policies") or []:
            if not isinstance(item, dict) or not item.get("id"):
                continue
            entity_id = item.get("entity_id")
            if entity_id and entity_id not in entity_ids:
                skipped.append(
                    f"生成策略 {item['id']} 指向不存在的实体 {entity_id}，已跳过"
                )
                continue
            policy_rows.append(
                {
                    "id": item["id"],
                    "entity_id": entity_id,
                    "policy_type": safe_enum(
                        item.get("policy_type"),
                        {
                            "ALLOW_COMBINATION", "ALLOW_COLOR_VARIATION", "ALLOW_SCALE_ONLY",
                            "DISPLAY_ONLY", "REVIEW_REQUIRED", "BLOCKED",
                        },
                        "BLOCKED",
                        f"生成策略 {item['id']} 的 policy_type",
                    ),
                    "allowed_operations": list(item.get("allowed_operations") or []),
                    "blocked_operations": list(item.get("blocked_operations") or []),
                    "review_note": item.get("review_note"),
                    "approved_by": item.get("approved_by"),
                    "review_status": safe_enum(
                        item.get("review_status"),
                        {"draft", "review", "approved"},
                        "approved",
                        f"生成策略 {item['id']} 的 review_status",
                    ),
                }
            )

    bump("rights_records", upsert_rows(db, RightsRecord, rights_rows))
    db.commit()
    bump("generation_policies", upsert_rows(db, GenerationPolicy, policy_rows))
    db.commit()


def main() -> int:
    parser = argparse.ArgumentParser(description="把 content/ 写入 PostgreSQL（幂等）")
    parser.add_argument("--reset", action="store_true", help="写入前先清空内容表")
    args = parser.parse_args()

    chapters = content_loader.load_chapters_config()
    if not chapters:
        print("content/chapters.json 为空或不存在，无法写入。")
        return 1

    apply_alters()

    db = SessionLocal()
    try:
        if args.reset:
            print("清空既有内容表……")
            reset_content(db)

        chapter_ids = seed_chapters(db, chapters)
        sources = seed_sources(db, content_loader.load_global_sources())
        source_ids = set(sources.keys())

        entity_chapter = seed_entities(db, chapter_ids)
        entity_ids = set(entity_chapter.keys())

        claim_sources = seed_claims(db, entity_ids, source_ids)
        claim_ids = set(claim_sources.keys())

        seed_relations(db, entity_ids, source_ids, claim_ids)
        seed_chunks(db, source_ids, entity_ids, claim_ids)
        seed_characters(db, chapters, entity_ids)
        seed_faq(db, chapter_ids, source_ids, entity_ids)
        seed_scenes(db, entity_ids)
        seed_chapter_extras(db, entity_ids, source_ids, claim_ids)
        seed_rights_and_policies(db, entity_ids)
    finally:
        db.close()
        engine.dispose()

    print()
    print("写入完成（幂等，可重复执行）：")
    for key in sorted(stats):
        print(f"  {key:<22} {stats[key]}")
    if skipped:
        print()
        print(f"跳过 / 收敛 {len(skipped)} 项：")
        for item in skipped[:30]:
            print(f"  - {item}")
        if len(skipped) > 30:
            print(f"  …… 其余 {len(skipped) - 30} 项省略")
    print()
    print("提示：图数据库请另外运行 scripts/seed_neo4j.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
