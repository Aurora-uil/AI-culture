"""健康检查出参模型。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class LlmStatusOut(BaseModel):
    """LLM 状态。未配置 Key 时 demo_mode=true，界面需显示「演示保障模式」。"""

    configured: bool = False
    provider: str = "openai_compatible"
    model: str | None = None
    demo_mode: bool = True


class EmbeddingStatusOut(BaseModel):
    """向量服务状态。未配置时检索自动走纯 Python 中文检索。"""

    provider: str = "none"
    configured: bool = False


class HealthOut(BaseModel):
    """对应前端 `HealthStatus`。"""

    status: str = "ok"  # ok | degraded
    postgres: bool = False
    neo4j: bool = False
    llm: LlmStatusOut = Field(default_factory=LlmStatusOut)
    embedding: EmbeddingStatusOut = Field(default_factory=EmbeddingStatusOut)
    counts: dict[str, int] = Field(default_factory=dict)
