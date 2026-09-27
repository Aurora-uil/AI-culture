"""Anthropic Claude Provider。

调用 `/v1/messages`。system 消息单独放在顶层 `system` 字段，
其余消息按 user / assistant 交替传入。
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.ai.llm.base import LlmTimeoutError, LlmUnavailableError
from app.config import settings

logger = logging.getLogger(__name__)

ANTHROPIC_VERSION = "2023-06-01"


class AnthropicProvider:
    """Claude 接口。"""

    name = "anthropic"

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self.base_url = (base_url or settings.llm_base_url or "https://api.anthropic.com").rstrip("/")
        self.api_key = api_key or settings.llm_api_key
        self.model = model or settings.llm_model
        self.timeout = float(timeout or settings.llm_timeout_seconds)

    @property
    def _endpoint(self) -> str:
        if self.base_url.endswith("/messages"):
            return self.base_url
        if self.base_url.endswith("/v1"):
            return f"{self.base_url}/messages"
        return f"{self.base_url}/v1/messages"

    def _headers(self) -> dict[str, str]:
        return {
            "x-api-key": self.api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "Content-Type": "application/json",
        }

    @staticmethod
    def _split_messages(messages: list[dict]) -> tuple[str, list[dict]]:
        """抽出 system 提示，其余保持顺序。"""
        system_parts: list[str] = []
        rest: list[dict] = []
        for message in messages or []:
            role = message.get("role")
            content = message.get("content") or ""
            if role == "system":
                system_parts.append(content)
            else:
                rest.append({"role": role or "user", "content": content})
        if not rest:
            rest = [{"role": "user", "content": "请开始。"}]
        return "\n\n".join(system_parts), rest

    def _payload(self, messages: list[dict], stream: bool, **kw: Any) -> dict:
        system, rest = self._split_messages(messages)
        payload: dict[str, Any] = {
            "model": kw.get("model") or self.model,
            "max_tokens": int(kw.get("max_tokens") or settings.llm_max_tokens),
            "messages": rest,
            "stream": stream,
        }
        if system:
            payload["system"] = system
        temperature = kw.get("temperature")
        if temperature is not None:
            payload["temperature"] = temperature
        return payload

    def _wrap_error(self, exc: Exception) -> Exception:
        if isinstance(exc, httpx.TimeoutException):
            return LlmTimeoutError("AI 讲述暂时没有完成（模型响应超时）。")
        return LlmUnavailableError("AI 服务暂时不可用，已切换到演示保障模式。")

    async def complete(self, messages: list[dict], **kw: Any) -> str:
        payload = self._payload(messages, stream=False, **kw)
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self._endpoint, headers=self._headers(), json=payload
                )
                if response.status_code >= 400:
                    logger.warning(
                        "Claude 返回错误状态 %s：%s", response.status_code, response.text[:300]
                    )
                    raise LlmUnavailableError("AI 服务返回异常，已切换到演示保障模式。")
                data = response.json()
        except httpx.HTTPError as exc:
            raise self._wrap_error(exc) from exc

        try:
            blocks = data.get("content") or []
            return "".join(block.get("text", "") for block in blocks if block.get("type") == "text")
        except (AttributeError, TypeError) as exc:
            logger.warning("无法解析 Claude 响应：%s", str(data)[:300])
            raise LlmUnavailableError("AI 返回内容无法解析，已切换到演示保障模式。") from exc

    async def stream(self, messages: list[dict], **kw: Any) -> AsyncIterator[str]:
        payload = self._payload(messages, stream=True, **kw)
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST", self._endpoint, headers=self._headers(), json=payload
                ) as response:
                    if response.status_code >= 400:
                        body = await response.aread()
                        logger.warning(
                            "Claude 流式返回错误状态 %s：%s", response.status_code, body[:300]
                        )
                        raise LlmUnavailableError("AI 服务返回异常，已切换到演示保障模式。")

                    async for line in response.aiter_lines():
                        if not line or not line.startswith("data:"):
                            continue
                        data = line[5:].strip()
                        if not data:
                            continue
                        try:
                            parsed = json.loads(data)
                        except json.JSONDecodeError:
                            continue
                        if parsed.get("type") == "content_block_delta":
                            text = (parsed.get("delta") or {}).get("text")
                            if text:
                                yield text
        except httpx.HTTPError as exc:
            raise self._wrap_error(exc) from exc
