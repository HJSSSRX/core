from dataclasses import dataclass
from typing import Any


@dataclass
class PluginEntry:
    name: str
    version: str
    domain: str
    description: str
    repo_url: str
    owner_cell: str


class Marketplace:
    def __init__(self) -> None:
        self._plugins: dict[str, PluginEntry] = {}

    def register(self, entry: PluginEntry) -> None:
        self._plugins[entry.name] = entry

    def list_all(self) -> list[dict[str, Any]]:
        return [self._to_dict(e) for e in self._plugins.values()]

    def query(self, domain: str) -> list[dict[str, Any]]:
        return [self._to_dict(e) for e in self._plugins.values() if e.domain == domain]

    def _to_dict(self, entry: PluginEntry) -> dict[str, Any]:
        return {
            "name": entry.name,
            "version": entry.version,
            "domain": entry.domain,
            "description": entry.description,
            "repo_url": entry.repo_url,
            "owner_cell": entry.owner_cell,
        }

    def __bool__(self) -> bool:
        return bool(self._plugins)

    def __iter__(self):
        return iter(self.list_all())

    def __len__(self) -> int:
        return len(self._plugins)


MARKETPLACE = Marketplace()
