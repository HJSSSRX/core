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
    def __init__(self):
        self._plugins: dict[str, PluginEntry] = {}

    def register(self, entry: PluginEntry):
        self._plugins[entry.name] = entry

    def list_all(self) -> list[dict[str, Any]]:
        return [self._to_dict(e) for e in self._plugins.values()]

    def query(self, domain: str) -> list[dict[str, Any]]:
        return [self._to_dict(e) for e in self._plugins.values() if e.domain == domain]

    def _to_dict(self, entry: PluginEntry) -> dict:
        return {
            "name": entry.name,
            "version": entry.version,
            "domain": entry.domain,
            "description": entry.description,
            "repo_url": entry.repo_url,
            "owner_cell": entry.owner_cell,
        }
