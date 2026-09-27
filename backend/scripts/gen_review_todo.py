#!/usr/bin/env python
"""生成 content/REVIEW_TODO.md —— 待内容组核验清单。

项目里有一部分数据是由工程实现方依据规格文档补写的（规格没给 URL、
没给坐标、没给来源分级等）。这些数据在库里标为 draft / review，
不会进入 AI 检索，但必须在交付时明确列出来，交给内容组逐条核验。

本脚本扫描 content/ 目录，把所有非 approved 的条目按章汇总成一张表。

用法：

    cd backend
    .venv/Scripts/python.exe scripts/gen_review_todo.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent.parent
CONTENT = ROOT / "content"
OUT = CONTENT / "REVIEW_TODO.md"

CHAPTERS = [
    ("han", "汉代", "相遇"),
    ("northern_wei", "北魏", "交融"),
    ("tang", "唐代", "交流"),
    ("yuan", "元代", "共存"),
    ("qing", "清代", "归属"),
    ("contemporary", "当代", "传承"),
]

# 各类文件里，要把「待核验说明」写在哪个字段
TODO_FIELDS = ("content_team_todo", "review_note", "rename_reason", "spec_note")


def load(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def rows_of(data) -> list[dict]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for key in ("hotspots", "nodes", "segments", "estimates", "timeline_events",
                    "comparison_groups", "evidence_items", "rights_records",
                    "generation_policies", "flow_items"):
            if isinstance(data.get(key), list):
                return [x for x in data[key] if isinstance(x, dict)]
    return []


def collect() -> dict:
    """按章收集待核验条目。"""
    per_chapter: dict[str, list[dict]] = defaultdict(list)
    source_status: dict[str, list] = {"draft": [], "review": []}

    for dir_name, era, keyword in CHAPTERS:
        base = CONTENT / dir_name

        # 实体 / Claim / 关系 / Chunk
        for key, label in [
            ("entities", "实体"),
            ("claims", "Claim"),
            ("relations", "关系"),
            ("chunks", "知识切片"),
            ("faq", "兜底问答"),
        ]:
            for item in rows_of(load(base / f"{key}.json")):
                if str(item.get("id", "")).startswith("_"):
                    continue
                status = item.get("review_status")
                if status in ("draft", "review"):
                    per_chapter[f"{era} · {keyword}"].append(
                        {
                            "kind": label,
                            "id": item.get("id"),
                            "name": item.get("display_name")
                            or item.get("name")
                            or item.get("canonical_question")
                            or (item.get("claim_text") or "")[:40],
                            "status": status,
                            "todo": next(
                                (item.get(f) for f in TODO_FIELDS if item.get(f)), ""
                            ),
                        }
                    )

        # scene / extra 里的热点、地图、时间轴、估算、权利记录、策略
        scene = load(base / "scene.json")
        for block in rows_of(scene) or ([scene] if isinstance(scene, dict) else []):
            if not isinstance(block, dict):
                continue
            for hs in block.get("hotspots") or []:
                if isinstance(hs, dict) and hs.get("review_status") in ("draft", "review"):
                    per_chapter[f"{era} · {keyword}"].append(
                        {
                            "kind": "热点",
                            "id": hs.get("id"),
                            "name": hs.get("label"),
                            "status": hs["review_status"],
                            "todo": hs.get("content_team_todo", ""),
                        }
                    )
            mp = block.get("map")
            if isinstance(mp, dict):
                for n in mp.get("nodes") or []:
                    if isinstance(n, dict) and n.get("review_status") in ("draft", "review"):
                        per_chapter[f"{era} · {keyword}"].append(
                            {"kind": "地图节点", "id": n.get("id"), "name": n.get("label"),
                             "status": n["review_status"], "todo": n.get("content_team_todo", "")}
                        )

        extra = load(base / "extra.json")
        if isinstance(extra, dict):
            for key, label in [
                ("historical_estimates", "历史数字"),
                ("timeline_events", "时间轴事件"),
                ("rights_records", "权利记录"),
                ("generation_policies", "生成策略"),
                ("evidence_items", "证据条目"),
                ("flow_items", "物品流动"),
            ]:
                for item in extra.get(key) or []:
                    if not isinstance(item, dict):
                        continue
                    if item.get("review_status") in ("draft", "review"):
                        per_chapter[f"{era} · {keyword}"].append(
                            {
                                "kind": label,
                                "id": item.get("id"),
                                "name": item.get("display_name") or item.get("title") or item.get("name"),
                                "status": item["review_status"],
                                "todo": next((item.get(f) for f in TODO_FIELDS if item.get(f)), ""),
                            }
                        )

    # 来源单独统计（关系到能不能被检索）
    for dir_name, era, keyword in CHAPTERS:
        for s in rows_of(load(CONTENT / dir_name / "sources.json")):
            st = s.get("review_status")
            if st in source_status:
                source_status[st].append((era, s.get("id"), s.get("title"),
                                          s.get("source_level"), s.get("public_url")))
    return {"per_chapter": per_chapter, "sources": source_status}


def main() -> int:
    data = collect()
    per_chapter = data["per_chapter"]
    src = data["sources"]

    total = sum(len(v) for v in per_chapter.values())
    lines: list[str] = []
    add = lines.append

    add("# 待内容组核验清单")
    add("")
    add("> 本文件由 `backend/scripts/gen_review_todo.py` 自动生成，请勿手改。")
    add("")
    add("项目里有一部分数据是**由工程实现方依据章节规格文档补写**的 —— "
        "规格没有给 URL、没有给坐标、没有给来源分级，而接口又必须返回完整结构。")
    add("")
    add("这些数据的处理原则是：")
    add("")
    add("1. 一律标 `review_status: draft` 或 `review`，**不标 approved**；")
    add("2. 每条都带 `content_team_todo` 字段，写明具体要核验什么；")
    add("3. **不进入 AI 检索**（检索门禁只放行 approved）；")
    add("4. 界面上以「待核验」状态呈现，不冒充已确认史实。")
    add("")
    add(f"**当前合计待核验条目：{total} 条**")
    add("")
    add("---")
    add("")

    # ---------- 一、来源 ----------
    add("## 一、来源状态（优先处理）")
    add("")
    add("来源状态直接决定内容能不能被 AI 检索到。")
    add("")
    add(f"- `draft`（实现方补写，**书目与 URL 均待补**）：**{len(src['draft'])} 条**")
    add(f"- `review`（已有基本信息，待核验准确性）：**{len(src['review'])} 条**")
    add("")
    if src["draft"]:
        add("### draft 来源")
        add("")
        add("| 章节 | 来源 ID | 标题 | 等级 | 公开链接 |")
        add("|---|---|---|---|---|")
        for era, sid, title, level, url in src["draft"]:
            add(f"| {era} | `{sid}` | {title or '—'} | {level or '—'} | {url or '**缺失**'} |")
        add("")
    if src["review"]:
        add("### review 来源")
        add("")
        add("| 章节 | 来源 ID | 标题 | 等级 | 公开链接 |")
        add("|---|---|---|---|---|")
        for era, sid, title, level, url in src["review"]:
            add(f"| {era} | `{sid}` | {title or '—'} | {level or '—'} | {url or '**缺失**'} |")
        add("")

    add("> 说明：`source_level` 为空的来源，其全部 chunk 会被 RAG 过滤器永久排除。")
    add("> 元代与当代两章的来源等级由实现方按各章 §17.3 定义补全，需内容组确认。")
    add("")

    # ---------- 二、分章明细 ----------
    add("## 二、分章待核验明细")
    add("")
    if not per_chapter:
        add("（无）")
    for dir_name, era, keyword in CHAPTERS:
        key = f"{era} · {keyword}"
        items = per_chapter.get(key) or []
        if not items:
            continue
        counter = Counter(i["kind"] for i in items)
        summary = "、".join(f"{k} {v}" for k, v in counter.most_common())
        add(f"### {key}　（{len(items)} 条：{summary}）")
        add("")
        add("| 类型 | ID | 名称 | 状态 | 待核验事项 |")
        add("|---|---|---|---|---|")
        for it in items[:60]:
            todo = (it["todo"] or "").replace("\n", " ").replace("|", "／")
            if len(todo) > 130:
                todo = todo[:128] + "……"
            name = (str(it["name"] or "—")).replace("|", "／")[:46]
            add(f"| {it['kind']} | `{it['id']}` | {name} | {it['status']} | {todo or '—'} |")
        if len(items) > 60:
            add(f"| … | | | | 另有 {len(items) - 60} 条，见 `content/{dir_name}/` |")
        add("")

    # ---------- 三、最优先处理 ----------
    add("## 三、建议优先处理的三项")
    add("")
    add("1. **元代来源链接** —— 规格文档未提供来源附录，"
        "现有来源的书目信息与 URL 均由实现方补写，无法核验。")
    add("2. **元代五处题刻热点坐标** —— 规格只给出了「藏文」一处的坐标，"
        "其余五处为实现方按 2400×1350 画布拟定的初值；"
        "放入真实场景图后必须重新标注（见 `content/ASSETS.md`）。")
    add("3. **当代素材授权** —— 现有 15 个纹样元素全部为「仅可展示」，"
        "共创流程靠 4 个**项目自绘的演示元素**（`pattern_demo_*`）支撑。"
        "正式上线前应替换为已授权的传世纹样素材，或经传承实践方确认。")
    add("")
    add("---")
    add("")
    add("处理完上述条目后，把对应内容的 `review_status` 改为 `approved`，"
        "再重新执行 `seed_postgres.py` 与 `seed_neo4j.py`，内容即进入 AI 检索。")
    add("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"已生成 {OUT}")
    print(f"  待核验条目：{total} 条")
    print(f"  draft 来源：{len(src['draft'])} 条；review 来源：{len(src['review'])} 条")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
