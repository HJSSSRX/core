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
