"""OpenAI 兼容 Provider（DeepSeek / 通义千问 / 豆包 / Kimi / 智谱）。

用 httpx 直接调 `/chat/completions`，不引入各家 SDK，避免依赖膨胀。
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


class OpenAICompatProvider:
    """OpenAI 兼容接口。"""

    name = "openai_compatible"

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self.base_url = (base_url or settings.llm_base_url or "").rstrip("/")
        self.api_key = api_key or settings.llm_api_key
        self.model = model or settings.llm_model
        self.timeout = float(timeout or settings.llm_timeout_seconds)

    # ---------- 内部 ----------

    @property
    def _endpoint(self) -> str:
        # 兼容用户把 base_url 写成 https://api.deepseek.com（不带 /v1）
        if self.base_url.endswith("/chat/completions"):
            return self.base_url
        return f"{self.base_url}/chat/completions"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _payload(self, messages: list[dict], stream: bool, **kw: Any) -> dict:
        payload: dict[str, Any] = {
            "model": kw.get("model") or self.model,
            "messages": messages,
            "stream": stream,
            "max_tokens": int(kw.get("max_tokens") or settings.llm_max_tokens),
        }
        temperature = kw.get("temperature")
        if temperature is not None:
            payload["temperature"] = temperature
        if kw.get("json_mode"):
            payload["response_format"] = {"type": "json_object"}
        return payload

    def _wrap_error(self, exc: Exception) -> Exception:
        if isinstance(exc, httpx.TimeoutException):
            return LlmTimeoutError("AI 讲述暂时没有完成（模型响应超时）。")
        return LlmUnavailableError("AI 服务暂时不可用，已切换到演示保障模式。")

    # ---------- 接口 ----------

    async def complete(self, messages: list[dict], **kw: Any) -> str:
        payload = self._payload(messages, stream=False, **kw)
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self._endpoint, headers=self._headers(), json=payload
                )
                if response.status_code >= 400:
                    logger.warning(
                        "LLM 返回错误状态 %s：%s", response.status_code, response.text[:300]
                    )
                    raise LlmUnavailableError("AI 服务返回异常，已切换到演示保障模式。")
                data = response.json()
        except httpx.HTTPError as exc:
            raise self._wrap_error(exc) from exc

        try:
            return data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as exc:
            logger.warning("无法解析 LLM 响应：%s", str(data)[:300])
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
                            "LLM 流式返回错误状态 %s：%s", response.status_code, body[:300]
                        )
                        raise LlmUnavailableError("AI 服务返回异常，已切换到演示保障模式。")

                    async for line in response.aiter_lines():
                        if not line or not line.startswith("data:"):
                            continue
                        data = line[5:].strip()
                        if data == "[DONE]":
                            break
                        try:
                            parsed = json.loads(data)
                        except json.JSONDecodeError:
                            continue
                        choices = parsed.get("choices") or []
                        if not choices:
                            continue
                        delta = choices[0].get("delta") or {}
                        text = delta.get("content")
                        if text:
                            yield text
        except httpx.HTTPError as exc:
            raise self._wrap_error(exc) from exc
