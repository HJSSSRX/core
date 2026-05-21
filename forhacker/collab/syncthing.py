import os
from pathlib import Path


def check_conflicts(shared_dir: Path) -> list[Path]:
    """Scan for Syncthing conflict files. Returns list of conflict paths."""
    conflicts = []
    for root, _, files in os.walk(shared_dir):
        for f in files:
            if ".sync-conflict-" in f:
                conflicts.append(Path(root) / f)
    return conflicts


def resolve_conflict(conflict_path: Path, operator: str) -> None:
    """Rename conflict file to .resolved-by-<operator> to mark resolution."""
    stem = conflict_path.name.split(".sync-conflict-")[0]
    suffix = conflict_path.suffix
    resolved = conflict_path.with_name(f"{stem}.resolved-by-{operator}{suffix}")
    conflict_path.rename(resolved)


class SyncthingHealth:
    """Check Syncthing health via its REST API (default: http://localhost:8384)."""

    def __init__(self, api_url: str = "http://localhost:8384"):
        self._api_url = api_url

    async def check(self) -> dict:
        """Query Syncthing REST API for connection and sync status."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self._api_url}/rest/system/status")
                data = resp.json()
                return {
                    "status": "ok",
                    "api_accessible": True,
                    "connected_devices": data.get("connections", {}).get("total", 0),
                    "pending_items": data.get("folderSummary", {}).get("needTotalItems", 0),
                }
        except Exception:
            return {
                "status": "offline",
                "api_accessible": False,
                "connected_devices": 0,
                "pending_items": 0,
            }
