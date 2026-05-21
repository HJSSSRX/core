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
