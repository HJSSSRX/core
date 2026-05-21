from collections.abc import AsyncIterator
from typing import Any

from openai import AsyncOpenAI

from forhacker.llm.backend import LLMBackend, LLMResponse, Message


class OpenAIBackend(LLMBackend):
    def __init__(self, model: str, api_key: str, base_url: str | None = None, timeout: float = 120.0):
        self._model = model
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=timeout)

    @property
    def model_name(self) -> str:
        return self._model

    def _messages_to_openai_format(self, messages: list[Message]) -> list[dict[str, Any]]:
        return [{"role": m.role, "content": m.content} for m in messages]

    async def complete(self, messages: list[Message], tools: list[dict[str, Any]] | None = None, **kwargs: Any) -> LLMResponse:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=self._messages_to_openai_format(messages),
            tools=tools or None,
            **kwargs,
        )
        choice = response.choices[0]
        return LLMResponse(
            text=choice.message.content or "",
            model=response.model,
            tokens_used=response.usage.total_tokens if response.usage else 0,
            finish_reason=choice.finish_reason or "stop",
            tool_calls=[tc.model_dump() for tc in choice.message.tool_calls] if choice.message.tool_calls else None,
        )

    async def stream(self, messages: list[Message], tools: list[dict[str, Any]] | None = None, **kwargs: Any) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=self._messages_to_openai_format(messages),
            tools=tools or None,
            stream=True,
            **kwargs,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
