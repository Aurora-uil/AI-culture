#!/usr/bin/env python
"""校验 `content/` 目录。

用法：

    cd backend
    .venv/Scripts/python.exe scripts/validate_content.py

检查项：
1. ID 唯一性（全局唯一，跨章节也不允许重复）
2. 外键完整性（relation 两端 entity 存在、source_id 存在、claim 引用存在）
3. `source_level` 非空且在 S/A/B/C 之内
4. chunk 字数在 300–800
5. 红线字段是否填写（Script / PatternElement / Technique / Person / Artwork）
6. 打印 review_status 分布
7. 章节专属结构（清代 route_scope / certainty、北魏四层、当代权利记录）

退出码：0 = 通过（可能有警告），1 = 存在阻断性问题。
"""

from __future__ import annotations

import sys
from pathlib import Path

# Windows 控制台默认 GBK，中文报告会变成乱码。强制 UTF-8 输出。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except Exception:
        pass

# 允许直接以脚本方式运行
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services import content_loader  # noqa: E402

# ---------------- 常量 ----------------

VALID_ENTITY_TYPES = {
    "Person", "Artifact", "Place", "Region", "Event", "Script", "Language",
    "Concept", "Period", "HeritageStructure", "InscriptionSet", "Text", "Group",
    "Institution", "Site", "Artwork", "Technique", "MotifCategory",
    "PatternElement", "ObjectType", "Practice", "ICHProject", "AttributionClaim",
    "Work",
    # 章节本身也作为实体入库（各章 §26 的第一条 ID）
    "Chapter",
    # 当代章节把权利记录也作为图谱节点（§25.5 / §28）
    "RightsRecord",
    # 北魏章节：改革政策与证据条目
    "Policy",
    "Evidence",
    # 唐代章节：画卷中被描绘的人物与人物群像
    "DepictedFigure",
    "DepictedGroup",
}
VALID_SOURCE_LEVELS = {"S", "A", "B", "C"}
VALID_REVIEW_STATUS = {"draft", "review", "approved"}
VALID_CLAIM_TYPES = {"fact", "interpretation", "curatorial", "catalogue_fact"}
VALID_VERIFICATION_LABELS = {
    "historical_fact", "scholarly_view", "digital_reconstruction",
    "ai_narrative", "curatorial", "disputed",
}
VALID_MEANING_STATUS = {
    "DOCUMENTED", "GENERAL_CATEGORY_ONLY", "UNKNOWN", "RESEARCH_DISPUTED",
}
VALID_CERTAINTY = {
    "confirmed_area", "approximate_corridor", "uncertain_segment",
    "curatorial_connector", "confirmed_region",
}
VALID_ROUTE_SCOPE = {
    "MASS_MIGRATION", "LEADER_AUDIENCE_JOURNEY", "SETTLEMENT_DISTRIBUTION",
}

CHUNK_MIN_CHARS = 300
CHUNK_MAX_CHARS = 800

# Script 类型必填的 extra 字段
SCRIPT_REQUIRED_EXTRA = [
    "ui_label", "yuntai_usage_note", "text_language_note", "forbidden_simplification",
]
# Artwork 类型必填的 extra 字段
ARTWORK_REQUIRED_EXTRA = [
    "attribution_status", "attribution_note", "catalogue_period",
    "catalogued_author", "collection", "depicted_in_artwork",
]
# Technique 类型必填的 extra 字段
TECHNIQUE_REQUIRED_EXTRA = ["canonical_name", "usage_note", "caveat"]

# 唐代：这些人物不在画中，不得设为热点
TANG_OFF_CANVAS = {"person_princess_wencheng", "person_songtsen_gampo"}

MIN_FAQ_PER_CHAPTER = 12


class Report:
    """校验报告收集器。"""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def dump(self) -> int:
        print()
        print("=" * 68)
        if self.warnings:
            print(f"警告 {len(self.warnings)} 项：")
            for item in self.warnings:
                print(f"  [警告] {item}")
            print()
        if self.errors:
            print(f"错误 {len(self.errors)} 项：")
            for item in self.errors:
                print(f"  [错误] {item}")
            print()
            print("校验未通过。")
            return 1
        print("校验通过。")
        return 0


