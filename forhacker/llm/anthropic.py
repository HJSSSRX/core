from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from anthropic import AsyncAnthropic

from forhacker.llm.backend import LLMBackend, LLMResponse, Message


class AnthropicBackend(LLMBackend):
    def __init__(self, model: str = "claude-sonnet-4-6", api_key: str = "", timeout: float = 120.0):
        self._model = model
        self._client = AsyncAnthropic(api_key=api_key, timeout=timeout)

    @property
    def model_name(self) -> str:
        return self._model

    def _convert_messages(self, messages: list[Message]) -> tuple[str | None, list[dict[str, Any]]]:
        """Convert forhacker Messages to Anthropic API format.

        Anthropic API only accepts 'user' and 'assistant' roles. Tool-result messages
        (role='tool') raise NotImplementedError since tool_use_id tracking is deferred.
        """
        system_parts = []
        converted = []
        for m in messages:
            if m.role == "system":
                system_parts.append(m.content)
            elif m.role == "tool":
                raise NotImplementedError(
                    "AnthropicBackend does not yet support tool-calling workflows. "
                    "Tool result messages require tool_use_id tracking which is deferred "
                    "to a future implementation phase."
                )
            else:
                converted.append({"role": m.role, "content": m.content})
        system = "\n".join(system_parts) if system_parts else None
        return system, converted

    @staticmethod
    def _extract_tool_calls(content_blocks: list[Any]) -> list[dict[str, Any]] | None:
        """Extract tool_use blocks from Anthropic response and map to standard format."""
        tool_calls = []
        for block in content_blocks:
            if hasattr(block, "type") and block.type == "tool_use":
                tool_calls.append(
                    {
                        "id": getattr(block, "id", ""),
                        "name": getattr(block, "name", ""),
                        "arguments": getattr(block, "input", {}),
                    }
                )
        return tool_calls if tool_calls else None

    async def complete(
        self, messages: list[Message], tools: list[dict[str, Any]] | None = None, **kwargs: Any
    ) -> LLMResponse:
        system, converted_msgs = self._convert_messages(messages)
        kwargs_anthropic: dict[str, Any] = {"max_tokens": kwargs.pop("max_tokens", 4096)}
        if system:
            kwargs_anthropic["system"] = system
        if tools:
            kwargs_anthropic["tools"] = tools

        response = await self._client.messages.create(
            model=self._model,
            messages=converted_msgs,  # type: ignore[arg-type]
            **kwargs_anthropic,
            **kwargs,
        )
        text = "".join(block.text for block in response.content if hasattr(block, "text") and block.type == "text")
        return LLMResponse(
            text=text,
            model=response.model,
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            finish_reason=response.stop_reason or "stop",
            tool_calls=self._extract_tool_calls(response.content),
        )

    async def stream(  # type: ignore[override]
        self, messages: list[Message], tools: list[dict[str, Any]] | None = None, **kwargs: Any
    ) -> AsyncIterator[str]:
        system, converted_msgs = self._convert_messages(messages)
        kwargs_anthropic: dict[str, Any] = {"max_tokens": kwargs.pop("max_tokens", 4096)}
        if system:
            kwargs_anthropic["system"] = system
        if tools:
            kwargs_anthropic["tools"] = tools

        async with self._client.messages.stream(
            model=self._model,
            messages=converted_msgs,  # type: ignore[arg-type]
            **kwargs_anthropic,
            **kwargs,
        ) as stream:
            async for event in stream:
                if event.type == "content_block_delta" and event.delta.type == "text_delta":
                    yield event.delta.text
