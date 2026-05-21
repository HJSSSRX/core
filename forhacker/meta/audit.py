import datetime
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AuditTrail:
    _entries: list[dict[str, Any]] = field(default_factory=list)
    _snapshots: list[str] = field(default_factory=list)

    def log(self, action: str, actor: str, target: str | None = None, details: dict | None = None):
        self._entries.append({
            "action": action,
            "actor": actor,
            "target": target,
            "details": details or {},
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        })

    def snapshot(self, name: str):
        self._snapshots.append(name)

    def latest_snapshot(self) -> str | None:
        return self._snapshots[-1] if self._snapshots else None

    def entries(self) -> list[dict[str, Any]]:
        return list(self._entries)
