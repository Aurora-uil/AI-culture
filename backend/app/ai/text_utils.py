"""中文文本处理工具：字符 bigram、关键词加权、相似度。

无 Embedding Key 时，检索与兜底问答匹配都依赖这里的纯 Python 实现，
不引入 jieba 等分词依赖，避免现场环境不可控。
"""

from __future__ import annotations

import math
import re
from collections import Counter

# 中文停用词（高频但无区分度）
STOPWORDS = {
    "的", "了", "是", "在", "和", "与", "有", "为", "对", "从", "被", "把",
    "这", "那", "它", "他", "她", "我", "你", "们", "个", "什么", "怎么",
    "为什么", "如何", "哪些", "哪个", "吗", "呢", "吧", "啊", "会", "能",
    "可以", "一个", "一种", "以及", "而且", "但是", "因为", "所以", "如果",
    "请", "告诉", "介绍", "一下", "关于", "多少", "是否",
}

# 标点与空白
_PUNCT_RE = re.compile(r"[\s，。！？；：、（）《》“”‘’\[\]{}<>/\\|~`!@#$%^&*()\-_=+.,;:'\"]+")
# 连续英文 / 数字
_LATIN_RE = re.compile(r"[A-Za-z0-9]+")


def normalize(text: str) -> str:
    """归一化：去掉标点、转小写、压缩空白。"""
    if not text:
        return ""
    return _PUNCT_RE.sub("", text).lower()


def char_bigrams(text: str) -> list[str]:
    """字符 bigram。中文不需要分词也能获得不错的检索效果。"""
    normalized = normalize(text)
    if len(normalized) < 2:
        return [normalized] if normalized else []
    return [normalized[i : i + 2] for i in range(len(normalized) - 1)]


def latin_tokens(text: str) -> list[str]:
    """英文 / 数字词元（如 GPS、1771），中文 bigram 覆盖不到。"""
    return [t.lower() for t in _LATIN_RE.findall(text or "")]


def tokenize(text: str) -> list[str]:
    """混合分词：字符 bigram + 拉丁词元。"""
    return char_bigrams(text) + latin_tokens(text)


def extract_keywords(text: str, limit: int = 12) -> list[str]:
    """抽取关键词：按 bigram 频次，过滤停用词与纯数字。"""
    tokens = [
        token
        for token in tokenize(text)
        if token not in STOPWORDS and not token.isdigit() and len(token) >= 2
    ]
    if not tokens:
        # 退化到单字（很短的问句）
        tokens = [c for c in normalize(text) if c not in STOPWORDS]
    return [token for token, _ in Counter(tokens).most_common(limit)]


def bm25_like_score(query_tokens: Counter, doc_tokens: list[str], avg_len: float, k1: float = 1.5, b: float = 0.75) -> float:
    """简化 BM25。语料只有数百条，直接算即可。"""
    if not doc_tokens or not query_tokens:
        return 0.0
    doc_len = len(doc_tokens)
    freqs = Counter(doc_tokens)
    score = 0.0
    for token, qtf in query_tokens.items():
        tf = freqs.get(token, 0)
        if not tf:
            continue
        denom = tf + k1 * (1 - b + b * doc_len / max(avg_len, 1e-6))
        score += (tf * (k1 + 1) / denom) * min(qtf, 2)
    return score


def keyword_overlap(query: str, doc: str, keywords: list[str] | None = None) -> float:
    """关键词命中率（0–1）。用于兜底问答库的 keywords 字段加权。"""
    if not query or not doc:
        return 0.0
    keys = keywords or extract_keywords(query)
    if not keys:
        return 0.0
    normalized_doc = normalize(doc)
    hits = sum(1 for key in keys if key and key in normalized_doc)
    return hits / len(keys)


def jaccard(text_a: str, text_b: str) -> float:
    """字符 bigram Jaccard 相似度（0–1）。"""
    set_a = set(char_bigrams(text_a))
    set_b = set(char_bigrams(text_b))
    if not set_a or not set_b:
        return 0.0
    union = set_a | set_b
    return len(set_a & set_b) / len(union) if union else 0.0


def cosine(vec_a: list[float], vec_b: list[float]) -> float:
    """余弦相似度。维度不一致（换过 embedding 供应商）时返回 0 而不是报错。"""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for a, b in zip(vec_a, vec_b):
        dot += a * b
        norm_a += a * a
        norm_b += b * b
    if norm_a <= 0 or norm_b <= 0:
        return 0.0
    return dot / (math.sqrt(norm_a) * math.sqrt(norm_b))


def truncate(text: str, limit: int = 120) -> str:
    """按字数截断，附省略号。"""
    if not text:
        return ""
    return text if len(text) <= limit else text[: limit - 1] + "…"
