"""Neo4j 连接管理。

driver 为进程级单例。启动探测失败不阻断应用启动：图谱接口在 Neo4j 不可用
或图数据库为空时必须返回空子图，而不是 500。
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager

from neo4j import Driver, GraphDatabase

from app.config import settings

logger = logging.getLogger(__name__)

_driver: Driver | None = None


def get_driver() -> Driver:
    """获取（惰性创建）driver 单例。"""
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
            connection_timeout=5,
            max_connection_lifetime=3600,
        )
    return _driver


def close_driver() -> None:
    global _driver
    if _driver is not None:
        try:
            _driver.close()
        finally:
            _driver = None


@contextmanager
def get_graph_db() -> Iterator[object]:
    """获取一个 Neo4j session。调用方负责捕获异常。"""
    session = get_driver().session(database=settings.neo4j_database)
    try:
        yield session
    finally:
        session.close()


def ping() -> bool:
    """连通性探测。失败只记日志，返回 False。"""
    try:
        get_driver().verify_connectivity()
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Neo4j 连接探测失败：%s", exc)
        return False


def run_query(cypher: str, **params) -> list[dict]:
    """执行 Cypher 并返回记录列表。

    Neo4j 不可用时返回空列表 —— 上层接口因此天然返回空结果而不是 500。
    """
    try:
        with get_graph_db() as session:
            result = session.run(cypher, **params)
            return [dict(record) for record in result]
    except Exception as exc:  # noqa: BLE001
        logger.warning("Neo4j 查询失败（返回空结果）：%s", exc)
        return []


def node_count() -> int:
    """图数据库节点总数，用于 /health。"""
    rows = run_query("MATCH (n) RETURN count(n) AS c")
    return int(rows[0]["c"]) if rows else 0
