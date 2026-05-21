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


def resolve_conflict(conflict_path: Path, operator: str):
    """Rename conflict file to .resolved-by-<operator> to mark resolution."""
    stem = conflict_path.name.split(".sync-conflict-")[0]
    suffix = conflict_path.suffix
    resolved = conflict_path.with_name(f"{stem}.resolved-by-{operator}{suffix}")
    conflict_path.rename(resolved)
