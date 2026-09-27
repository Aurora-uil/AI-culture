#!/usr/bin/env python
"""跨章内容归一化。

各章内容由不同的人/流程并行编写，因此会出现两类跨章冲突。
本脚本只处理**必须修掉**的一类，另一类交给 seed 层合并。

1. **Claim ID 跨章重名（必须修）**
   Claim ID 是数据库主键。两章各写了一条同名 claim 时，
   后写入的会静默覆盖前一条，导致溯源丢失。
   处理：把非首个出现的 claim 重命名为 `<原ID>__<章节目录>`，
   并同步更新该章内所有引用（relations.claim_ids、chunks.claim_ids、claims.relation_id）。

2. **实体 ID 跨章重名（不在这里修）**
   如 `place_changan` 同时出现在汉代与唐代，`concept_cultural_exchange`
   出现在汉/唐/元。这是**产品期望的行为** —— 同一个历史对象本就跨越多个时代，
   共用同一节点才能让总图谱真正连起来。
   处理：由 seed 层合并成一行，并写入 `chapter_ids` 数组记录它属于哪些章。
   本脚本只做检测与报告。

用法：

    cd backend
    .venv/Scripts/python.exe scripts/normalize_content.py            # 预演
    .venv/Scripts/python.exe scripts/normalize_content.py --apply    # 实际写入
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

CONTENT_DIR = Path(__file__).resolve().parent.parent.parent / "content"
CHAPTER_DIRS = ["han", "northern_wei", "tang", "yuan", "qing", "contemporary"]


def read_json(path: Path, default=None):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"  !! 读取失败 {path}: {exc}")
        return default


def write_json(path: Path, data) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def find_duplicate_claims() -> dict[str, list[str]]:
    """返回 {claim_id: [章节目录, ...]}，只含出现次数 > 1 的。"""
    seen: dict[str, list[str]] = {}
    for dir_name in CHAPTER_DIRS:
        for claim in read_json(CONTENT_DIR / dir_name / "claims.json", []) or []:
            if isinstance(claim, dict) and claim.get("id"):
                seen.setdefault(claim["id"], []).append(dir_name)
    return {k: v for k, v in seen.items() if len(v) > 1}


def find_duplicate_entities() -> dict[str, list[str]]:
    seen: dict[str, list[str]] = {}
    for dir_name in CHAPTER_DIRS:
        for entity in read_json(CONTENT_DIR / dir_name / "entities.json", []) or []:
            if isinstance(entity, dict) and entity.get("id"):
                seen.setdefault(entity["id"], []).append(dir_name)
    return {k: v for k, v in seen.items() if len(v) > 1}


def rename_claim(dir_name: str, old_id: str, new_id: str, apply: bool) -> int:
    """在指定章节目录内把 old_id 改名为 new_id，返回改动处数。"""
    changed = 0

    claims = read_json(CONTENT_DIR / dir_name / "claims.json", []) or []
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        if claim.get("id") == old_id:
            claim["id"] = new_id
            # 记录改名原因，方便内容组回溯
            claim["renamed_from"] = old_id
            claim["rename_reason"] = "跨章 Claim ID 重名，已按章节加后缀（见 normalize_content.py）"
            changed += 1

    relations = read_json(CONTENT_DIR / dir_name / "relations.json", []) or []
    for relation in relations:
        if not isinstance(relation, dict):
            continue
        ids = relation.get("claim_ids")
        if isinstance(ids, list) and old_id in ids:
            relation["claim_ids"] = [new_id if x == old_id else x for x in ids]
            changed += 1

    chunks = read_json(CONTENT_DIR / dir_name / "chunks.json", []) or []
    for chunk in chunks:
        if not isinstance(chunk, dict):
            continue
        ids = chunk.get("claim_ids")
        if isinstance(ids, list) and old_id in ids:
            chunk["claim_ids"] = [new_id if x == old_id else x for x in ids]
            changed += 1

    if apply and changed:
        write_json(CONTENT_DIR / dir_name / "claims.json", claims)
        if relations:
            write_json(CONTENT_DIR / dir_name / "relations.json", relations)
        if chunks:
            write_json(CONTENT_DIR / dir_name / "chunks.json", chunks)

    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description="跨章内容归一化")
    parser.add_argument("--apply", action="store_true", help="实际写入（默认只预演）")
    args = parser.parse_args()

    print("=" * 66)
    print("跨章内容归一化" + ("" if args.apply else "（预演模式，不会写入）"))
    print("=" * 66)

    # ---------- 一、Claim 重名：必须改 ----------
    print()
    print("【一】Claim ID 跨章重名 —— 必须修复")
    dup_claims = find_duplicate_claims()
    if not dup_claims:
        print("  没有发现重名。")
    total = 0
    for claim_id, dirs in sorted(dup_claims.items()):
        # 保留第一个出现的章节，其余加章节后缀
        for dir_name in dirs[1:]:
            new_id = f"{claim_id}__{dir_name}"
            changed = rename_claim(dir_name, claim_id, new_id, args.apply)
            total += changed
            print(
                f"  {claim_id}\n"
                f"    出现在 {', '.join(dirs)} → 把 {dir_name} 的改名为 {new_id}"
                f"（更新 {changed} 处引用）"
            )
    if dup_claims:
        print(f"  共处理 {total} 处引用。" + ("已写入。" if args.apply else "加 --apply 生效。"))

    # ---------- 二、实体重名：交给 seed 合并 ----------
    print()
    print("【二】实体 ID 跨章重名 —— 由 seed 层合并，不需要修内容")
    dup_entities = find_duplicate_entities()
    if not dup_entities:
        print("  没有发现重名。")
    for entity_id, dirs in sorted(dup_entities.items()):
        print(
            f"  {entity_id:34} 出现在 {', '.join(dirs)}\n"
            f"    → 合并为一个节点，chapter_ids = {dirs}"
        )
    if dup_entities:
        print()
        print("  说明：同一个历史对象跨越多个时代是正常现象（如「长安」同时出现在")
        print("  汉代与唐代）。共用一个节点，正是总图谱能够跨时代连接的前提。")

    print()
    print("=" * 66)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
