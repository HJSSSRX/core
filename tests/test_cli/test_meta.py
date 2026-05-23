"""Tests for meta CLI commands — scan, proposals, sources, review, watchdog, verify, rollback, snapshots."""

from pathlib import Path

import yaml
from click.testing import CliRunner

from forhacker.cli.main import cli


def test_meta_scan_no_sources():
    runner = CliRunner()
    result = runner.invoke(cli, ["meta", "scan"])
    assert result.exit_code == 0
    assert "Scanning sources" in result.output


def test_meta_scan_with_custom_source():
    runner = CliRunner()
    result = runner.invoke(cli, ["meta", "scan", "-s", "https://example.com/feed"])
    assert result.exit_code == 0
    assert "Scanning sources" in result.output


def test_meta_proposals_empty():
    runner = CliRunner()
    result = runner.invoke(cli, ["meta", "proposals"])
    assert result.exit_code == 0


def test_meta_proposals_with_data(tmp_path):
    proposals_dir = tmp_path / "shared" / "meta" / "proposals"
    proposals_dir.mkdir(parents=True)
    kb_dir = tmp_path / "shared" / "kb"
    kb_dir.mkdir(parents=True)

    proposal_data = {
        "title": "Test Proposal",
        "what": "Add caching layer to KB store",
        "why": "Reduce disk reads",
        "risk": "LOW",
        "relevance_score": 0.8,
    }
    (proposals_dir / "test_proposal.yaml").write_text(yaml.dump(proposal_data, allow_unicode=True), encoding="utf-8")

    import forhacker.cli.commands.meta as meta_mod

    old_proposals = meta_mod.PROPOSALS_DIR
    old_kb = meta_mod.KB_DIR
    try:
        meta_mod.PROPOSALS_DIR = proposals_dir
        meta_mod.KB_DIR = kb_dir
        runner = CliRunner()
        result = runner.invoke(cli, ["meta", "proposals"])
        assert result.exit_code == 0
        assert "Test Proposal" in result.output
    finally:
        meta_mod.PROPOSALS_DIR = old_proposals
        meta_mod.KB_DIR = old_kb


def test_meta_sources():
    runner = CliRunner()
    result = runner.invoke(cli, ["meta", "sources"])
    assert result.exit_code == 0


def test_meta_watchdog():
    runner = CliRunner()
    result = runner.invoke(cli, ["meta", "watchdog"])
    assert result.exit_code == 0
    assert "Watchdog OK" in result.output or "WARNING" in result.output


def test_meta_verify_no_dir():
    import forhacker.cli.commands.meta as meta_mod

    old_proposals = meta_mod.PROPOSALS_DIR
    old_kb = meta_mod.KB_DIR
    try:
        meta_mod.PROPOSALS_DIR = Path("/nonexistent_meta_proposals")
        meta_mod.KB_DIR = Path("/nonexistent_meta_kb")
        runner = CliRunner()
        result = runner.invoke(cli, ["meta", "verify"])
        assert result.exit_code == 0
        assert "No proposals" in result.output
    finally:
        meta_mod.PROPOSALS_DIR = old_proposals
        meta_mod.KB_DIR = old_kb


def test_meta_verify_empty(tmp_path):
    proposals_dir = tmp_path / "proposals"
    proposals_dir.mkdir(parents=True)
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir(parents=True)

    import forhacker.cli.commands.meta as meta_mod

    old_proposals = meta_mod.PROPOSALS_DIR
    old_kb = meta_mod.KB_DIR
    try:
        meta_mod.PROPOSALS_DIR = proposals_dir
        meta_mod.KB_DIR = kb_dir
        runner = CliRunner()
        result = runner.invoke(cli, ["meta", "verify"])
        assert result.exit_code == 0
        assert "No proposals to verify" in result.output
    finally:
        meta_mod.PROPOSALS_DIR = old_proposals
        meta_mod.KB_DIR = old_kb


