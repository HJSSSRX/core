import pytest

from forhacker.llm.anthropic import AnthropicBackend
from forhacker.llm.backend import Message


def test_anthropic_backend_model_name():
    backend = AnthropicBackend(model="claude-sonnet-4-6", api_key="test-key")
    assert backend.model_name == "claude-sonnet-4-6"


def test_anthropic_detects_tool_role_messages():
    """Anthropic API rejects role='tool'; backend must detect and raise NotImplementedError."""
    backend = AnthropicBackend(model="claude-sonnet-4-6", api_key="test-key")
    msgs = [
        Message(role="user", content="run analysis"),
        Message(role="assistant", content=""),
        Message(role="tool", content="result: 123"),
    ]
    with pytest.raises(NotImplementedError, match="tool-calling"):
        backend._convert_messages(msgs)


def test_anthropic_extracts_tool_use_blocks():
    """Verify _extract_tool_calls maps Anthropic tool_use blocks to standard format."""
    # Use dicts to mock Anthropic content blocks (avoid import dependency)
    mock_block = type("MockBlock", (), {
        "type": "tool_use",
        "id": "tool_123",
        "name": "search",
        "input": {"query": "test"},
    })
    result = AnthropicBackend._extract_tool_calls([mock_block])
    assert len(result) == 1
    assert result[0]["name"] == "search"
    assert result[0]["arguments"] == {"query": "test"}
