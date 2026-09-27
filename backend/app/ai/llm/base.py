"""LLM Provider 协议。

所有 Provider 都实现：

    async def complete(messages, **kw) -> str
    async def stream(messages, **kw) -> AsyncIterator[str]

`messages` 为 OpenAI 风格：[{"role": "system"|"user"|"assistant", "content": "..."}]
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


class LlmError(Exception):
    """LLM 调用异常基类。异常信息一律为中文，绝不把英文堆栈抛给用户。"""


class LlmTimeoutError(LlmError):
    """调用超时。上层据此把 status 标为 MODEL_TIMEOUT 并降级。"""


class LlmUnavailableError(LlmError):
    """网络错误 / 鉴权失败 / 服务不可用。上层据此降级到兜底问答库。"""


@dataclass
class LlmResponse:
    """一次完整调用的结果。"""

    text: str = ""
    model: str = ""
    finish_reason: str | None = None
    usage: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class LlmProvider(Protocol):
    """Provider 协议。"""

    name: str
    model: str

    async def complete(self, messages: list[dict], **kw: Any) -> str:
        """一次性返回完整文本。"""
        ...

    def stream(self, messages: list[dict], **kw: Any) -> AsyncIterator[str]:
        """流式返回增量文本。"""
        ...


def message_content(messages: list[dict]) -> str:
    """拼接全部消息文本，供 mock / 启发式逻辑使用。"""
    parts = []
    for message in messages or []:
        content = message.get("content")
        if isinstance(content, str):
            parts.append(content)
    return "\n".join(parts)


def last_user_message(messages: list[dict]) -> str:
    """取最后一条 user 消息。"""
    for message in reversed(messages or []):
        if message.get("role") == "user":
            content = message.get("content")
            if isinstance(content, str):
                return content
    return ""