def test_meta_verify_with_proposals(tmp_path):
    proposals_dir = tmp_path / "proposals"
    proposals_dir.mkdir(parents=True)
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir(parents=True)

    valid = proposals_dir / "valid.yaml"
    valid.write_text(
        yaml.dump({"title": "T", "what": "W", "why": "Y", "risk": "LOW"}, allow_unicode=True),
        encoding="utf-8",
    )
    invalid = proposals_dir / "invalid.yaml"
    invalid.write_text("not: [valid: yaml: dict", encoding="utf-8")
    incomplete = proposals_dir / "incomplete.yaml"
    incomplete.write_text(yaml.dump({"title": "T"}, allow_unicode=True), encoding="utf-8")

    import forhacker.cli.commands.meta as meta_mod

    old_proposals = meta_mod.PROPOSALS_DIR
    old_kb = meta_mod.KB_DIR
    try:
        meta_mod.PROPOSALS_DIR = proposals_dir
        meta_mod.KB_DIR = kb_dir
        runner = CliRunner()
        result = runner.invoke(cli, ["meta", "verify"])
        assert result.exit_code == 0
        assert "OK" in result.output
        assert "BROKEN" in result.output or "INCOMPLETE" in result.output
    finally:
        meta_mod.PROPOSALS_DIR = old_proposals
        meta_mod.KB_DIR = old_kb


def test_meta_review_invalid_index(tmp_path):
    proposals_dir = tmp_path / "proposals"
    proposals_dir.mkdir(parents=True)
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir(parents=True)

    import forhacker.cli.commands.meta as meta_mod

    old_proposals = meta_mod.PROPOSALS_DIR
    old_kb = meta_mod.KB_DIR
    try:
        meta_mod.PROPOSALS_DIR = proposals_dir
        meta_mod.KB_DIR = kb_dir
        runner = CliRunner()
        result = runner.invoke(cli, ["meta", "review", "99"])
        assert result.exit_code == 0
        assert "Invalid" in result.output
    finally:
        meta_mod.PROPOSALS_DIR = old_proposals
        meta_mod.KB_DIR = old_kb


def test_meta_review_without_flag(tmp_path):
    proposals_dir = tmp_path / "proposals"
    proposals_dir.mkdir(parents=True)
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir(parents=True)

    proposal_data = {
        "title": "Review Test",
        "what": "Something to do",
        "why": "Because",
        "risk": "LOW",
        "relevance_score": 0.5,
        "quality_score": 0.6,
    }
    (proposals_dir / "review_me.yaml").write_text(yaml.dump(proposal_data, allow_unicode=True), encoding="utf-8")

    import forhacker.cli.commands.meta as meta_mod

    old_proposals = meta_mod.PROPOSALS_DIR
    old_kb = meta_mod.KB_DIR
    try:
        meta_mod.PROPOSALS_DIR = proposals_dir
        meta_mod.KB_DIR = kb_dir
        runner = CliRunner()
        result = runner.invoke(cli, ["meta", "review", "1"])
        assert result.exit_code == 0
        assert "Review Test" in result.output
        assert "--approve" in result.output
    finally:
        meta_mod.PROPOSALS_DIR = old_proposals
        meta_mod.KB_DIR = old_kb


def test_meta_review_reject(tmp_path):
    proposals_dir = tmp_path / "proposals"
    proposals_dir.mkdir(parents=True)
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir(parents=True)

    proposal_data = {
        "title": "Reject Me",
        "what": "Bad idea",
        "why": "Because",
        "risk": "HIGH",
    }
    (proposals_dir / "reject_me.yaml").write_text(yaml.dump(proposal_data, allow_unicode=True), encoding="utf-8")

    import forhacker.cli.commands.meta as meta_mod

    old_proposals = meta_mod.PROPOSALS_DIR
    old_kb = meta_mod.KB_DIR
    try:
        meta_mod.PROPOSALS_DIR = proposals_dir
        meta_mod.KB_DIR = kb_dir
        runner = CliRunner()
        result = runner.invoke(cli, ["meta", "review", "1", "--reject"])
        assert result.exit_code == 0
        assert "Rejected" in result.output
        assert not (proposals_dir / "reject_me.yaml").exists()
    finally:
        meta_mod.PROPOSALS_DIR = old_proposals
        meta_mod.KB_DIR = old_kb


