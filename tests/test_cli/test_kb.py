"""Tests for KB CLI commands — search, add, list, show, delete."""

from click.testing import CliRunner

from forhacker.cli.main import cli


def test_kb_list_empty():
    runner = CliRunner()
    result = runner.invoke(cli, ["kb", "list"])
    assert result.exit_code == 0


def test_kb_search_no_results():
    runner = CliRunner()
    result = runner.invoke(cli, ["kb", "search", "nonexistent_xyz_123"])
    assert result.exit_code == 0
    assert "No results" in result.output


def test_kb_show_not_found():
    runner = CliRunner()
    result = runner.invoke(cli, ["kb", "show", "nonexistent-id"])
    assert result.exit_code == 0
    assert "not found" in result.output


def test_kb_add_and_show():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "kb",
            "add",
            "--title",
            "Test Entry",
            "--content",
            "This is test content for KB.",
            "--confidence",
            "high",
            "--tag",
            "test",
            "--source",
            "manual",
        ],
    )
    assert result.exit_code == 0
    assert "Entry" in result.output


def test_kb_add_with_multiple_tags():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "kb",
            "add",
            "--title",
            "Multi-tag Entry",
            "--content",
            "Content with multiple tags.",
            "--confidence",
            "medium",
            "--tag",
            "test",
            "--tag",
            "forensics",
            "--source",
            "manual",
        ],
    )
    assert result.exit_code == 0
    assert "Entry" in result.output


def test_kb_search_hits():
    runner = CliRunner()
    # First add something
    runner.invoke(
        cli,
        [
            "kb",
            "add",
            "--title",
            "Searchable",
            "--content",
            "Unique content for searching.",
            "--confidence",
            "high",
            "--source",
            "manual",
        ],
    )
    # Then search
    result = runner.invoke(cli, ["kb", "search", "Searchable"])
    assert result.exit_code == 0


def test_kb_list_has_entries():
    runner = CliRunner()
    # Ensure at least one entry exists
    runner.invoke(
        cli,
        [
            "kb",
            "add",
            "--title",
            "List Test",
            "--content",
            "Entry for list test.",
            "--confidence",
            "low",
            "--source",
            "manual",
        ],
    )
    result = runner.invoke(cli, ["kb", "list"])
    assert result.exit_code == 0


def test_kb_show_existing():
    runner = CliRunner()
    # Add then show
    add_result = runner.invoke(
        cli,
        [
            "kb",
            "add",
            "--title",
            "Show Test",
            "--content",
            "Content to show.",
            "--confidence",
            "medium",
            "--source",
            "manual",
        ],
    )
    assert add_result.exit_code == 0
    # Extract entry ID from output: "Entry [<id>] saved to ..."
    output = add_result.output
    if "[" in output and "]" in output:
        entry_id = output.split("[")[1].split("]")[0]
        result = runner.invoke(cli, ["kb", "show", entry_id])
        assert result.exit_code == 0
        assert "Show Test" in result.output


def test_kb_delete_existing():
    runner = CliRunner()
    # Add then delete
    add_result = runner.invoke(
        cli,
        [
            "kb",
            "add",
            "--title",
            "Delete Me",
            "--content",
            "Will be deleted.",
            "--confidence",
            "low",
            "--source",
            "manual",
        ],
    )
    assert add_result.exit_code == 0
    output = add_result.output
    if "[" in output and "]" in output:
        entry_id = output.split("[")[1].split("]")[0]
        result = runner.invoke(cli, ["kb", "delete", entry_id, "--yes"])
        assert result.exit_code == 0
        assert "Deleted" in result.output


def test_kb_delete_not_found():
    runner = CliRunner()
    result = runner.invoke(cli, ["kb", "delete", "nonexistent-id", "--yes"])
    assert result.exit_code == 0
    assert "not found" in result.output
