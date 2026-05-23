from __future__ import annotations

import pytest

from forhacker.llm.backend import Message
from forhacker.llm.openai import OpenAIBackend


@pytest.mark.asyncio
async def test_openai_backend_model_name():
    backend = OpenAIBackend(model="gpt-4o-mini", api_key="test-key")
    assert backend.model_name == "gpt-4o-mini"


@pytest.mark.asyncio
async def test_openai_backend_converts_messages():
    backend = OpenAIBackend(model="gpt-4o-mini", api_key="test-key")
    messages = [Message(role="user", content="hello")]
    converted = backend._messages_to_openai_format(messages)
    assert converted == [{"role": "user", "content": "hello"}]