def test_meta_review_approve(tmp_path):
    proposals_dir = tmp_path / "proposals"
    proposals_dir.mkdir(parents=True)
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir(parents=True)

    proposal_data = {
        "title": "Approve Me",
        "what": "Good idea",
        "why": "Because",
        "risk": "LOW",
    }
    (proposals_dir / "approve_me.yaml").write_text(yaml.dump(proposal_data, allow_unicode=True), encoding="utf-8")

    import forhacker.cli.commands.meta as meta_mod

    old_proposals = meta_mod.PROPOSALS_DIR
    old_kb = meta_mod.KB_DIR
    try:
        meta_mod.PROPOSALS_DIR = proposals_dir
        meta_mod.KB_DIR = kb_dir
        runner = CliRunner()
        result = runner.invoke(cli, ["meta", "review", "1", "--approve"])
        assert result.exit_code == 0
        assert "Approved" in result.output
        assert "Snapshot saved" in result.output
        assert not (proposals_dir / "approve_me.yaml").exists()
    finally:
        meta_mod.PROPOSALS_DIR = old_proposals
        meta_mod.KB_DIR = old_kb


def test_meta_snapshots_empty():
    runner = CliRunner()
    result = runner.invoke(cli, ["meta", "snapshots"])
    assert result.exit_code == 0


def test_meta_snapshots_with_data(tmp_path):
    proposals_dir = tmp_path / "proposals"
    proposals_dir.mkdir(parents=True)
    snapshots_dir = proposals_dir / ".snapshots" / "test_change"
    snapshots_dir.mkdir(parents=True)
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir(parents=True)

    (snapshots_dir / "snapshot_meta.yaml").write_text(
        yaml.dump(
            {"change_id": "test_change", "created_at": "2024-01-01T00:00:00", "target_dirs": ["kb"]},
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    import forhacker.cli.commands.meta as meta_mod

    old_proposals = meta_mod.PROPOSALS_DIR
    old_kb = meta_mod.KB_DIR
    try:
        meta_mod.PROPOSALS_DIR = proposals_dir
        meta_mod.KB_DIR = kb_dir
        runner = CliRunner()
        result = runner.invoke(cli, ["meta", "snapshots"])
        assert result.exit_code == 0
        assert "test_change" in result.output
    finally:
        meta_mod.PROPOSALS_DIR = old_proposals
        meta_mod.KB_DIR = old_kb


def test_meta_rollback_not_found():
    runner = CliRunner()
    result = runner.invoke(cli, ["meta", "rollback", "nonexistent_change_id"])
    assert result.exit_code == 0
    assert "No snapshot found" in result.output or "Available snapshots" in result.output


def test_meta_rollback_without_confirm(tmp_path):
    proposals_dir = tmp_path / "proposals"
    proposals_dir.mkdir(parents=True)
    snapshots_dir = proposals_dir / ".snapshots" / "test_rollback"
    snapshots_dir.mkdir(parents=True)
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir(parents=True)

    (snapshots_dir / "snapshot_meta.yaml").write_text(
        yaml.dump(
            {"change_id": "test_rollback", "created_at": "2024-01-01T00:00:00", "target_dirs": ["kb"]},
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    import forhacker.cli.commands.meta as meta_mod

    old_proposals = meta_mod.PROPOSALS_DIR
    old_kb = meta_mod.KB_DIR
    try:
        meta_mod.PROPOSALS_DIR = proposals_dir
        meta_mod.KB_DIR = kb_dir
        runner = CliRunner()
        result = runner.invoke(cli, ["meta", "rollback", "test_rollback"])
        assert result.exit_code == 0
        assert "test_rollback" in result.output
        assert "--confirm" in result.output
    finally:
        meta_mod.PROPOSALS_DIR = old_proposals
        meta_mod.KB_DIR = old_kb
