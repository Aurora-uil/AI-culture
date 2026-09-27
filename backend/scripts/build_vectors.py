#!/usr/bin/env python
"""为 `rag_chunks` 计算并写入向量。

用法：

    cd backend
    .venv/Scripts/python.exe scripts/build_vectors.py
    .venv/Scripts/python.exe scripts/build_vectors.py --force   # 重算已有向量

**没有配置 EMBEDDING_API_KEY 时会跳过并给出提示** —— 检索会自动切换到
纯 Python 中文检索（字符 bigram + 关键词加权），功能不受影响。

向量以 `double precision[]` 存储而非 pgvector 固定维度列：不同供应商维度
不同（1024 / 1536 / 768），固定维度会导致换供应商即全表报错。语料只有
数百条，numpy 暴力余弦在微秒级。
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except Exception:
        pass

import httpx  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.config import settings  # noqa: E402
from app.db.postgres import SessionLocal, engine  # noqa: E402
from app.models import RagChunk  # noqa: E402

BATCH_SIZE = 16
MAX_RETRIES = 2


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """批量向量化。返回顺序与输入一致。"""
    base_url = (settings.embedding_base_url or "").rstrip("/")
    endpoint = f"{base_url}/embeddings" if not base_url.endswith("/embeddings") else base_url
    headers = {
        "Authorization": f"Bearer {settings.embedding_api_key}",
        "Content-Type": "application/json",
    }
    payload = {"model": settings.embedding_model, "input": texts}

    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(endpoint, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
            rows = sorted(data["data"], key=lambda item: item.get("index", 0))
            return [list(row["embedding"]) for row in rows]
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt < MAX_RETRIES:
                await asyncio.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"向量化失败：{last_error}")


async def main_async(force: bool) -> int:
    if not settings.embedding_configured:
        print("未配置 EMBEDDING_API_KEY，跳过向量构建。")
        print()
        print("这不会影响功能：检索会自动使用纯 Python 中文检索")
        print("（字符 bigram + 关键词加权），无需任何外部依赖。")
        print()
        print("如需启用向量检索，请在 backend/.env 中设置：")
        print("  EMBEDDING_PROVIDER=openai_compatible")
        print("  EMBEDDING_BASE_URL=<向量服务地址>")
        print("  EMBEDDING_API_KEY=<你的 Key>")
        print("  EMBEDDING_MODEL=<模型名>")
        return 0

    db = SessionLocal()
    try:
        stmt = select(RagChunk).where(RagChunk.review_status == "approved")
        chunks = list(db.execute(stmt).scalars().all())
        if not chunks:
            print("rag_chunks 表为空，请先运行 scripts/seed_postgres.py。")
            return 0

        pending = [
            chunk for chunk in chunks if force or not chunk.embedding
        ]
        print(f"待处理 chunk：{len(pending)} / {len(chunks)}")
        if not pending:
            print("所有 chunk 都已有向量。如需重算请加 --force。")
            return 0

        written = 0
        started = time.time()
        for index in range(0, len(pending), BATCH_SIZE):
            batch = pending[index : index + BATCH_SIZE]
            texts = [(chunk.title or "") + "\n" + (chunk.text or "") for chunk in batch]
            try:
                vectors = await embed_texts(texts)
            except Exception as exc:  # noqa: BLE001
                print(f"  批次 {index // BATCH_SIZE + 1} 失败：{exc}")
                continue

            for chunk, vector in zip(batch, vectors):
                chunk.embedding = vector
                chunk.embedding_dim = len(vector)
                written += 1

            db.commit()
            print(f"  已写入 {written} / {len(pending)}")

        elapsed = time.time() - started
        print()
        print(f"完成：{written} 条向量，用时 {elapsed:.1f} 秒。")
        if pending:
            print(f"向量维度：{pending[0].embedding_dim or settings.embedding_dim}")
        return 0
    finally:
        db.close()
        engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description="为 rag_chunks 计算向量")
    parser.add_argument("--force", action="store_true", help="重算已有向量")
    args = parser.parse_args()
    return asyncio.run(main_async(args.force))


if __name__ == "__main__":
    raise SystemExit(main())