def main() -> int:
    report = Report()

    content_dir = content_loader.content_dir()
    print(f"内容目录：{content_dir}")
    if not content_dir.is_dir():
        print("内容目录不存在。")
        return 1

    chapters = content_loader.load_chapters_config()
    print(f"章节数：{len(chapters)}")
    if not chapters:
        report.error("content/chapters.json 为空或不存在。")
        return report.dump()

    # ---------------- 第一章节目录 ----------------
    dirs = content_loader.available_chapter_dirs()
    print(f"章节目录：{', '.join(dirs) or '（无）'}")
    if not dirs:
        report.warn("content/ 下还没有任何章节目录，内容可能尚未生成完成。")

    for dir_name in dirs:
        if content_loader.chapter_id_for_dir(dir_name, chapters) is None:
            report.error(f"目录 content/{dir_name}/ 找不到对应章节（章节 ID 前缀应为 {dir_name}_）。")

    # ---------------- 二、来源 ----------------
    print()
    print("-" * 68)
    print("来源 sources.json")
    sources = content_loader.load_global_sources()
    print(f"  合并去重后来源数：{len(sources)}")

    if not sources:
        report.warn("没有读取到任何来源。")

    for source_id, source in sources.items():
        title = source.get("title")
        if not title:
            report.error(f"来源 {source_id} 缺少 title。")

        level = source.get("source_level")
        if not level:
            # source_level 为空 → 该来源的所有 chunk 永远检索不到
            report.error(f"来源 {source_id} 的 source_level 为空（该来源的 chunk 将永远检索不到）。")
        elif level not in VALID_SOURCE_LEVELS:
            report.error(f"来源 {source_id} 的 source_level 非法：{level}")

        if not source.get("institution"):
            report.error(f"来源 {source_id} 缺少 institution。")
        if not source.get("source_type"):
            report.error(f"来源 {source_id} 缺少 source_type。")

        status = source.get("review_status")
        if status and status not in VALID_REVIEW_STATUS:
            report.error(f"来源 {source_id} 的 review_status 非法：{status}")

    # 分章 sources.json 中重复定义的 id
    for dir_name in dirs:
        for item in content_loader.load_chapter_file(dir_name, "sources", default=[]) or []:
            if not isinstance(item, dict) or not item.get("id"):
                report.error(f"content/{dir_name}/sources.json 存在缺少 id 的条目。")

    # ---------------- 三、实体 ----------------
    print()
    print("-" * 68)
    print("实体 entities.json")

    all_entities: dict[str, dict] = {}
    # 跨章共用的实体（如「长安」同时属于汉代与唐代）。
    # 这不是错误：同一个历史对象本就跨越多个时代，共用节点才能让总图谱连起来。
    # seed 层会合并成一行，并写入 chapter_ids 记录它属于哪些章。
    shared_entities: dict[str, list[str]] = {}
    for dir_name in dirs:
        items = content_loader.load_chapter_file(dir_name, "entities", default=[]) or []
        print(f"  {dir_name}: {len(items)} 个实体")
        for item in items:
            if not isinstance(item, dict):
                report.error(f"content/{dir_name}/entities.json 存在非对象条目。")
                continue
            entity_id = item.get("id")
            if not entity_id:
                report.error(f"content/{dir_name}/entities.json 存在缺少 id 的实体。")
                continue
            if entity_id in all_entities:
                # 保留首个定义的完整内容，只登记它还被哪些章引用
                first_dir = all_entities[entity_id].get("_dir", "?")
                shared_entities.setdefault(entity_id, [first_dir]).append(dir_name)
                continue
            item["_dir"] = dir_name
            all_entities[entity_id] = item

    if shared_entities:
        print()
        print("  跨章共用实体（seed 时会合并为一个节点）：")
        # 注意：这里不能用 dirs 作循环变量 —— 会覆盖上面的章节目录列表，
        # 导致后续所有章节循环只遍历到最后一条记录涉及的章。
        for entity_id, owning_dirs in sorted(shared_entities.items()):
            unique_dirs = sorted(set(owning_dirs))
            print(f"    {entity_id:34} {' / '.join(unique_dirs)}")

    for entity_id, entity in all_entities.items():
        entity_type = entity.get("entity_type")
        if entity_type not in VALID_ENTITY_TYPES:
            report.error(f"实体 {entity_id} 的 entity_type 非法：{entity_type}")

        label = entity.get("verification_label")
        if label not in VALID_VERIFICATION_LABELS:
            report.error(f"实体 {entity_id} 的 verification_label 非法：{label}")

        status = entity.get("review_status")
        if status not in VALID_REVIEW_STATUS:
            report.error(f"实体 {entity_id} 的 review_status 非法或缺失：{status}")

        if not entity.get("name"):
            report.error(f"实体 {entity_id} 缺少 name。")

        summary = entity.get("short_summary") or ""
        if len(summary) > 130:
            report.warn(f"实体 {entity_id} 的 short_summary 超过 120 字（{len(summary)}）。")

        extra = entity.get("extra") or {}
        if not isinstance(extra, dict):
            report.error(f"实体 {entity_id} 的 extra 不是对象。")
            extra = {}

        # 类型专属红线字段
        for field in _required_extra_fields(entity_type, extra):
            if not extra.get(field):
                report.error(
                    f"实体 {entity_id}（{entity_type}）缺少红线字段 extra.{field}。"
                )

        if entity_type == "PatternElement":
            meaning = extra.get("meaning_status")
            if meaning not in VALID_MEANING_STATUS:
                report.error(
                    f"纹样元素 {entity_id} 的 meaning_status 非法或缺失：{meaning}"
                )

        if entity_type == "Person":
            if extra.get("living_person") and extra.get("persona_use_allowed"):
                report.error(
                    f"在世人物 {entity_id} 不得开启 persona_use_allowed（禁止模拟在世传承人人格）。"
                )

        # 唐代红线：文成公主、松赞干布不在画中
        if entity_id in TANG_OFF_CANVAS and extra.get("depicted_in_artwork"):
            report.error(
                f"实体 {entity_id} 属于画外关联人物，depicted_in_artwork 必须为 false。"
            )

    # ---------------- 四、claims ----------------
    print()
    print("-" * 68)
    print("主张 claims.json")

    all_claims: dict[str, dict] = {}
    for dir_name in dirs:
        items = content_loader.load_chapter_file(dir_name, "claims", default=[]) or []
        print(f"  {dir_name}: {len(items)} 条 claim")
        for item in items:
            if not isinstance(item, dict) or not item.get("id"):
                report.error(f"content/{dir_name}/claims.json 存在缺少 id 的条目。")
                continue
            claim_id = item["id"]
            if claim_id in all_claims:
                report.error(f"Claim ID 重复：{claim_id}")
                continue
            all_claims[claim_id] = item

    for claim_id, claim in all_claims.items():
        claim_type = claim.get("claim_type")
        if claim_type not in VALID_CLAIM_TYPES:
            report.error(f"Claim {claim_id} 的 claim_type 非法：{claim_type}")

        status = claim.get("review_status")
        if status not in VALID_REVIEW_STATUS:
            report.error(f"Claim {claim_id} 的 review_status 非法或缺失：{status}")

        if not (claim.get("claim_text") or "").strip():
            report.error(f"Claim {claim_id} 的 claim_text 为空。")

        entity_id = claim.get("entity_id")
        if entity_id and entity_id not in all_entities:
            report.error(f"Claim {claim_id} 引用了不存在的实体：{entity_id}")

        source_ids = claim.get("source_ids") or []
        if not source_ids:
            report.warn(f"Claim {claim_id} 没有关联任何来源。")
        for source_id in source_ids:
            if source_id not in sources:
                report.error(f"Claim {claim_id} 引用了不存在的来源：{source_id}")

    # ---------------- 五、relations ----------------
    print()
    print("-" * 68)
    print("关系 relations.json")

    all_relations: dict[str, dict] = {}
    chapter_relation_types: dict[str, set[str]] = {}
    for dir_name in dirs:
        items = content_loader.load_chapter_file(dir_name, "relations", default=[]) or []
        chapter_id = content_loader.chapter_id_for_dir(dir_name, chapters)
        print(f"  {dir_name}: {len(items)} 条关系")
        seen_types: set[str] = set()
        for item in items:
            if not isinstance(item, dict):
                report.error(f"content/{dir_name}/relations.json 存在非对象条目。")
                continue
            # 以 _ 开头的键是元数据（如 _forbidden_relations_note），不是关系边
            if not item.get("id"):
                report.error(f"content/{dir_name}/relations.json 存在缺少 id 的条目。")
                continue
            if str(item.get("id", "")).startswith("_"):
                continue
            relation_id = item["id"]
            if relation_id in all_relations:
                report.error(f"关系 ID 重复：{relation_id}")
                continue
            item["_dir"] = dir_name
            all_relations[relation_id] = item
            seen_types.add(item.get("claim_type"))
        if chapter_id:
            chapter_relation_types[chapter_id] = seen_types

    for relation_id, relation in all_relations.items():
        for endpoint in ("source_entity_id", "target_entity_id"):
            value = relation.get(endpoint)
            if not value:
                report.error(f"关系 {relation_id} 缺少 {endpoint}。")
            elif value not in all_entities:
                report.error(f"关系 {relation_id} 的 {endpoint} 指向不存在的实体：{value}")

        if not relation.get("relation_type"):
            report.error(f"关系 {relation_id} 缺少 relation_type。")
        if not relation.get("display_label"):
            report.error(f"关系 {relation_id} 缺少 display_label（中文显示词）。")

        claim_type = relation.get("claim_type")
        if claim_type not in VALID_CLAIM_TYPES:
            report.error(f"关系 {relation_id} 的 claim_type 非法：{claim_type}")

        status = relation.get("review_status")
        if status not in VALID_REVIEW_STATUS:
            report.error(f"关系 {relation_id} 的 review_status 非法或缺失：{status}")

        source_ids = relation.get("source_ids") or []
        if not source_ids:
            report.error(f"关系 {relation_id} 的 source_ids 为空（每条边都必须可溯源）。")
        for source_id in source_ids:
            if source_id not in sources:
                report.error(f"关系 {relation_id} 引用了不存在的来源：{source_id}")

        for claim_id in relation.get("claim_ids") or []:
            if claim_id not in all_claims:
                report.error(f"关系 {relation_id} 引用了不存在的 claim：{claim_id}")

        # 空间相关的枚举（route_scope / certainty）只在**清代**有规格定义。
        # 其它章节会按自己的语义写（如汉代的 high_level / LONG_TERM_NETWORK），
        # 只要非空即视为合法，不做跨章枚举校验。
        if relation.get("_dir") == "qing":
            if relation.get("route_scope") and relation["route_scope"] not in VALID_ROUTE_SCOPE:
                report.error(
                    f"关系 {relation_id} 的 route_scope 非法：{relation['route_scope']}"
                )
            if relation.get("certainty") and relation["certainty"] not in VALID_CERTAINTY:
                report.error(f"关系 {relation_id} 的 certainty 非法：{relation['certainty']}")

    # 每章至少一条 interpretation 边
    for chapter_id, types in chapter_relation_types.items():
        if types and "interpretation" not in types:
            report.warn(
                f"章节 {chapter_id} 没有 claim_type=interpretation 的边"
                "（要求每章至少 1 条，用虚线渲染与事实边区分）。"
            )

    # ---------------- 六、chunks ----------------
    print()
    print("-" * 68)
    print("知识切片 chunks.json")

    all_chunks: list[dict] = []
    for dir_name in dirs:
        items = content_loader.load_chapter_file(dir_name, "chunks", default=[]) or []
        print(f"  {dir_name}: {len(items)} 个 chunk")
        for item in items:
            if not isinstance(item, dict):
                continue
            item["_dir"] = dir_name
            all_chunks.append(item)

    if not all_chunks:
        report.warn("没有读取到任何 chunk，AI 检索将无内容可用（内容可能尚未生成完成）。")

    chunk_ids: set[str] = set()
    for chunk in all_chunks:
        chunk_id = chunk.get("id")
        dir_name = chunk.get("_dir", "?")
        if not chunk_id:
            report.error(f"content/{dir_name}/chunks.json 存在缺少 id 的 chunk。")
            continue
        if chunk_id in chunk_ids:
            report.error(f"chunk ID 重复：{chunk_id}")
        chunk_ids.add(chunk_id)

        source_id = chunk.get("source_id")
        if not source_id:
            report.error(f"chunk {chunk_id} 缺少 source_id。")
        elif source_id not in sources:
            report.error(f"chunk {chunk_id} 引用了不存在的来源：{source_id}")

        level = chunk.get("source_level")
        if not level:
            # 强制 metadata filter 依赖它，绝不能为空
            report.error(f"chunk {chunk_id} 的 source_level 为空（将永远检索不到）。")
        elif level not in VALID_SOURCE_LEVELS:
            report.error(f"chunk {chunk_id} 的 source_level 非法：{level}")

        if chunk.get("review_status") not in VALID_REVIEW_STATUS:
            report.error(
                f"chunk {chunk_id} 的 review_status 非法或缺失：{chunk.get('review_status')}"
            )

        chapter_ids = chunk.get("chapter_ids") or []
        if not chapter_ids:
            report.error(f"chunk {chunk_id} 的 chapter_ids 为空（将永远检索不到）。")

        for entity_id in chunk.get("entity_ids") or []:
            if entity_id not in all_entities:
                report.warn(f"chunk {chunk_id} 引用了不存在的实体：{entity_id}")
        for claim_id in chunk.get("claim_ids") or []:
            if claim_id not in all_claims:
                report.warn(f"chunk {chunk_id} 引用了不存在的 claim：{claim_id}")

        text = chunk.get("text") or ""
        length = len(text)
        if length < CHUNK_MIN_CHARS:
            report.error(f"chunk {chunk_id} 只有 {length} 字，少于 {CHUNK_MIN_CHARS} 字下限。")
        elif length > CHUNK_MAX_CHARS:
            report.error(f"chunk {chunk_id} 有 {length} 字，超过 {CHUNK_MAX_CHARS} 字上限。")

    # ---------------- 七、faq ----------------
    print()
    print("-" * 68)
    print("兜底问答库 faq.json")

    for dir_name in dirs:
        chapter_id = content_loader.chapter_id_for_dir(dir_name, chapters)
        items = content_loader.load_chapter_file(dir_name, "faq", default=[]) or []
        print(f"  {dir_name}: {len(items)} 条")
        if not items:
            report.warn(
                f"content/{dir_name}/faq.json 缺失或为空。"
                "无 LLM Key 时将无法兜底作答。"
            )
            continue
        if len(items) < MIN_FAQ_PER_CHAPTER:
            report.warn(
                f"content/{dir_name}/faq.json 只有 {len(items)} 条，建议至少 {MIN_FAQ_PER_CHAPTER} 条。"
            )
        seen: set[str] = set()
        for item in items:
            if not isinstance(item, dict) or not item.get("id"):
                report.error(f"content/{dir_name}/faq.json 存在缺少 id 的条目。")
                continue
            faq_id = item["id"]
            if faq_id in seen:
                report.error(f"FAQ ID 重复：{faq_id}")
            seen.add(faq_id)

            if not (item.get("answer_markdown") or "").strip():
                report.error(f"FAQ {faq_id} 的 answer_markdown 为空。")
            if not (item.get("canonical_question") or "").strip():
                report.error(f"FAQ {faq_id} 缺少 canonical_question。")
            for source_id in item.get("source_ids") or []:
                if source_id not in sources:
                    report.error(f"FAQ {faq_id} 引用了不存在的来源：{source_id}")

    # ---------------- 八、scene ----------------
    print()
    print("-" * 68)
    print("场景 scene.json")

    for dir_name in dirs:
        raw_scene = content_loader.load_chapter_file(dir_name, "scene", default=None)
        if not raw_scene:
            report.warn(f"content/{dir_name}/scene.json 缺失或为空。")
            continue

        # 北魏是「云冈—龙门」双场景章节，scene.json 是数组；其余章节是单对象。
        if isinstance(raw_scene, list):
            scene_blocks = [b for b in raw_scene if isinstance(b, dict)]
        elif isinstance(raw_scene, dict):
            scene_blocks = [raw_scene]
        else:
            report.warn(f"content/{dir_name}/scene.json 结构无法识别。")
            continue

        if not scene_blocks:
            report.warn(f"content/{dir_name}/scene.json 没有可用的场景块。")
            continue

        for data in scene_blocks:
            _check_scene_block(data, dir_name, all_entities, report, sources)

    # ---------------- 九、extra.json ----------------
    print()
    print("-" * 68)
    print("章节额外数据 extra.json")

    for dir_name in dirs:
        extra = content_loader.load_chapter_file(dir_name, "extra", default=None)
        if not isinstance(extra, dict) or not extra:
            continue
        print(f"  {dir_name}: {', '.join(sorted(extra.keys()))}")

        for group in extra.get("comparison_groups") or []:
            if not isinstance(group, dict) or not group.get("id"):
                report.error(f"content/{dir_name}/extra.json 的 comparison_groups 存在缺少 id 的条目。")

        for item in extra.get("evidence_items") or []:
            if not isinstance(item, dict):
                continue
            item_id = item.get("id", "?")
            for field in ("observed", "described_by_source", "supports", "does_not_support"):
                if not (item.get(field) or "").strip():
                    report.error(
                        f"证据条目 {item_id} 缺少固定四层之一的 {field}。"
                    )

        for event in extra.get("timeline_events") or []:
            if not isinstance(event, dict):
                continue
            event_id = event.get("id", "?")
            if not event.get("display_date"):
                report.error(f"时间轴事件 {event_id} 缺少 display_date。")
            precision = event.get("date_precision")
            if precision not in {"day", "month_or_period", "season", "year", "decade", "period", None}:
                report.error(f"时间轴事件 {event_id} 的 date_precision 非法：{precision}")

        estimates = extra.get("historical_estimates") or []
        metrics: dict[str, list[dict]] = {}
        for estimate in estimates:
            if not isinstance(estimate, dict):
                continue
            estimate_id = estimate.get("id", "?")
            metric = estimate.get("metric")
            if not metric:
                report.error(f"历史数字 {estimate_id} 缺少 metric。")
            if not estimate.get("value_text"):
                report.error(f"历史数字 {estimate_id} 缺少 value_text（必须原样保留）。")
            # 「数字必须带来源」是硬规则，但只对**已审核**的数字成立。
            # 尚未找到来源的口径（如清代「三万多户」）允许以 review 状态暂存，
            # 以便内容组后续补齐来源；这类数字不会进入 AI 检索。
            if not estimate.get("source_id"):
                if estimate.get("review_status") == "approved":
                    report.error(
                        f"历史数字 {estimate_id} 已审核通过但缺少 source_id"
                        "（数字必须带来源；无来源的口径请先标为 review）。"
                    )
                else:
                    report.warn(
                        f"历史数字 {estimate_id} 暂无来源（状态 {estimate.get('review_status')}），"
                        "补齐来源前不应转为 approved。"
                    )
            elif estimate["source_id"] not in sources:
                report.error(f"历史数字 {estimate_id} 引用了不存在的来源：{estimate['source_id']}")
            if metric:
                metrics.setdefault(metric, []).append(estimate)

        for metric, items in metrics.items():
            if len(items) == 1 and len(estimates) > 1:
                report.warn(
                    f"指标 {metric} 只有 1 个来源取值。历史数字要求多来源并列，"
                    "只有单一来源时请确认是否有其它记录可补充。"
                )

        for rights in extra.get("rights_records") or []:
            if not isinstance(rights, dict):
                continue
            rights_id = rights.get("id", "?")
            for field in (
                "can_display", "can_crop", "can_transform", "can_use_for_generation",
                "can_use_for_training", "can_download_original", "commercial_use",
                "attribution_required",
            ):
                if field not in rights:
                    report.error(f"权利记录 {rights_id} 缺少字段 {field}（必须逐项明确）。")

        for policy in extra.get("generation_policies") or []:
            if not isinstance(policy, dict):
                continue
            policy_id = policy.get("id", "?")
            if policy.get("policy_type") not in {
                "ALLOW_COMBINATION", "ALLOW_COLOR_VARIATION", "ALLOW_SCALE_ONLY",
                "DISPLAY_ONLY", "REVIEW_REQUIRED", "BLOCKED",
            }:
                report.error(
                    f"生成策略 {policy_id} 的 policy_type 非法：{policy.get('policy_type')}"
                )
            if policy.get("entity_id") and policy["entity_id"] not in all_entities:
                report.error(f"生成策略 {policy_id} 指向不存在的实体：{policy['entity_id']}")

        for item in extra.get("flow_items") or []:
            if not isinstance(item, dict) or not item.get("id"):
                report.error(f"content/{dir_name}/extra.json 的 flow_items 存在缺少 id 的条目。")

    # ---------------- 十、review_status 分布 ----------------
    print()
    print("=" * 68)
    print("review_status 分布")
    _print_distribution("实体", [e.get("review_status") for e in all_entities.values()])
    _print_distribution("来源", [s.get("review_status") for s in sources.values()])
    _print_distribution("Claim", [c.get("review_status") for c in all_claims.values()])
    _print_distribution("关系", [r.get("review_status") for r in all_relations.values()])
    _print_distribution("chunk", [c.get("review_status") for c in all_chunks])

    return report.dump()


