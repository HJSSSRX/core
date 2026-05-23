import asyncio

import pytest

from forhacker.llm.backend import LLMBackend, LLMResponse, Message
from forhacker.llm.resilience import ResilienceWrapper


class FakeBackend(LLMBackend):
    """Mock LLM backend for resilience testing."""

    def __init__(self, responses=None, model="fake"):
        self._responses = responses or []
        self._call_count = 0
        self._model = model

    async def complete(self, messages, tools=None, **kwargs):
        resp = self._responses[self._call_count]
        self._call_count += 1
        if isinstance(resp, Exception):
            raise resp
        return resp

    @property
    def model_name(self):
        return self._model


def _ok_response():
    return LLMResponse(text="ok", model="fake", tokens_used=10, finish_reason="stop")


def _msg():
    return [Message(role="user", content="hello")]


@pytest.mark.asyncio
async def test_complete_normal():
    backend = FakeBackend(responses=[_ok_response()])
    rw = ResilienceWrapper(max_retries=2, timeout=30.0)
    resp = await rw.complete(backend, _msg())
    assert resp.text == "ok"


@pytest.mark.asyncio
async def test_retry_on_timeout_then_succeed():
    backend = FakeBackend(responses=[TimeoutError(), _ok_response()])
    rw = ResilienceWrapper(max_retries=3, timeout=1.0)
    resp = await rw.complete(backend, _msg())
    assert resp.text == "ok"
    assert backend._call_count == 2


@pytest.mark.asyncio
async def test_all_retries_exhausted():
    backend = FakeBackend(responses=[TimeoutError()] * 4)
    rw = ResilienceWrapper(max_retries=3, timeout=0.1)
    with pytest.raises(TimeoutError):
        await rw.complete(backend, _msg())
    assert backend._call_count == 3


@pytest.mark.asyncio
async def test_auth_error_propagates_immediately():
    class AuthError(Exception):
        status_code = 401

    backend = FakeBackend(responses=[AuthError("unauthorized")])
    rw = ResilienceWrapper(max_retries=3)
    with pytest.raises(AuthError):
        await rw.complete(backend, _msg())
    assert backend._call_count == 1  # no retry


@pytest.mark.asyncio
async def test_rate_limit_429_retries():
    class RateLimitError(Exception):
        status_code = 429

    backend = FakeBackend(responses=[RateLimitError("too many"), _ok_response()])
    rw = ResilienceWrapper(max_retries=3)
    resp = await rw.complete(backend, _msg())
    assert resp.text == "ok"
    assert backend._call_count == 2


@pytest.mark.asyncio
async def test_server_error_retries():
    class ServerError(Exception):
        status_code = 500

    backend = FakeBackend(responses=[ServerError("boom"), _ok_response()])
    rw = ResilienceWrapper(max_retries=3)
    resp = await rw.complete(backend, _msg())
    assert resp.text == "ok"
    assert backend._call_count == 2


@pytest.mark.asyncio
async def test_circuit_breaker_open_immediate():
    rw = ResilienceWrapper(circuit_threshold=3, circuit_cooldown=60.0)
    rw._consecutive_failures = 5
    rw._circuit_open_until = 999999999.0  # far future
    backend = FakeBackend(responses=[_ok_response()])
    with pytest.raises(RuntimeError, match="Circuit breaker open"):
        await rw.complete(backend, _msg())


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_threshold():
    backend = FakeBackend(responses=[TimeoutError()] * 4)
    rw = ResilienceWrapper(max_retries=1, circuit_threshold=2, circuit_cooldown=60.0)
    # First call: retry exhausted, consecutive_failures goes to 1
    with pytest.raises(TimeoutError):
        await rw.complete(backend, _msg())
    assert rw._consecutive_failures == 1
    # Second call: retry exhausted, consecutive_failures goes to 2
    # circuit opens: _circuit_open_until set
    with pytest.raises(TimeoutError):
        await rw.complete(backend, _msg())
    assert rw._consecutive_failures >= rw._circuit_threshold
    assert rw._circuit_open_until > 0


@pytest.mark.asyncio
async def test_circuit_closed_after_cooldown():
    rw = ResilienceWrapper(circuit_threshold=1, circuit_cooldown=0.01)
    backend = FakeBackend(responses=[_ok_response()])
    # First, open the circuit
    fail_backend = FakeBackend(responses=[TimeoutError()] * 2)
    rw._max_retries = 1
    rw._circuit_threshold = 1
    with pytest.raises(TimeoutError):
        await rw.complete(fail_backend, _msg())
    assert rw._circuit_open_until > 0
    # Wait for cooldown
    await asyncio.sleep(0.02)
    # Should work now
    resp = await rw.complete(backend, _msg())
    assert resp.text == "ok"


@pytest.mark.asyncio
async def test_generic_exception_retry():
    backend = FakeBackend(responses=[ValueError("transient"), _ok_response()])
    rw = ResilienceWrapper(max_retries=3)
    resp = await rw.complete(backend, _msg())
    assert resp.text == "ok"
    assert backend._call_count == 2
