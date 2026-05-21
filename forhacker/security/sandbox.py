from abc import ABC, abstractmethod


class Sandbox(ABC):
    @abstractmethod
    async def run(self, command: list[str], read_only_mounts: list[str] | None = None) -> dict:
        """Returns {'exit_code': int, 'stdout': str, 'stderr': str}"""
        ...