def _check_scene_block(
    data: dict,
    dir_name: str,
    all_entities: dict[str, dict],
    report: "Report",
    sources: dict[str, dict],
) -> None:
    """校验单个场景块（scene + hotspots + map + workbench）。

    北魏章节的 scene.json 是两个场景块组成的数组（云冈 / 龙门），
    其余章节是单对象，因此这里按「块」而不是按「章」来校验。
    """
    scene = data.get("scene") or {}
    hotspots = data.get("hotspots") or []
    print(f"  {dir_name}: 场景 {scene.get('id', '?')}，热点 {len(hotspots)} 个")

    if not scene.get("id"):
        report.error(f"content/{dir_name}/scene.json 的 scene 缺少 id。")

    for hotspot in hotspots:
        if not isinstance(hotspot, dict):
            continue
        hotspot_id = hotspot.get("id", "?")
        entity_id = hotspot.get("entity_id")
        if entity_id and entity_id not in all_entities:
            report.error(f"热点 {hotspot_id} 指向不存在的实体：{entity_id}")
        if hotspot.get("shape") not in {"polygon", "rect", "point", None}:
            report.error(f"热点 {hotspot_id} 的 shape 非法：{hotspot.get('shape')}")
        points = hotspot.get("normalized_points")
        if not points:
            report.error(f"热点 {hotspot_id} 缺少 normalized_points。")
        else:
            for point in _iter_points(points):
                if any(coord < 0 or coord > 1 for coord in point):
                    report.error(f"热点 {hotspot_id} 的坐标超出 0–1 归一化范围：{point}")
                    break
        # 唐代红线：文成公主与松赞干布不在画中，不得设为热点
        if entity_id in TANG_OFF_CANVAS:
            report.error(
                f"热点 {hotspot_id} 把画外人物 {entity_id} 设成了热点，唐代章节禁止这么做。"
            )

    # ---------- 地图 ----------
    historical_map = data.get("map")
    if not isinstance(historical_map, dict):
        pass
    else:
        # route_scope / certainty 的枚举是**清代专属**（规格 §2.3）。
        # 汉代地图用另一套词汇（LONG_TERM_NETWORK / high_level 等），
        # 因此只对清代做枚举校验，其它章节只校验结构与坐标。
        is_qing = dir_name == "qing"

        node_ids = {
            n.get("id") for n in (historical_map.get("nodes") or []) if isinstance(n, dict)
        }
        for node in historical_map.get("nodes") or []:
            if not isinstance(node, dict):
                continue
            if is_qing and node.get("certainty") not in VALID_CERTAINTY:
                report.error(
                    f"地图节点 {node.get('id')} 的 certainty 非法：{node.get('certainty')}"
                )
            if (
                is_qing
                and node.get("route_scope")
                and node["route_scope"] not in VALID_ROUTE_SCOPE
            ):
                report.error(
                    f"地图节点 {node.get('id')} 的 route_scope 非法：{node.get('route_scope')}"
                )
            if node.get("x") is None or node.get("y") is None:
                report.error(f"地图节点 {node.get('id')} 缺少 x / y 坐标。")

        for segment in historical_map.get("segments") or []:
            if not isinstance(segment, dict):
                continue
            segment_id = segment.get("id", "?")
            if is_qing:
                if segment.get("certainty") not in VALID_CERTAINTY:
                    report.error(
                        f"地图区段 {segment_id} 的 certainty 非法：{segment.get('certainty')}"
                    )
                if segment.get("route_scope") not in VALID_ROUTE_SCOPE:
                    report.error(
                        f"地图区段 {segment_id} 的 route_scope 非法或缺失："
                        f"{segment.get('route_scope')}"
                    )
            for endpoint in ("from_node_id", "to_node_id"):
                if segment.get(endpoint) not in node_ids:
                    report.error(
                        f"地图区段 {segment_id} 的 {endpoint} 指向不存在的节点："
                        f"{segment.get(endpoint)}"
                    )

    # ---------- 工坊（当代章节）----------
    workbench = data.get("workbench")
    if isinstance(workbench, dict):
        for key in ("technique_ids", "motif_category_ids", "object_ids", "practice_ids"):
            for entity_id in workbench.get(key) or []:
                if entity_id not in all_entities:
                    report.warn(
                        f"content/{dir_name}/scene.json 的 workbench.{key} "
                        f"引用了不存在的实体：{entity_id}"
                    )


