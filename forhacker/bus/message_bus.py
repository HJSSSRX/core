from abc import ABC, abstractmethod
from collections.abc import Callable, Coroutine
from typing import Any


class MessageBus(ABC):
    @abstractmethod
    async def publish(self, topic: str, message: dict) -> None:
        ...

    @abstractmethod
    async def subscribe(self, topic: str, handler: Callable[[dict], Coroutine]) -> None:
        ...

    @abstractmethod
    async def request(self, target: str, payload: dict) -> dict:
        ...
