#!/usr/bin/env python
"""为当代章节补充「平台自绘」的演示共创元素。

## 为什么需要这个脚本

按当代章节规格 §2.6「权利状态必须进入数据层」，**没有明确授权的素材默认拒绝**，
因此 `content/contemporary/` 里已有的 15 个纹样元素全部是
`DISPLAY_ONLY` / `REVIEW_REQUIRED`，没有任何一个允许进入 AI 共创。
这在内容纪律上是对的，但导致比赛演示时 C08 共创流程一步都走不下去。

## 这里怎么解决

补入 4 个**由项目自己绘制**的矢量纹样示意图。它们的权利方是本项目本身，
因此可以合法地允许用于生成 —— 这不是绕过限制，而是真实地持有了权利。

同时严格保留三条内容纪律：

1. **不声称它们是传统羌绣作品**：`verification_label = digital_reconstruction`，
   名称统一带「（数字示意图）」后缀。
2. **不编造寓意**：`meaning_status = GENERAL_CATEGORY_ONLY`，
   只说明它参考了公开资料记载的题材类别，不解释「象征什么」。
3. **不可用于模型训练、不可商用**：`can_use_for_training = false`、
   `commercial_use = false`，并在 `content_team_todo` 里写明
   「正式上线前应由内容组替换为已授权的传世纹样素材，或经传承实践方确认」。

用法：

    cd backend
    .venv/Scripts/python.exe scripts/add_demo_cocreation_elements.py            # 预演
    .venv/Scripts/python.exe scripts/add_demo_cocreation_elements.py --apply    # 写入
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except Exception:
        pass

CONTENT = Path(__file__).resolve().parent.parent.parent / "content" / "contemporary"

TODO = (
    "演示用元素：由《同心千年》项目组自行绘制的数字示意图，用于保证共创流程可演示。"
    "正式上线前应替换为已获授权的传世纹样素材，或经相关传承实践方确认后使用。"
)

# ---------------------------------------------------------------
# 四个演示元素。ID 一律带 demo_ 前缀，与真实素材明显区分，避免日后混淆。
# ---------------------------------------------------------------
DEMO_ELEMENTS = [
    {
        "id": "pattern_demo_flora_01",
        "motif_category_id": "motif_flora",
        "name": "花草题材数字示意图",
        "display_name": "花草题材（数字示意图）",
        "short_summary": "项目自绘的花草题材数字示意图，用于演示共创流程。",
        "body_markdown": (
            "这是一幅由项目组绘制的花草题材数字示意图。羌族刺绣的公开资料中记载，"
            "花草蔬果是常见题材类别之一。本图仅用于说明「花草题材」这一类别在构图上的"
            "一般特征，**不是任何一件传世羌绣作品的记录，也不代表某一种具体传统纹样**。\n\n"
            "关于这一图样的具体文化寓意，当前审核资料没有提供足够依据加以解释，"
            "因此平台不做说明。"
        ),
        "categories_note": "花草蔬果",
    },
    {
        "id": "pattern_demo_bird_01",
        "motif_category_id": "motif_birds_animals",
        "name": "飞禽走兽题材数字示意图",
        "display_name": "飞禽走兽题材（数字示意图）",
        "short_summary": "项目自绘的飞禽走兽题材数字示意图，用于演示共创流程。",
        "body_markdown": (
            "这是一幅由项目组绘制的飞禽走兽题材数字示意图。公开非遗资料将"
            "飞禽走兽列为羌绣常见题材类别之一。本图只说明该类别的一般构图特征，"
            "**不是传世羌绣作品的记录**。\n\n"
            "具体纹样的固定寓意，当前审核资料不足以支持解释，平台不做说明。"
        ),
        "categories_note": "飞禽走兽",
    },
    {
        "id": "pattern_demo_geometric_01",
        "motif_category_id": "motif_geometric",
        "name": "几何构图数字示意图",
        "display_name": "几何构图（数字示意图）",
        "short_summary": "项目自绘的几何构图数字示意图，用于演示共创流程。",
        "body_markdown": (
            "这是一幅由项目组绘制的几何构图数字示意图。需要说明的是，"
            "「几何」这一类别是平台为便于组织内容而设的，"
            "公开非遗资料中并未单列该类别，因此本图只是**平台自绘的通用几何排列示意**，"
            "不代表任何特定的传统纹样。\n\n"
            "平台不对其文化寓意作任何推断。"
        ),
        "categories_note": "平台自设类别（公开资料未单列）",
    },
    {
        "id": "pattern_demo_composite_01",
        "motif_category_id": "motif_flora",
        "name": "组合构图数字示意图",
        "display_name": "组合构图（数字示意图）",
        "short_summary": "项目自绘的组合构图数字示意图，用于演示共创流程。",
        "body_markdown": (
            "这是一幅由项目组绘制的组合构图数字示意图，用于演示「多种题材元素组合」"
            "在共创流程中如何被处理。**它不是传统羌绣作品，也不对应某一种具体纹样**。\n\n"
            "平台不对其文化寓意作任何推断。"
        ),
        "categories_note": "组合示意",
    },
]


def build_entity(spec: dict) -> dict:
    return {
        "id": spec["id"],
        "entity_type": "PatternElement",
        "name": spec["name"],
        "display_name": spec["display_name"],
        "subtitle": "PatternElement / 纹样元素（演示用）",
        "era": "当代",
        "short_summary": spec["short_summary"],
        "body_markdown": spec["body_markdown"],
        "image_url": None,
        "verification_label": "digital_reconstruction",
        "review_status": "review",
        "sort_order": 900,
        "extra": {
            "meaning_status": "GENERAL_CATEGORY_ONLY",
            "meaning_claim_ids": [],
            "motif_category_id": spec["motif_category_id"],
            "rights_record_id": f"rights_{spec['id']}",
            "generation_policy_id": f"policy_{spec['id']}",
            "is_demo_element": True,
            "category_note": spec["categories_note"],
            "forbidden_simplification": (
                "禁止把本元素称为「传统羌绣纹样」或其复原；"
                "禁止为它编造固定文化寓意；"
                "禁止把 AI 基于它生成的结果称为传统羌绣原作。"
            ),
            "content_team_todo": TODO,
        },
    }


def build_rights(spec: dict) -> dict:
    """权利方是项目本身 —— 这是它能够被合法用于生成的真实原因。"""
    return {
        "id": f"rights_{spec['id']}",
        "asset_id": f"asset_{spec['id']}",
        "entity_id": spec["id"],
        "rights_holder": "《同心千年》项目组",
        "rights_basis": "项目自行绘制的数字示意图，未使用任何第三方素材",
        "license_document_ref": None,
        "can_display": True,
        "can_crop": True,
        "can_transform": True,
        "can_use_for_generation": True,
        "can_use_for_training": False,
        "can_download_original": False,
        "commercial_use": False,
        "attribution_required": True,
        "attribution_text": "数字示意图由《同心千年》项目组绘制",
        "valid_from": None,
        "valid_until": None,
        "territory": None,
        "notes": TODO,
        "review_status": "review",
    }


def build_policy(spec: dict) -> dict:
    return {
        "id": f"policy_{spec['id']}",
        "entity_id": spec["id"],
        "policy_type": "ALLOW_COMBINATION",
        "allowed_operations": ["combine", "recolor", "rescale", "recompose"],
        "blocked_operations": ["claim_as_traditional", "claim_as_authentic", "commercial_use"],
        "review_note": TODO,
        "approved_by": None,
        "review_status": "review",
    }


def build_relation(spec: dict) -> dict:
    return {
        "id": f"rel_demo_{spec['id']}_belongs_category",
        "source_entity_id": spec["id"],
        "target_entity_id": spec["motif_category_id"],
        "relation_type": "BELONGS_TO_CATEGORY",
        "display_label": "属于题材",
        "claim_type": "fact",
        "review_status": "review",
        "source_ids": ["src_ihchina_qiang_embroidery"],
        "claim_ids": [],
        "time_scope": None,
        "route_scope": None,
        "certainty": None,
        "source_perspective": None,
        "note": "演示元素与其题材类别的归属关系。元素本身为项目自绘。",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    entities_path = CONTENT / "entities.json"
    extra_path = CONTENT / "extra.json"
    relations_path = CONTENT / "relations.json"

    entities = json.loads(entities_path.read_text(encoding="utf-8"))
    extra = json.loads(extra_path.read_text(encoding="utf-8"))
    relations = json.loads(relations_path.read_text(encoding="utf-8"))

    existing_ids = {e.get("id") for e in entities}
    new_specs = [s for s in DEMO_ELEMENTS if s["id"] not in existing_ids]

    print("=" * 66)
    print("补充平台自绘演示共创元素" + ("" if args.apply else "（预演模式）"))
    print("=" * 66)
    print(f"已有纹样元素：{sum(1 for e in entities if e.get('entity_type') == 'PatternElement')} 个")
    print(f"待新增      ：{len(new_specs)} 个")
    for spec in new_specs:
        print(f"  + {spec['id']:32} {spec['display_name']}")

    # 已有权利记录里有多少允许生成
    allow_before = sum(
        1 for r in extra.get("rights_records", []) if r.get("can_use_for_generation")
    )
    print(f"当前允许用于生成的素材：{allow_before} 个")

    if not new_specs:
        print()
        print("已全部存在，无需改动。")
        return 0

    if not args.apply:
        print()
        print("加 --apply 生效。")
        return 0

    entities.extend(build_entity(s) for s in new_specs)
    relations.extend(build_relation(s) for s in new_specs)
    extra.setdefault("rights_records", []).extend(build_rights(s) for s in new_specs)
    extra.setdefault("generation_policies", []).extend(build_policy(s) for s in new_specs)

    entities_path.write_text(
        json.dumps(entities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    relations_path.write_text(
        json.dumps(relations, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    extra_path.write_text(
        json.dumps(extra, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print()
    print(f"已写入：实体 {len(new_specs)}、关系 {len(new_specs)}、"
          f"权利记录 {len(new_specs)}、生成策略 {len(new_specs)}")
    print("全部标为 review_status=review，并带 content_team_todo 说明待替换。")
    print()
    print("下一步：")
    print("  python scripts/seed_postgres.py && python scripts/seed_neo4j.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
