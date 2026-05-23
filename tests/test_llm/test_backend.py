from __future__ import annotations

import pytest

from forhacker.llm.backend import LLMBackend, LLMResponse, Message


def test_cannot_instantiate_abc():
    """LLMBackend is abstract — cannot instantiate directly."""
    with pytest.raises(TypeError):
        LLMBackend()


def test_message_fields():
    msg = Message(role="user", content="test message")
    assert msg.role == "user"
    assert msg.content == "test message"


def test_llm_response_fields():
    resp = LLMResponse(text="hello", model="test-model", tokens_used=10, finish_reason="stop", tool_calls=None)
    assert resp.text == "hello"
    assert resp.model == "test-model"
    assert resp.tokens_used == 10
    assert resp.finish_reason == "stop"
    assert resp.tool_calls is None


def test_llm_response_with_tool_calls():
    resp = LLMResponse(
        text="",
        model="test-model",
        tokens_used=20,
        finish_reason="tool_calls",
        tool_calls=[{"name": "search", "arguments": {"query": "test"}}],
    )
    assert resp.tool_calls is not None
    assert len(resp.tool_calls) == 1


def test_concrete_backend_must_implement_complete():
    """Subclasses must implement abstract methods."""

    class IncompleteBackend(LLMBackend):
        pass

    with pytest.raises(TypeError):
        IncompleteBackend()
