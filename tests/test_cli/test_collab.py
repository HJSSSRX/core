from __future__ import annotations

"""Tests for collab CLI commands — status, conflicts, resolve, syncthing, sync."""

from pathlib import Path

from click.testing import CliRunner

from forhacker.cli.main import cli


def test_collab_status_no_shared():
    runner = CliRunner()
    result = runner.invoke(cli, ["collab", "status"])
    assert result.exit_code == 0


def test_collab_status_empty_shared(tmp_path):
    shared_dir = tmp_path / "shared"
    shared_dir.mkdir()

    import os

    old_cwd = Path.cwd()
    os.chdir(str(tmp_path))
    try:
        runner = CliRunner()
        result = runner.invoke(cli, ["collab", "status"])
        assert result.exit_code == 0
        assert "No shared directory" in result.output or "No active cases" in result.output
    finally:
        os.chdir(str(old_cwd))


def test_collab_status_with_cases(tmp_path):
    cases_dir = tmp_path / "shared" / "cases" / "testcase"
    cases_dir.mkdir(parents=True)
    import yaml

    (cases_dir / "dag_state.yaml").write_text(
        yaml.dump(
            {
                "tasks": [
                    {"id": "1", "status": "done"},
                    {"id": "2", "status": "running"},
                    {"id": "3", "status": "pending"},
                ]
            }
        ),
        encoding="utf-8",
    )

    import os

    old_cwd = Path.cwd()
    os.chdir(str(tmp_path))
    try:
        runner = CliRunner()
        result = runner.invoke(cli, ["collab", "status"])
        assert result.exit_code == 0
        assert "testcase" in result.output
        assert "done=1" in result.output or "done" in result.output
    finally:
        os.chdir(str(old_cwd))


def test_collab_status_with_agents(tmp_path):
    shared_dir = tmp_path / "shared"
    shared_dir.mkdir()
    agents_dir = shared_dir / "agents" / "agent-1"
    agents_dir.mkdir(parents=True)
    (agents_dir / "heartbeat").write_text("2024-06-01T12:00:00Z")

    import os

    old_cwd = Path.cwd()
    os.chdir(str(tmp_path))
    try:
        runner = CliRunner()
        result = runner.invoke(cli, ["collab", "status"])
        assert result.exit_code == 0
        assert "agent-1" in result.output
    finally:
        os.chdir(str(old_cwd))


def test_collab_conflicts_no_shared():
    runner = CliRunner()
    result = runner.invoke(cli, ["collab", "conflicts"])
    assert result.exit_code == 0
    assert "No Syncthing conflict" in result.output or "conflict" in result.output.lower()


def test_collab_resolve_not_found():
    runner = CliRunner()
    result = runner.invoke(cli, ["collab", "resolve", "nonexistent.sync-conflict-12345"])
    assert result.exit_code == 0
    assert "File not found" in result.output


def test_collab_resolve_not_conflict(tmp_path):
    f = tmp_path / "regular_file.txt"
    f.write_text("content", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["collab", "resolve", str(f)])
    assert result.exit_code == 0
    assert "Not a Syncthing conflict" in result.output


def test_collab_syncthing():
    runner = CliRunner()
    result = runner.invoke(cli, ["collab", "syncthing"])
    # Syncthing may or may not be running — just ensure it doesn't crash
    assert result.exit_code in (0, 1)


def test_collab_sync():
    runner = CliRunner()
    result = runner.invoke(cli, ["collab", "sync"])
    # May fail if no Syncthing — ensure graceful output
    assert result.exit_code in (0, 1)


def test_collab_conflicts_with_conflict_files(tmp_path):
    shared_dir = tmp_path / "shared"
    conflict_file = shared_dir / "test.sync-conflict-20240101-120000"
    conflict_file.parent.mkdir(parents=True)
    conflict_file.write_text("conflicting content", encoding="utf-8")

    import os

    old_cwd = Path.cwd()
    os.chdir(str(tmp_path))
    try:
        runner = CliRunner()
        result = runner.invoke(cli, ["collab", "conflicts"])
        assert result.exit_code == 0
        assert ".sync-conflict-" in result.output
    finally:
        os.chdir(str(old_cwd))


