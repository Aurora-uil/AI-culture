"""健康检查。界面据此显示「演示保障模式」。

数据库不可用时不返回 500，而是 status=degraded —— 现场演示时前端仍能启动。
"""

from __future__ import annotations

import logging

from fastapi import APIRouter

from app.config import settings
from app.db import neo4j as neo4j_db
from app.db import postgres as pg_db
from app.schemas.health import EmbeddingStatusOut, HealthOut, LlmStatusOut
from app.services import content_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthOut, summary="服务健康状态")
def get_health() -> HealthOut:
    """返回 Postgres / Neo4j 连通性、LLM 配置、Embedding 配置与内容量统计。

    任何一项探测失败都不抛异常，只体现在字段值上。**这个接口不依赖 get_db**
    —— 数据库整个挂掉时它恰恰是最需要能通的一个接口，不能跟着一起 502。
    """
    postgres_ok = pg_db.ping()
    neo4j_ok = neo4j_db.ping()

    counts: dict[str, int] = {}
    if postgres_ok:
        try:
            with pg_db.SessionLocal() as db:
                counts = content_service.content_totals(db)
        except Exception as exc:  # noqa: BLE001 - 统计失败不影响健康检查
            logger.warning("内容统计失败：%s", exc)
            counts = {}
    if neo4j_ok:
        counts["graph_nodes"] = neo4j_db.node_count()

    return HealthOut(
        status="ok" if (postgres_ok and neo4j_ok) else "degraded",
        postgres=postgres_ok,
        neo4j=neo4j_ok,
        llm=LlmStatusOut(
            configured=settings.llm_configured,
            provider=settings.llm_provider,
            model=settings.llm_model or None,
            demo_mode=settings.demo_mode,
        ),
        embedding=EmbeddingStatusOut(
            provider=settings.embedding_provider,
            configured=settings.embedding_configured,
        ),
        counts=counts,
    )
