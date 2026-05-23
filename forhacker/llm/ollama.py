from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from openai import AsyncOpenAI

from forhacker.llm.backend import LLMBackend, LLMResponse, Message


class OllamaBackend(LLMBackend):
    """Ollama via its OpenAI-compatible API."""

    def __init__(self, model: str, base_url: str = "http://localhost:11434/v1", timeout: float = 300.0):
        self._model = model
        self._client = AsyncOpenAI(api_key="ollama", base_url=base_url, timeout=timeout)

    @property
    def model_name(self) -> str:
        return self._model

    async def complete(
        self, messages: list[Message], tools: list[dict[str, Any]] | None = None, **kwargs: Any
    ) -> LLMResponse:
        fmt = [{"role": m.role, "content": m.content} for m in messages]
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=fmt,  # type: ignore[arg-type]
            tools=tools or None,  # type: ignore[arg-type]
            **kwargs,  # type: ignore[arg-type]
        )
        choice = response.choices[0]
        return LLMResponse(
            text=choice.message.content or "",
            model=response.model,
            tokens_used=response.usage.total_tokens if response.usage else 0,
            finish_reason=choice.finish_reason or "stop",
        )

    async def stream(  # type: ignore[override]
        self, messages: list[Message], tools: list[dict[str, Any]] | None = None, **kwargs: Any
    ) -> AsyncIterator[str]:
        fmt = [{"role": m.role, "content": m.content} for m in messages]
        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=fmt,  # type: ignore[arg-type]
            tools=tools or None,  # type: ignore[arg-type]
            stream=True,
            **kwargs,  # type: ignore[arg-type]
        )
        async for chunk in stream:  # type: ignore[union-attr]
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
