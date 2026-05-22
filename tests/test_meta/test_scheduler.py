import asyncio

from forhacker.meta.scheduler import MetaScheduler


def test_scheduler_scan_once(tmp_path):
    kb = tmp_path / "kb"
    kb.mkdir()
    proposals = tmp_path / "proposals"

    scheduler = MetaScheduler(kb_dir=kb, proposals_dir=proposals)
    result = asyncio.run(scheduler.scan_once())

    assert "sources_checked" in result
    assert "candidates" in result
    assert "passed" in result
    assert isinstance(result["sources_checked"], int)


def test_scheduler_list_empty_proposals(tmp_path):
    scheduler = MetaScheduler(kb_dir=tmp_path / "kb", proposals_dir=tmp_path / "proposals")
    assert scheduler.list_pending_proposals() == []


def test_scheduler_add_source(tmp_path):
    scheduler = MetaScheduler(kb_dir=tmp_path / "kb", proposals_dir=tmp_path / "proposals")
    initial_count = len(scheduler._agent.sources)
    scheduler.add_source(name="test", url="https://example.com", category="test")
    assert len(scheduler._agent.sources) == initial_count + 1


def test_scheduler_scan_with_custom_source(tmp_path):
    scheduler = MetaScheduler(kb_dir=tmp_path / "kb", proposals_dir=tmp_path / "proposals")
    scheduler.add_source(
        name="test-source", url="http://localhost:1/test", category="test"
    )
    result = asyncio.run(scheduler.scan_once())
    assert result["sources_checked"] >= 1


def test_snapshot_create_and_restore(tmp_path):
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    (kb_dir / "test.md").write_text("original content")
    proposals_dir = tmp_path / "proposals"

    scheduler = MetaScheduler(kb_dir=kb_dir, proposals_dir=proposals_dir)

    # Create snapshot
    snap_dir = scheduler.create_snapshot("change-001", target_dirs=[kb_dir])
    assert snap_dir.exists()
    assert (snap_dir / "kb" / "test.md").exists()

    # Modify the original
    (kb_dir / "test.md").write_text("modified content")
    assert (kb_dir / "test.md").read_text() == "modified content"

    # Restore from snapshot
    result = scheduler.restore_snapshot("change-001")
    assert result["status"] == "ok"
    assert "kb" in result["restored"]
    assert (kb_dir / "test.md").read_text() == "original content"


def test_snapshot_list(tmp_path):
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    proposals_dir = tmp_path / "proposals"

    scheduler = MetaScheduler(kb_dir=kb_dir, proposals_dir=proposals_dir)
    scheduler.create_snapshot("change-001", target_dirs=[kb_dir])

    snapshots = scheduler.list_snapshots()
    assert len(snapshots) == 1
    assert snapshots[0]["change_id"] == "change-001"


def test_restore_nonexistent_snapshot(tmp_path):
    scheduler = MetaScheduler(kb_dir=tmp_path / "kb", proposals_dir=tmp_path / "proposals")
    result = scheduler.restore_snapshot("nonexistent")
    assert result["status"] == "error"


def test_list_empty_snapshots(tmp_path):
    scheduler = MetaScheduler(kb_dir=tmp_path / "kb", proposals_dir=tmp_path / "proposals")
    assert scheduler.list_snapshots() == []
