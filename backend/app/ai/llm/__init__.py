"""LLM Provider 工厂。

按 settings.llm_provider 选择实现：
- openai_compatible → DeepSeek / 通义千问 / 豆包 / Kimi / 智谱
- anthropic         → Claude
- mock              → 强制走兜底问答库（调试用）

未配置 Key 时一律返回 MockProvider，保证系统进入「演示保障模式」而不是报错。
"""

from __future__ import annotations

from functools import lru_cache

from app.ai.llm.anthropic import AnthropicProvider
from app.ai.llm.base import LlmProvider, LlmResponse, LlmTimeoutError, LlmUnavailableError
from app.ai.llm.mock import MockProvider
from app.ai.llm.openai_compat import OpenAICompatProvider
from app.config import settings

__all__ = [
    "LlmProvider",
    "LlmResponse",
    "LlmTimeoutError",
    "LlmUnavailableError",
    "OpenAICompatProvider",
    "AnthropicProvider",
    "MockProvider",
    "get_provider",
]


@lru_cache(maxsize=1)
def get_provider() -> LlmProvider:
    """当前生效的 Provider 单例。

    没配 Key → MockProvider（兜底问答库）。这是「演示保障模式」的实现方式。
    """
    if not settings.llm_configured:
        return MockProvider()

    if settings.llm_provider == "anthropic":
        return AnthropicProvider()

    return OpenAICompatProvider()


def reset_provider() -> None:
    """清空缓存（测试或改配置后调用）。"""
    get_provider.cache_clear()
