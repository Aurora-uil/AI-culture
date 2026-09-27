"""v1 路由汇总。所有接口统一挂在 /api/v1 前缀下。"""

from fastapi import APIRouter

from app.api.v1 import chapters, chat, cocreation, entities, exploration, graph, health, scenes

api_router = APIRouter()

api_router.include_router(health.router, tags=["系统"])
api_router.include_router(chapters.router, tags=["章节与内容"])
api_router.include_router(entities.router, tags=["实体"])
api_router.include_router(scenes.router, tags=["场景与地图"])
api_router.include_router(graph.router, tags=["图谱"])
api_router.include_router(chat.router, tags=["AI 对话"])
api_router.include_router(exploration.router, tags=["探索"])
api_router.include_router(cocreation.router, tags=["AI 共创"])

__all__ = ["api_router"]
