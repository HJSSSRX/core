from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Coroutine


class MessageBus(ABC):
    @abstractmethod
    async def publish(self, topic: str, message: dict) -> None: ...

    @abstractmethod
    async def subscribe(self, topic: str, handler: Callable[[dict], Coroutine]) -> None: ...

    @abstractmethod
    async def request(self, target: str, payload: dict) -> dict: ...
