"""接口层公共依赖。

探索会话 ID 有两种传法（前端 `client.ts` 的 axios 拦截器统一注入请求头）：

    X-Exploration-Session: exp_xxx

部分接口也支持 `?session_id=` 查询参数。两者都接受，请求头优先。
"""

from __future__ import annotations

import functools
import logging
from collections.abc import Callable
from typing import Any, TypeVar

from fastapi import Header, Query
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

T = TypeVar("T")


def degrade_to(default: Any) -> Callable:
    """路由装饰器：数据库不可用时返回空结果，而不是 500。

    现场演示时 Docker 没起来、或容器中途挂掉，前端仍应能进入页面看到空态，
    而不是满屏报错。只捕获 SQLAlchemy 异常 —— HTTPException（如 404）
    照常抛出，不会被这里吞掉。

    用法：
        @router.get("/chapters", response_model=list[ChapterOut])
        @degrade_to([])
        def list_chapters(...): ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except SQLAlchemyError as exc:
                logger.warning(
                    "数据库不可用，%s 返回空结果：%s", func.__name__, str(exc)[:160]
                )
                return default() if callable(default) else default

        return wrapper

    return decorator


def get_exploration_session_id(
    x_exploration_session: str | None = Header(default=None, alias="X-Exploration-Session"),
    session_id: str | None = Query(default=None),
) -> str | None:
    """取当前探索会话 ID。都没有时返回 None，调用方据此降级。"""
    return x_exploration_session or session_id or None
