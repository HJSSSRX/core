from collections.abc import Callable, Coroutine

from forhacker.bus.message_bus import MessageBus


class InProcessBus(MessageBus):
    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = {}

    async def publish(self, topic: str, message: dict) -> None:
        for handler in self._subscribers.get(topic, []):
            await handler(message)

    async def subscribe(self, topic: str, handler: Callable[[dict], Coroutine]) -> None:
        self._subscribers.setdefault(topic, []).append(handler)

    async def request(self, target: str, payload: dict) -> dict:
        handlers = self._subscribers.get(target, [])
        if not handlers:
            raise ValueError(f"No handler for target: {target}")
        return await handlers[0](payload)
