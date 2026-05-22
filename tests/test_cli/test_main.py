from pathlib import Path

from click.testing import CliRunner

from forhacker.cli.main import cli


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "forhacker" in result.output


def test_case_create_dry():
    runner = CliRunner()
    result = runner.invoke(cli, ["case", "create", "test-case"])
    assert result.exit_code == 0
    assert "test-case" in result.output


def test_case_status_empty():
    runner = CliRunner()
    result = runner.invoke(cli, ["case", "status"])
    assert result.exit_code == 0


def test_plugin_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["plugin", "--help"])
    assert result.exit_code == 0
    assert "list-plugins" in result.output


def test_plugin_list():
    runner = CliRunner()
    result = runner.invoke(cli, ["plugin", "list-plugins"])
    assert result.exit_code == 0


def test_plugin_marketplace():
    runner = CliRunner()
    result = runner.invoke(cli, ["plugin", "marketplace"])
    assert result.exit_code == 0


def test_meta_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["meta", "--help"])
    assert result.exit_code == 0


def test_meta_proposals():
    runner = CliRunner()
    result = runner.invoke(cli, ["meta", "proposals"])
    assert result.exit_code == 0


def test_meta_watchdog():
    runner = CliRunner()
    result = runner.invoke(cli, ["meta", "watchdog"])
    assert result.exit_code == 0


def test_meta_verify():
    runner = CliRunner()
    result = runner.invoke(cli, ["meta", "verify"])
    assert result.exit_code == 0


def test_kb_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["kb", "--help"])
    assert result.exit_code == 0


def test_collab_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["collab", "--help"])
    assert result.exit_code == 0


def test_collab_conflicts():
    runner = CliRunner()
    result = runner.invoke(cli, ["collab", "conflicts"])
    assert result.exit_code == 0


def test_evidence_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["evidence", "--help"])
    assert result.exit_code == 0
    assert "verify" in result.output or "purge" in result.output


def test_evidence_verify_no_dir():
    runner = CliRunner()
    result = runner.invoke(cli, ["evidence", "verify", "nonexistent"])
    assert result.exit_code == 0


def test_plugin_create(tmp_path):
    import shutil
    cells_dir = tmp_path / "cells"
    cells_dir.mkdir()
    # Create a minimal plugin.py so _discover_plugins doesn't crash
    runner = CliRunner()
    # Use the real cells dir since CliRunner runs from cwd
    result = runner.invoke(cli, ["plugin", "create", "test_plugin"])
    assert result.exit_code == 0
    # Clean up the created plugin
    created = Path("cells") / "test_plugin"
    if created.exists():
        shutil.rmtree(created)


def test_plugin_create_already_exists():
    # Create first, then try again
    runner = CliRunner()
    runner.invoke(cli, ["plugin", "create", "test_existing"])
    result = runner.invoke(cli, ["plugin", "create", "test_existing"])
    # Second create should exit cleanly with message
    assert result.exit_code == 0
    # Clean up
    import shutil
    created = Path("cells") / "test_existing"
    if created.exists():
        shutil.rmtree(created)
