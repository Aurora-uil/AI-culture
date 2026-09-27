"""`content/` 目录读取器。

内容目录是项目的单一事实源。seed 脚本、校验脚本、无 Key 时的兜底问答
都从这里读数据。

目录与章节的对应关系由章节 ID 前缀决定，不需要硬编码映射表：

    content/han/            → han_encounter
    content/northern_wei/   → northern_wei_integration
    content/tang/           → tang_exchange
    content/yuan/           → yuan_yuntai
    content/qing/           → qing_return
    content/contemporary/   → contemporary_qiang_embroidery

即：目录名 == 章节 ID 第一个下划线之前的部分；slug == 目录名把下划线换成连字符。
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.config import CONTENT_DIR

logger = logging.getLogger(__name__)

# 六个章节目录（固定顺序，与 chapters.json 的 sort_order 一致）
CHAPTER_DIRS = ["han", "northern_wei", "tang", "yuan", "qing", "contemporary"]

# 各章内容文件
CHAPTER_FILES = {
    "entities": "entities.json",
    "relations": "relations.json",
    "claims": "claims.json",
    "chunks": "chunks.json",
    "faq": "faq.json",
    "sources": "sources.json",
    "scene": "scene.json",
    "extra": "extra.json",
    "flow_items": "flow_items.json",
}


def is_note_entry(item: Any) -> bool:
    """判断内容文件里的条目是否为「说明性备注」而非数据。

    各章 relations.json 里有 `_forbidden_relations_note` 这类条目，用来记录
    「禁止建立哪些边」。它们不是数据，seed 与校验都必须跳过，否则会被当成
    端点缺失的脏数据。
    """
    return isinstance(item, dict) and str(item.get("id") or "").startswith("_")


def data_entries(items: Any) -> list[dict]:
    """过滤掉说明性备注，只保留真正的数据条目。"""
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict) and not is_note_entry(item)]


def read_json(path: Path, default: Any = None) -> Any:
    """读取 JSON 文件。文件不存在或格式错误时返回 default，不抛异常。"""
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取 %s 失败：%s", path, exc)
        return default


def content_dir() -> Path:
    return CONTENT_DIR


def load_chapters_config() -> list[dict]:
    """读取 content/chapters.json，并补上 slug 字段。"""
    raw = read_json(CONTENT_DIR / "chapters.json", default=[]) or []
    chapters: list[dict] = []
    for item in raw:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        chapter = dict(item)
        chapter["slug"] = slug_for_chapter_id(chapter["id"])
        chapters.append(chapter)
    chapters.sort(key=lambda c: c.get("sort_order", 0))
    return chapters


# 章节 ID → 内容目录名 / 前端 slug。
# 不能靠 `id.split("_")[0]` 推导：northern_wei_integration 会得到 "northern"，
# 而实际目录是 content/northern_wei/。
_CHAPTER_KEY: dict[str, str] = {
    "han_encounter": "han",
    "northern_wei_integration": "northern_wei",
    "tang_exchange": "tang",
    "yuan_yuntai": "yuan",
    "qing_return": "qing",
    "contemporary_qiang_embroidery": "contemporary",
}


def slug_for_chapter_id(chapter_id: str) -> str:
    """由章节 ID 推出前端路由 slug。northern_wei_integration → northern-wei"""
    key = _CHAPTER_KEY.get(chapter_id)
    if key:
        return key.replace("_", "-")
    prefix = (chapter_id or "").split("_")[0]
    return prefix.replace("_", "-") if prefix else ""


def chapter_dir_name(chapter_id: str) -> str:
    """由章节 ID 推出内容目录名。han_encounter → han，northern_wei_integration → northern_wei"""
    key = _CHAPTER_KEY.get(chapter_id)
    if key:
        return key
    return (chapter_id or "").split("_")[0]


def chapter_id_for_dir(dir_name: str, chapters: list[dict] | None = None) -> str | None:
    """由目录名反查章节 ID。northern_wei → northern_wei_integration"""
    chapters = chapters if chapters is not None else load_chapters_config()
    for chapter in chapters:
        if chapter_dir_name(chapter["id"]) == dir_name:
            return chapter["id"]
    return None


def chapter_ids() -> list[str]:
    """全部章节 ID，按 sort_order 排序。"""
    return [c["id"] for c in load_chapters_config()]


def load_chapter_file(dir_name: str, key: str, default: Any = None) -> Any:
    """读取某一章的某个内容文件。key 见 CHAPTER_FILES。"""
    filename = CHAPTER_FILES.get(key, f"{key}.json")
    return read_json(CONTENT_DIR / dir_name / filename, default=default)


def load_all_chapters_file(key: str) -> dict[str, list]:
    """读取六章的同名文件，返回 {chapter_id: [...]}。

    只包含文件真实存在的章节，方便调用方区分「没有这个文件」与「文件是空数组」。
    """
    result: dict[str, list] = {}
    chapters = load_chapters_config()
    for dir_name in available_chapter_dirs():
        chapter_id = chapter_id_for_dir(dir_name, chapters)
        if not chapter_id:
            continue
        data = load_chapter_file(dir_name, key, default=None)
        if data is None:
            continue
        if isinstance(data, dict):
            # scene.json 等是对象，包装成单元素列表交由调用方处理
            result[chapter_id] = [data]
        else:
            result[chapter_id] = list(data)
    return result


def available_chapter_dirs() -> list[str]:
    """实际存在的内容目录，保持 CHAPTER_DIRS 的固定顺序。"""
    found = []
    for name in CHAPTER_DIRS:
        if (CONTENT_DIR / name).is_dir():
            found.append(name)
    # 兼容：目录名不在预设列表里也一并纳入
    if CONTENT_DIR.is_dir():
        for path in sorted(CONTENT_DIR.iterdir()):
            if path.is_dir() and path.name not in found and not path.name.startswith("."):
                found.append(path.name)
    return found


def load_global_sources() -> dict[str, dict]:
    """合并全局 content/sources.json 与各章 sources.json，按 id 去重。

    同一 id 出现多次时，先出现的优先（全局表优先于分章表），
    但缺失字段会用后续出现的内容补齐 —— 避免分章表补充了 public_url 却丢失。
    """
    merged: dict[str, dict] = {}

    def _merge(item: dict) -> None:
        src_id = item.get("id")
        if not src_id:
            return
        if src_id not in merged:
            merged[src_id] = dict(item)
            return
        existing = merged[src_id]
        for key, value in item.items():
            if existing.get(key) in (None, "", [], {}) and value not in (None, "", [], {}):
                existing[key] = value

    for item in read_json(CONTENT_DIR / "sources.json", default=[]) or []:
        if isinstance(item, dict):
            _merge(item)

    for dir_name in available_chapter_dirs():
        for item in load_chapter_file(dir_name, "sources", default=[]) or []:
            if isinstance(item, dict):
                _merge(item)

    return merged


def load_all_faq() -> list[dict]:
    """合并六章 faq.json，并补上 chapter_id。"""
    items: list[dict] = []
    chapters = load_chapters_config()
    for dir_name in available_chapter_dirs():
        chapter_id = chapter_id_for_dir(dir_name, chapters)
        for faq in load_chapter_file(dir_name, "faq", default=[]) or []:
            if not isinstance(faq, dict):
                continue
            entry = dict(faq)
            entry.setdefault("chapter_id", chapter_id)
            items.append(entry)
    return items


def load_chapter_extra(chapter_id: str) -> dict:
    """读取某章 extra.json。文件不存在时返回空字典。"""
    dir_name = chapter_dir_name(chapter_id)
    data = load_chapter_file(dir_name, "extra", default=None)
    return data if isinstance(data, dict) else {}


def load_scene_config(chapter_id: str) -> dict:
    """读取某章 scene.json（含 scene / hotspots / map / workbench）。"""
    dir_name = chapter_dir_name(chapter_id)
    data = load_chapter_file(dir_name, "scene", default=None)
    return data if isinstance(data, dict) else {}


def iter_scene_configs():
    """遍历所有存在 scene.json 的章节，产出 (chapter_id, scene_config)。

    大多数章节的 scene.json 是单个对象；
    北魏是「云冈—龙门」双场景章节，文件是一个数组，这里逐个产出，
    否则该章的场景会被整章跳过（syndication 时表现为「北魏没有场景」）。
    """
    chapters = load_chapters_config()
    for dir_name in available_chapter_dirs():
        chapter_id = chapter_id_for_dir(dir_name, chapters)
        if not chapter_id:
            continue
        data = load_chapter_file(dir_name, "scene", default=None)

        if isinstance(data, dict) and data:
            yield chapter_id, data
        elif isinstance(data, list):
            for block in data:
                if isinstance(block, dict) and block:
                    yield chapter_id, block
