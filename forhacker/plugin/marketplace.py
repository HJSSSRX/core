import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


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
        self._load_plugins_yaml()

    def _load_plugins_yaml(self) -> None:
        for search_path in (Path("plugins.yaml"), Path("forhacker-core/plugins.yaml")):
            if search_path.exists():
                try:
                    data = yaml.safe_load(search_path.read_text(encoding="utf-8"))
                    for entry in data.get("plugins", []):
                        self.register(PluginEntry(**entry))
                    logger.info("Loaded %d plugins from %s", len(self._plugins), search_path)
                    return
                except (yaml.YAMLError, TypeError) as e:
                    logger.warning("Failed to load %s: %s", search_path, e)

    def register(self, entry: PluginEntry) -> None:
        self._plugins[entry.name] = entry

    def get(self, name: str) -> PluginEntry | None:
        return self._plugins.get(name)

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
