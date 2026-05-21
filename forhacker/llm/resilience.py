import asyncio
import random
import time
from typing import Any

from forhacker.llm.backend import LLMBackend, LLMResponse, Message


class ResilienceWrapper:
    """Wraps LLMBackend.complete() with timeout, retry, and circuit breaker."""

    def __init__(self, max_retries: int = 3, timeout: float = 120.0,
                 circuit_threshold: int = 5, circuit_cooldown: float = 60.0):
        self._max_retries = max_retries
        self._timeout = timeout
        self._circuit_threshold = circuit_threshold
        self._circuit_cooldown = circuit_cooldown
        self._consecutive_failures = 0
        self._circuit_open_until: float = 0.0

    async def complete(self, backend: LLMBackend, messages: list[Message],
                       tools: list[dict[str, Any]] | None = None, **kwargs) -> LLMResponse:
        if time.monotonic() < self._circuit_open_until:
            raise RuntimeError("Circuit breaker open — too many failures")
        last_exc = None
        for attempt in range(self._max_retries):
            try:
                resp = await asyncio.wait_for(
                    backend.complete(messages, tools=tools, **kwargs),
                    timeout=self._timeout,
                )
                self._consecutive_failures = 0
                return resp
            except asyncio.TimeoutError:
                last_exc = TimeoutError(f"LLM call timed out ({self._timeout}s)")
            except Exception as e:
                last_exc = e
                if hasattr(e, "status_code") and 400 <= e.status_code < 500 and e.status_code != 429:
                    raise  # auth errors propagate immediately
            if attempt < self._max_retries - 1:
                delay = (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(delay)
        self._consecutive_failures += 1
        if self._consecutive_failures >= self._circuit_threshold:
            self._circuit_open_until = time.monotonic() + self._circuit_cooldown
        raise last_exc  # type: ignore[misc]
