from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Literal


@dataclass(slots=True)
class Message:
    role: Literal["system", "user", "assistant", "tool"]
    content: str


@dataclass(slots=True)
class LLMResponse:
    text: str
    model: str
    tokens_used: int
    finish_reason: str
    tool_calls: list[dict[str, Any]] | None = None


class LLMBackend(ABC):
    """Unified interface for all LLM providers."""

    @abstractmethod
    async def complete(self, messages: list[Message], tools: list[dict[str, Any]] | None = None, **kwargs: Any) -> LLMResponse:
        ...

    async def stream(self, messages: list[Message], tools: list[dict[str, Any]] | None = None, **kwargs: Any) -> AsyncIterator[str]:
        """Stream tokens as they are generated. Not all backends support streaming."""
        raise NotImplementedError(f"{self.__class__.__name__} does not support streaming")

    @property
    @abstractmethod
    def model_name(self) -> str:
        ...
