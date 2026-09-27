"""PostgreSQL 连接管理。

提供 SQLAlchemy engine / SessionLocal / `get_db` 依赖。

设计要点：
- `pool_pre_ping=True`：容器重启后旧连接自动失效重连，避免演示现场 500。
- 启动探测失败**不阻断应用启动**：所有接口在数据库为空或暂时不可用时
  也必须返回空结果，而不是崩溃。
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Iterator[Session]:
    """FastAPI 依赖：每请求一个 Session，异常时回滚，结束时关闭。"""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def session_scope() -> Iterator[Session]:
    """脚本 / 后台任务用的上下文管理器。"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def ping() -> bool:
    """连通性探测。任何异常都吞掉并返回 False —— 健康检查不应抛错。"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:  # noqa: BLE001 - 探测失败原因只记日志
        logger.warning("PostgreSQL 连接探测失败：%s", exc)
        return False


def table_count(table: str) -> int:
    """统计某张表的行数。表不存在或查询失败时返回 0（接口不报错）。"""
    try:
        with engine.connect() as conn:
            return int(conn.execute(text(f"SELECT count(*) FROM {table}")).scalar() or 0)
    except Exception:  # noqa: BLE001
        return 0


def table_counts(tables: list[str]) -> dict[str, int]:
    """批量统计。用于 /health 的 counts 字段。"""
    return {name: table_count(name) for name in tables}


def apply_alters() -> None:
    """应用 schema.sql 之外的补充字段 / 表。

    `schema.sql` 是已建表的权威定义，不修改它；内容层在实现过程中需要的
    少量补充（章节 slug、角色头像、反馈表等）统一放在 `alters.sql`，
    使用 `IF NOT EXISTS` 写法，可重复执行。
    """
    from pathlib import Path

    alters = Path(__file__).resolve().parent / "alters.sql"
    if not alters.exists():
        return
    sql = alters.read_text(encoding="utf-8")
    try:
        with engine.begin() as conn:
            conn.execute(text(sql))
        logger.info("补充字段 / 表已应用（alters.sql）")
    except Exception as exc:  # noqa: BLE001
        logger.warning("应用 alters.sql 失败：%s", exc)
