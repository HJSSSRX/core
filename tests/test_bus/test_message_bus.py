import asyncio

import pytest

from forhacker.bus.in_process import InProcessBus
from forhacker.bus.message_bus import MessageBus


def test_cannot_instantiate_message_bus_abc():
    with pytest.raises(TypeError):
        MessageBus()


@pytest.mark.asyncio
async def test_in_process_publish_subscribe():
    bus = InProcessBus()
    received = []

    async def handler(message):
        received.append(message)

    await bus.subscribe("test.topic", handler)
    await bus.publish("test.topic", {"key": "value"})
    await asyncio.sleep(0.05)
    assert len(received) == 1
    assert received[0] == {"key": "value"}


@pytest.mark.asyncio
async def test_in_process_request_response():
    bus = InProcessBus()

    async def handler(payload):
        return {"result": payload["x"] * 2}

    await bus.subscribe("compute", handler)
    result = await bus.request("compute", {"x": 21})
    assert result == {"result": 42}


@pytest.mark.asyncio
async def test_in_process_multiple_subscribers():
    bus = InProcessBus()
    results = []

    async def handler_a(msg):
        results.append(("a", msg))

    async def handler_b(msg):
        results.append(("b", msg))

    await bus.subscribe("multi", handler_a)
    await bus.subscribe("multi", handler_b)
    await bus.publish("multi", {"data": 1})
    await asyncio.sleep(0.05)
    assert len(results) == 2
