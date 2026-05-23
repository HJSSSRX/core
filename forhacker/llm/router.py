from __future__ import annotations

from typing import Any, Literal

from forhacker.llm.backend import LLMBackend, LLMResponse, Message

Sensitivity = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class SensitivityRouter:
    """Routes LLM requests to the appropriate backend based on sensitivity level.

    Default policy: LOW→local (Ollama), MEDIUM→DeepSeek, HIGH/CRITICAL→strongest cloud.
    Supports offline mode where everything routes to the local backend.
    """

    def __init__(self) -> None:
        self._backends: dict[Sensitivity, LLMBackend] = {}
        self.offline: bool = False

    def register(self, level: Sensitivity, backend: LLMBackend) -> None:
        self._backends[level] = backend

    def resolve(self, sensitivity: Sensitivity) -> LLMBackend:
        if self.offline:
            local = self._backends.get("LOW")
            if local is not None:
                return local
        backend = self._backends.get(sensitivity)
        if backend is not None:
            return backend
        # Fallback chain: try lower sensitivity levels
        for fallback in ("MEDIUM", "LOW"):
            fb = self._backends.get(fallback)  # type: ignore[arg-type]
            if fb is not None:
                return fb
        raise RuntimeError(f"No backend registered for sensitivity={sensitivity}")

    async def complete(
        self,
        messages: list[Message],
        sensitivity: Sensitivity = "MEDIUM",
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        backend = self.resolve(sensitivity)
        return await backend.complete(messages, tools=tools, **kwargs)