def test_collab_resolve_findings_auto_resolve(tmp_path):
    findings_dir = tmp_path / "shared" / "cases" / "mycase" / "findings"
    findings_dir.mkdir(parents=True)
    conflict_file = findings_dir / "member-A.sync-conflict-20240101"
    conflict_file.write_text("findings content", encoding="utf-8")

    import os

    old_cwd = Path.cwd()
    os.chdir(str(tmp_path))
    try:
        runner = CliRunner()
        result = runner.invoke(cli, ["collab", "resolve", str(conflict_file), "--force"])
        assert result.exit_code == 0
        assert "member-A" in result.output or "Resolved" in result.output
    finally:
        os.chdir(str(old_cwd))


def test_collab_resolve_missing_keep(tmp_path):
    conflict_file = tmp_path / "shared" / "config.sync-conflict-123"
    conflict_file.parent.mkdir(parents=True)
    conflict_file.write_text("config content", encoding="utf-8")

    import os

    old_cwd = Path.cwd()
    os.chdir(str(tmp_path))
    try:
        runner = CliRunner()
        result = runner.invoke(cli, ["collab", "resolve", str(conflict_file)])
        assert result.exit_code == 0
        assert "--keep" in result.output or "Specify --keep" in result.output
    finally:
        os.chdir(str(old_cwd))


def test_collab_resolve_critical_file_no_force(tmp_path):
    conflict_file = tmp_path / "shared" / "dag_state.sync-conflict-123"
    conflict_file.parent.mkdir(parents=True)
    conflict_file.write_text("critical", encoding="utf-8")

    import os

    old_cwd = Path.cwd()
    os.chdir(str(tmp_path))
    try:
        runner = CliRunner()
        result = runner.invoke(cli, ["collab", "resolve", str(conflict_file), "--keep", "admin"])
        assert result.exit_code == 0
        assert "Supervisor" in result.output or "team lead" in result.output
    finally:
        os.chdir(str(old_cwd))


def test_collab_resolve_with_keep_and_force(tmp_path):
    conflict_file = tmp_path / "shared" / "config.sync-conflict-456"
    conflict_file.parent.mkdir(parents=True)
    conflict_file.write_text("config data", encoding="utf-8")

    import os

    old_cwd = Path.cwd()
    os.chdir(str(tmp_path))
    try:
        runner = CliRunner()
        result = runner.invoke(cli, ["collab", "resolve", str(conflict_file), "--keep", "admin", "--force"])
        assert result.exit_code == 0
        assert "Resolved" in result.output
    finally:
        os.chdir(str(old_cwd))


def test_collab_status_with_syncthing_conflicts(tmp_path):
    shared_dir = tmp_path / "shared"
    shared_dir.mkdir()
    cases_dir = shared_dir / "cases" / "case1"
    cases_dir.mkdir(parents=True)
    import yaml

    (cases_dir / "dag_state.yaml").write_text(
        yaml.dump({"tasks": [{"id": "1", "status": "done"}]}),
        encoding="utf-8",
    )
    # Create a conflict file
    (shared_dir / "somefile.sync-conflict-2024").write_text("conflict", encoding="utf-8")

    import os

    old_cwd = Path.cwd()
    os.chdir(str(tmp_path))
    try:
        runner = CliRunner()
        result = runner.invoke(cli, ["collab", "status"])
        assert result.exit_code == 0
        assert "conflict" in result.output.lower()
    finally:
        os.chdir(str(old_cwd))


def test_collab_sync_with_folder_option():
    runner = CliRunner()
    result = runner.invoke(cli, ["collab", "sync", "--folder", "custom_shared"])
    assert result.exit_code in (0, 1)
