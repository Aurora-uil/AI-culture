"""《同心千年》后端入口。

启动：
    cd backend
    .venv/Scripts/python.exe -m uvicorn app.main:app --port 8000 --reload

约定：
- 所有 router 挂在 `/api/v1` 前缀下。
- **所有面向用户的中文文案不出现英文堆栈**：异常统一转成中文友好信息。
- 数据库不可用时应用照常启动，接口返回空结果而不是崩溃。
"""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1 import api_router
from app.config import settings
from app.db import neo4j as neo4j_db
from app.db import postgres as pg_db

# Windows 控制台默认 GBK，中文日志会变成乱码。强制 UTF-8 输出。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except Exception:  # noqa: BLE001 - 非交互环境可能不支持
        pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("tongxin")

API_PREFIX = "/api/v1"

# 统一的中文错误文案
INTERNAL_ERROR_MESSAGE = "服务暂时不可用，请稍后重试。"
VALIDATION_ERROR_MESSAGE = "请求参数不正确，请检查后重试。"
NOT_FOUND_MESSAGE = "请求的内容不存在。"
DATABASE_ERROR_MESSAGE = (
    "数据库暂时不可用，请确认已执行 docker compose up -d，然后稍后重试。"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时探测依赖并补齐补充字段。探测失败只告警，不阻断启动。"""
    logger.info("《同心千年》后端启动中……")

    if pg_db.ping():
        logger.info("PostgreSQL 连接正常")
        pg_db.apply_alters()
    else:
        logger.warning("PostgreSQL 暂时不可用，接口将返回空结果")

    if neo4j_db.ping():
        logger.info("Neo4j 连接正常")
    else:
        logger.warning("Neo4j 暂时不可用，图谱接口将回退到 PostgreSQL 或返回空结果")

    if settings.demo_mode:
        logger.warning(
            "未配置 LLM_API_KEY，已进入演示保障模式：回答来自已审核的预设问答库，"
            "界面会明确标注，不会伪装成实时 AI。"
        )
    else:
        logger.info("LLM 已配置：%s / %s", settings.llm_provider, settings.llm_model)

    if not settings.embedding_configured:
        logger.info("未配置 Embedding，检索使用本地中文检索（字符 bigram + 关键词加权）")

    yield

    neo4j_db.close_driver()
    logger.info("《同心千年》后端已停止")


app = FastAPI(
    title="《同心千年》后端 API",
    description="六章文化叙事与 AI 问答服务。所有内容均要求 Claim 级溯源。",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list or ["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # 前端需要读到的自定义头
    expose_headers=["X-Exploration-Session"],
)


# ---------- 全局异常处理（一律中文） ----------


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """HTTP 异常：detail 已是中文的直接透传，否则给通用文案。"""
    detail = exc.detail
    if not isinstance(detail, str) or not detail.strip():
        detail = NOT_FOUND_MESSAGE if exc.status_code == 404 else INTERNAL_ERROR_MESSAGE

    # 兜底：万一 detail 里混入英文堆栈特征，替换成通用文案
    if any(marker in detail for marker in ("Traceback", "sqlalchemy", "psycopg", "neo4j.")):
        logger.warning("异常 detail 含技术细节，已替换：%s", detail[:200])
        detail = INTERNAL_ERROR_MESSAGE

    return JSONResponse(status_code=exc.status_code, content={"detail": detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """参数校验失败：不回传英文的 pydantic 错误结构，只给中文提示。"""
    logger.info("请求参数校验失败：%s", exc.errors()[:3])
    return JSONResponse(status_code=422, content={"detail": VALIDATION_ERROR_MESSAGE})


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """数据库异常：返回 503 + 中文提示，不把英文堆栈抛给用户。

    列表类接口另有 `degrade_to` 装饰器兜底（直接返回空结果），
    这里是最后一道防线，覆盖详情类与写接口。
    """
    logger.warning("数据库操作失败 %s：%s", request.url.path, str(exc)[:200])
    return JSONResponse(status_code=503, content={"detail": DATABASE_ERROR_MESSAGE})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """未捕获异常：记录完整堆栈到服务端日志，只把中文提示返回给用户。"""
    logger.exception("未处理的异常：%s", exc)
    return JSONResponse(status_code=500, content={"detail": INTERNAL_ERROR_MESSAGE})


# ---------- 路由 ----------
app.include_router(api_router, prefix=API_PREFIX)


@app.get("/", include_in_schema=False)
def root() -> dict:
    """根路径给个可读的提示，方便现场排查。"""
    return {
        "name": "《同心千年》后端 API",
        "api_prefix": API_PREFIX,
        "health": f"{API_PREFIX}/health",
        "docs": "/docs",
        "demo_mode": settings.demo_mode,
    }
