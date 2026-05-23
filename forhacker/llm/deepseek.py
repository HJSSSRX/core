from __future__ import annotations

from forhacker.llm.openai import OpenAIBackend


class DeepSeekBackend(OpenAIBackend):
    """DeepSeek via OpenAI-compatible API (https://api.deepseek.com/v1)."""

    def __init__(self, model: str = "deepseek-chat", api_key: str = "", timeout: float = 300.0):
        super().__init__(
            model=model,
            api_key=api_key,
            base_url="https://api.deepseek.com/v1",
            timeout=timeout,
        )
