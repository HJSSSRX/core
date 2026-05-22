from forhacker.llm.backend import LLMBackend, LLMResponse
from forhacker.llm.router import SensitivityRouter


class _MockBackend(LLMBackend):
    def __init__(self, name: str = "mock"):
        self._name = name
        self.calls: list = []

    async def complete(self, messages, tools=None, **kwargs):
        self.calls.append({"messages": messages, "tools": tools, "kwargs": kwargs})
        return LLMResponse(text="ok", model=self._name, tokens_used=1, finish_reason="stop")

    @property
    def model_name(self) -> str:
        return self._name


def test_router_resolve_exact_match():
    router = SensitivityRouter()
    low = _MockBackend("low")
    med = _MockBackend("med")
    router.register("LOW", low)
    router.register("MEDIUM", med)
    assert router.resolve("LOW") is low
    assert router.resolve("MEDIUM") is med


def test_router_fallback_chain():
    router = SensitivityRouter()
    low = _MockBackend("low")
    router.register("LOW", low)
    # MEDIUM not registered → falls back to LOW
    assert router.resolve("MEDIUM") is low
    # HIGH not registered → falls back MEDIUM → LOW
    assert router.resolve("HIGH") is low


def test_router_offline_mode():
    router = SensitivityRouter()
    low = _MockBackend("low")
    high = _MockBackend("high")
    router.register("LOW", low)
    router.register("HIGH", high)
    router.offline = True
    # Even HIGH should route to LOW when offline
    assert router.resolve("HIGH") is low
    assert router.resolve("MEDIUM") is low


def test_router_offline_without_local_raises():
    router = SensitivityRouter()
    high = _MockBackend("high")
    router.register("HIGH", high)
    router.offline = True
    # No LOW backend registered, should raise
    try:
        router.resolve("MEDIUM")
        assert False, "Should have raised RuntimeError"
    except RuntimeError:
        pass


def test_router_no_backend_raises():
    router = SensitivityRouter()
    try:
        router.resolve("MEDIUM")
        assert False, "Should have raised RuntimeError"
    except RuntimeError:
        pass


def test_router_complete_routes():
    import asyncio
    router = SensitivityRouter()
    low = _MockBackend("low")
    router.register("LOW", low)

    async def _test():
        from forhacker.llm.backend import Message
        resp = await router.complete(
            [Message(role="user", content="hi")], sensitivity="LOW"
        )
        assert resp.model == "low"
        assert len(low.calls) == 1

    asyncio.run(_test())
