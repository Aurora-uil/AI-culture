#!/usr/bin/env python
"""把 `content/` 的实体与关系写入 Neo4j。

用法：

    cd backend
    .venv/Scripts/python.exe scripts/seed_neo4j.py          # 幂等写入（MERGE）
    .venv/Scripts/python.exe scripts/seed_neo4j.py --reset  # 先删除全部节点再写入

约定：
- 每个节点同时带 `:Entity` 通用标签与具体类型标签
  （HeritageStructure / Place / Period / InscriptionSet / Script / Text /
   Concept / Person / Artwork / Event / ...），图谱服务统一按 `:Entity` 匹配。
- 边属性带 `id / display_label / claim_type / review_status / source_ids`，
  其中 **claim_type 必须透传**，前端据此渲染实线 / 虚线 / 点划线。
- 全部使用 MERGE，可反复执行。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except Exception:
        pass

from app.db.neo4j import get_driver  # noqa: E402
from app.services import content_loader  # noqa: E402

# 合法标签 / 关系类型：只允许字母数字下划线，防止 Cypher 注入
_SAFE_TOKEN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

VALID_ENTITY_TYPES = {
    "Person", "Artifact", "Place", "Region", "Event", "Script", "Language",
    "Concept", "Period", "HeritageStructure", "InscriptionSet", "Text", "Group",
    "Institution", "Site", "Artwork", "Technique", "MotifCategory",
    "PatternElement", "ObjectType", "Practice", "ICHProject", "AttributionClaim",
    "Work", "Chapter", "RightsRecord",
    # 北魏：改革政策与证据条目
    "Policy", "Evidence",
    # 唐代：画卷中被描绘的人物与人物群像（与画外关联人物区分）
    "DepictedFigure", "DepictedGroup",
}

# 关系类型必须是 UPPER_SNAKE_CASE
VALID_RELATION_TYPES = {
    "LOCATED_IN", "USES_SCRIPT", "HAS_INSCRIPTION_SET", "MENTIONS", "PART_OF",
    "DEPICTS", "CREATED_BY", "COMMISSIONED_BY", "HELD_AT", "RELATED_TO",
    "ASSOCIATED_WITH", "SUCCEEDED_BY", "RECORDED_IN", "SAME_AS", "CONTRASTS_WITH",
    "CURATORIAL_LONGTERM_CONNECTION", "CHAPTER_CORE_ENTITY",
}

DEFAULT_RELATION_TYPE = "RELATED_TO"

BATCH_SIZE = 200


def safe_label(entity_type: str | None) -> str:
    """实体类型 → Neo4j 标签。非法值收敛为 Concept。"""
    if entity_type and entity_type in VALID_ENTITY_TYPES and _SAFE_TOKEN.match(entity_type):
        return entity_type
    return "Concept"


def safe_relation_type(relation_type: str | None) -> str:
    """关系类型 → 大写下划线形式。非法值收敛为 RELATED_TO。"""
    if not relation_type:
        return DEFAULT_RELATION_TYPE
    candidate = str(relation_type).strip().upper().replace(" ", "_").replace("-", "_")
    if not _SAFE_TOKEN.match(candidate):
        return DEFAULT_RELATION_TYPE
    return candidate


def collect_nodes() -> list[dict]:
    """读取六章 entities.json，汇总为节点列表。

    跨章共用实体（如「长安」同属汉代与唐代）合并为一个节点，
    chapter_ids 记录全部所属章节 —— 总图谱靠它把跨时代的对象连起来。
    """
    nodes: dict[str, dict] = {}
    for dir_name in content_loader.available_chapter_dirs():
        chapter_id = content_loader.chapter_id_for_dir(
            dir_name, content_loader.load_chapters_config()
        )
        for item in content_loader.load_chapter_file(dir_name, "entities", default=[]) or []:
            if not isinstance(item, dict) or not item.get("id"):
                continue
            entity_id = item["id"]
            existing = nodes.get(entity_id)
            if existing is not None:
                # 只追加章节归属，保留首个定义的完整内容
                if chapter_id and chapter_id not in existing["chapter_ids"]:
                    existing["chapter_ids"].append(chapter_id)
                    existing["chapter_ids"].sort()
                continue
            nodes[entity_id] = {
                "id": entity_id,
                "name": item.get("name") or entity_id,
                "display_name": item.get("display_name"),
                "subtitle": item.get("subtitle"),
                "short_summary": item.get("short_summary"),
                "entity_type": safe_label(item.get("entity_type")),
                "chapter_id": chapter_id,
                "chapter_ids": [chapter_id] if chapter_id else [],
                "era": item.get("era"),
                "verification_label": item.get("verification_label") or "historical_fact",
                "review_status": item.get("review_status") or "approved",
                "sort_order": int(item.get("sort_order") or 0),
            }
    return list(nodes.values())


def collect_edges(node_ids: set[str]) -> list[dict]:
    """读取六章 relations.json，汇总为边列表。"""
    edges: list[dict] = []
    for dir_name in content_loader.available_chapter_dirs():
        chapter_id = content_loader.chapter_id_for_dir(
            dir_name, content_loader.load_chapters_config()
        )
        for item in content_loader.data_entries(
            content_loader.load_chapter_file(dir_name, "relations", default=[])
        ):
            if not item.get("id"):
                continue
            source = item.get("source_entity_id")
            target = item.get("target_entity_id")
            if source not in node_ids or target not in node_ids:
                continue
            edges.append(
                {
                    "id": item["id"],
                    "source": source,
                    "target": target,
                    "relation_type": safe_relation_type(item.get("relation_type")),
                    # 中文显示词，界面直接展示「位于 / 使用 / 保存有」
                    "display_label": item.get("display_label") or "相关",
                    # claim_type 必须透传
                    "claim_type": item.get("claim_type") or "fact",
                    "review_status": item.get("review_status") or "approved",
                    "source_ids": list(item.get("source_ids") or []),
                    "claim_ids": list(item.get("claim_ids") or []),
                    "certainty": item.get("certainty"),
                    "route_scope": item.get("route_scope"),
                    "chapter_id": chapter_id,
                }
            )
    return edges


def clear_graph(session) -> None:
    """删除全部节点与关系。"""
    session.run("MATCH (n) DETACH DELETE n")


def write_nodes(session, nodes: list[dict]) -> int:
    """按标签分组批量 MERGE 节点。"""
    by_label: dict[str, list[dict]] = {}
    for node in nodes:
        by_label.setdefault(node["entity_type"], []).append(node)

    written = 0
    for label, group in by_label.items():
        # label 已通过 safe_label 白名单校验，可以安全拼接
        cypher = (
            f"UNWIND $rows AS row "
            f"MERGE (n:Entity:{label} {{id: row.id}}) "
            "SET n.name = row.name, "
            "    n.display_name = row.display_name, "
            "    n.subtitle = row.subtitle, "
            "    n.short_summary = row.short_summary, "
            "    n.entity_type = row.entity_type, "
            "    n.chapter_id = row.chapter_id, "
            "    n.chapter_ids = row.chapter_ids, "
            "    n.era = row.era, "
            "    n.verification_label = row.verification_label, "
            "    n.review_status = row.review_status, "
            "    n.sort_order = row.sort_order"
        )
        for index in range(0, len(group), BATCH_SIZE):
            chunk = group[index : index + BATCH_SIZE]
            session.run(cypher, rows=chunk)
            written += len(chunk)
    return written


def write_edges(session, edges: list[dict]) -> int:
    """按关系类型分组批量 MERGE 边。"""
    by_type: dict[str, list[dict]] = {}
    for edge in edges:
        by_type.setdefault(edge["relation_type"], []).append(edge)

    written = 0
    for relation_type, group in by_type.items():
        # relation_type 已通过 safe_relation_type 清洗，可以安全拼接
        cypher = (
            "UNWIND $rows AS row "
            "MATCH (a:Entity {id: row.source}) "
            "MATCH (b:Entity {id: row.target}) "
            f"MERGE (a)-[r:{relation_type} {{id: row.id}}]->(b) "
            "SET r.display_label = row.display_label, "
            "    r.claim_type = row.claim_type, "
            "    r.review_status = row.review_status, "
            "    r.source_ids = row.source_ids, "
            "    r.claim_ids = row.claim_ids, "
            "    r.certainty = row.certainty, "
            "    r.route_scope = row.route_scope, "
            "    r.chapter_id = row.chapter_id, "
            "    r.relation_type = row.relation_type"
        )
        for index in range(0, len(group), BATCH_SIZE):
            chunk = group[index : index + BATCH_SIZE]
            session.run(cypher, rows=chunk)
            written += len(chunk)
    return written


def write_constraint(session) -> None:
    """给 :Entity(id) 建唯一约束，保证 MERGE 不会产生重复节点。"""
    try:
        session.run(
            "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS "
            "FOR (n:Entity) REQUIRE n.id IS UNIQUE"
        )
    except Exception as exc:  # noqa: BLE001 - 约束失败不阻断导入
        print(f"  提示：创建唯一约束失败（不影响导入）：{exc}")


def main() -> int:
    parser = argparse.ArgumentParser(description="把 content/ 的实体与关系写入 Neo4j（幂等）")
    parser.add_argument("--reset", action="store_true", help="导入前删除全部节点")
    args = parser.parse_args()

    nodes = collect_nodes()
    edges = collect_edges({node["id"] for node in nodes})

    if not nodes:
        print("没有读取到任何实体（内容可能尚未生成完成）。")
        print("提示：Neo4j 为空时，图谱接口会自动回退到 PostgreSQL 的 relations 表。")
        return 0

    driver = get_driver()
    try:
        with driver.session() as session:
            if args.reset:
                print("删除既有节点……")
                clear_graph(session)

            write_constraint(session)
            node_count = write_nodes(session, nodes)
            edge_count = write_edges(session, edges)

            total = session.run("MATCH (n:Entity) RETURN count(n) AS c").single()["c"]
            rel_total = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
    except Exception as exc:  # noqa: BLE001
        print(f"写入 Neo4j 失败：{exc}")
        print("请确认容器已启动：docker compose up -d")
        return 1
    finally:
        driver.close()

    print()
    print("Neo4j 写入完成（MERGE，可重复执行）：")
    print(f"  本次处理实体   {node_count}")
    print(f"  本次处理关系   {edge_count}")
    print(f"  库内 :Entity 节点 {total}")
    print(f"  库内关系总数     {rel_total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
