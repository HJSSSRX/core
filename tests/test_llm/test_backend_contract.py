"""GATE test: validate LLMBackend contract across all planned backends.

If this gate fails after 2 REFACTOR iterations, STOP. The LLMBackend
interface must be redesigned before proceeding to implementation tasks.
"""
from forhacker.llm.backend import LLMBackend, LLMResponse, Message


def test_message_dataclass_matches_openai_convention():
    """OpenAI API uses role + content dicts; Message must serialize cleanly."""
    msg = Message(role="user", content="hello")
    as_dict = {"role": msg.role, "content": msg.content}
    assert as_dict == {"role": "user", "content": "hello"}


def test_message_dataclass_matches_anthropic_convention():
    """Anthropic API separates system from chat messages; Message.role must support all needed roles."""
    valid_roles = {"system", "user", "assistant", "tool"}
    for role in valid_roles:
        msg = Message(role=role, content="test")
        assert msg.role == role


def test_llmresponse_carries_tool_calls():
    """Tool-calling is central to forensics workflows; LLMResponse must carry optional tool_calls."""
    resp = LLMResponse(
        text="",
        model="test",
        tokens_used=0,
        finish_reason="tool_calls",
        tool_calls=[{"name": "search", "arguments": {"q": "x"}}],
    )
    assert resp.tool_calls is not None
    assert resp.tool_calls[0]["name"] == "search"


def test_complete_signature_accepts_tools():
    """SubAgents pass tools per spec; the ABC signature must accept them."""
    import inspect
    sig = inspect.signature(LLMBackend.complete)
    params = list(sig.parameters.keys())
    assert "tools" in params
    assert "messages" in params
