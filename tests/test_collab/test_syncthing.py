from __future__ import annotations

from forhacker.collab.syncthing import check_conflicts, resolve_conflict


def test_check_conflicts_no_conflicts(tmp_shared_dir):
    conflicts = check_conflicts(tmp_shared_dir)
    assert conflicts == []


def test_check_conflicts_detects_sync_conflict(tmp_shared_dir):
    (tmp_shared_dir / "progress.sync-conflict-20260521-120000.yaml").write_text("")
    conflicts = check_conflicts(tmp_shared_dir)
    assert len(conflicts) == 1
    assert "progress" in conflicts[0].name


def test_resolve_conflict_renames_loser(tmp_shared_dir):
    conflict = tmp_shared_dir / "test.sync-conflict-20260521.yaml"
    conflict.write_text("conflicting content")
    resolve_conflict(conflict, operator="lead")
    assert not conflict.exists()
    resolved = tmp_shared_dir / "test.resolved-by-lead.yaml"
    assert resolved.exists()
