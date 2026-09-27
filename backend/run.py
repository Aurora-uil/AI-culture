#!/usr/bin/env python
"""《同心千年》后端启动脚本。

用法：

    cd backend
    .venv/Scripts/python.exe run.py                 # 启动服务（--reload）
    .venv/Scripts/python.exe run.py --no-reload     # 现场演示用，关掉热重载
    .venv/Scripts/python.exe run.py --check         # 只做依赖探测，不启动

等价于：

    .venv/Scripts/python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except Exception:
        pass


def check_dependencies() -> bool:
    """探测 PostgreSQL / Neo4j / LLM 配置。返回是否全部就绪。"""
    from app.config import settings
    from app.db import neo4j as neo4j_db
    from app.db import postgres as pg_db
    from app.services import content_loader

    print("=" * 60)
    print("《同心千年》后端环境自检")
    print("=" * 60)

    postgres_ok = pg_db.ping()
    print(f"  PostgreSQL  {'正常' if postgres_ok else '不可用'}  {settings.database_url}")
    if not postgres_ok:
        print("              提示：先运行 docker compose up -d")

    neo4j_ok = neo4j_db.ping()
    print(f"  Neo4j       {'正常' if neo4j_ok else '不可用'}  {settings.neo4j_uri}")
    if postgres_ok:
        counts = pg_db.table_counts(["chapters", "entities", "relations", "sources", "rag_chunks"])
        print(f"  内容量      {counts}")
        if counts.get("chapters", 0) == 0:
            print("              提示：内容尚未入库，先运行 scripts/seed_postgres.py")
    if neo4j_ok:
        print(f"  图谱节点    {neo4j_db.node_count()}")

    print(f"  LLM         {'已配置 ' + settings.llm_model if settings.llm_configured else '未配置（演示保障模式）'}")
    print(f"  Embedding   {'已配置' if settings.embedding_configured else '未配置（本地中文检索）'}")

    chapters = content_loader.load_chapters_config()
    print(f"  内容目录    {len(chapters)} 章  {content_loader.content_dir()}")

    print("=" * 60)
    neo4j_db.close_driver()
    return postgres_ok


def main() -> int:
    parser = argparse.ArgumentParser(description="启动《同心千年》后端")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址（默认 0.0.0.0，便于局域网演示）")
    parser.add_argument("--port", type=int, default=None, help="端口（默认取 API_PORT）")
    parser.add_argument("--no-reload", action="store_true", help="关闭热重载")
    parser.add_argument("--check", action="store_true", help="只做环境自检")
    args = parser.parse_args()

    from app.config import settings

    if not check_dependencies() and not args.check:
        print()
        print("PostgreSQL 不可用。仍会启动服务（接口将返回空结果），")
        print("但建议先运行：docker compose up -d")
        print()

    if args.check:
        return 0

    port = args.port or settings.api_port

    print()
    print(f"接口地址  http://127.0.0.1:{port}/api/v1")
    print(f"接口文档  http://127.0.0.1:{port}/docs")
    if settings.demo_mode:
        print("当前为演示保障模式：回答来自已审核的预设问答库，界面会明确标注。")
    print()

    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=port,
        reload=not args.no_reload,
        reload_dirs=[str(Path(__file__).resolve().parent / "app")],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