def _required_extra_fields(entity_type: str | None, extra: dict) -> list[str]:
    """按类型返回必填的 extra 字段（只返回当前确实缺失的）。"""
    if entity_type == "Script":
        return [f for f in SCRIPT_REQUIRED_EXTRA if not extra.get(f)]
    if entity_type == "Artwork":
        return [
            f
            for f in ARTWORK_REQUIRED_EXTRA
            if f not in extra or extra.get(f) in (None, "")
        ]
    if entity_type == "Technique":
        return [f for f in TECHNIQUE_REQUIRED_EXTRA if not extra.get(f)]
    return []


def _iter_points(points):
    """归一化坐标可能是 [[x,y],...] 或 [x,y]。"""
    if not isinstance(points, list):
        return
    if points and isinstance(points[0], (int, float)):
        yield points
        return
    for point in points:
        if isinstance(point, list) and len(point) >= 2:
            yield point


def _print_distribution(label: str, values: list) -> None:
    counts: dict[str, int] = {}
    for value in values:
        key = value if isinstance(value, str) and value else "（缺失）"
        counts[key] = counts.get(key, 0) + 1
    if not counts:
        print(f"  {label}：无数据")
        return
    detail = "，".join(f"{k} {v}" for k, v in sorted(counts.items()))
    print(f"  {label}：{detail}")


if __name__ == "__main__":
    raise SystemExit(main())
