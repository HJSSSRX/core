"""Tests for case CLI commands — create, status, plugins, run."""

from click.testing import CliRunner

from forhacker.cli.main import cli


class TestCaseCreate:
    def test_create_new_case(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["case", "create", "test_case_create"])
        assert result.exit_code == 0
        assert "test_case_create" in result.output

    def test_create_case_with_special_chars(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["case", "create", "case-2024_01"])
        assert result.exit_code == 0
        assert "case-2024_01" in result.output

    def test_create_chinese_name(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["case", "create", "2026龙岩杯"])
        assert result.exit_code == 0
        assert "2026龙岩杯" in result.output


class TestCaseStatus:
    def test_status_empty(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["case", "status"])
        assert result.exit_code == 0

    def test_status_with_cases(self, tmp_path):
        cases_dir = tmp_path / "shared" / "cases"
        cases_dir.mkdir(parents=True)
        (cases_dir / "case_a").mkdir()
        (cases_dir / "case_b").mkdir()

        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(str(tmp_path))
            runner = CliRunner()
            result = runner.invoke(cli, ["case", "status"])
            assert result.exit_code == 0
            assert "case_a" in result.output or "case_b" in result.output
        finally:
            os.chdir(old_cwd)

    def test_status_no_shared_dir(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["case", "status"])
        assert result.exit_code == 0


class TestCasePlugins:
    def test_plugins_no_cells_dir(self, tmp_path):
        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(str(tmp_path))
            runner = CliRunner()
            result = runner.invoke(cli, ["case", "plugins"])
            assert result.exit_code == 0
            assert "No plugins found" in result.output
        finally:
            os.chdir(old_cwd)

    def test_plugins_with_cells_dir(self, tmp_path):
        cells_dir = tmp_path / "cells" / "test_cell"
        cells_dir.mkdir(parents=True)
        # Create a minimal plugin
        plugin_code = """
from forhacker.plugin.base import BasePlugin, Tool

class TestCellPlugin(BasePlugin):
    name = "test_cell"
    version = "0.1.0"
    domain = "test"
    risk_levels = {}

    def register_tools(self) -> list[Tool]:
        return [Tool(name="dummy", description="Dummy tool", domain="test", risk_level="LOW")]
"""
        (cells_dir / "plugin.py").write_text(plugin_code, encoding="utf-8")

        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(str(tmp_path))
            runner = CliRunner()
            result = runner.invoke(cli, ["case", "plugins"])
            assert result.exit_code == 0
            assert "test_cell" in result.output
        finally:
            os.chdir(old_cwd)


class TestCaseRun:
    def test_run_no_plugins_loaded(self, tmp_path):
        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(str(tmp_path))
            runner = CliRunner()
            result = runner.invoke(cli, ["case", "run", "testcase", "analyze memory"])
            assert result.exit_code == 0
            assert "No Cell plugins loaded" in result.output
        finally:
            os.chdir(old_cwd)

    def test_run_with_plugins_no_api_key(self, tmp_path):
        cells_dir = tmp_path / "cells" / "memcell"
        cells_dir.mkdir(parents=True)
        plugin_code = """
from forhacker.plugin.base import BasePlugin, Tool

class MemCellPlugin(BasePlugin):
    name = "memcell"
    version = "0.1.0"
    domain = "memory"
    risk_levels = {}

    def register_tools(self) -> list[Tool]:
        return [Tool(name="pslist", description="List processes", domain="memory", risk_level="LOW")]
"""
        (cells_dir / "plugin.py").write_text(plugin_code, encoding="utf-8")

        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(str(tmp_path))
            runner = CliRunner()
            result = runner.invoke(
                cli,
                ["case", "run", "memcase", "analyze", "--model", "deepseek-chat", "--no-llm-decompose"],
            )
            assert result.exit_code == 0
            assert "memcell" in result.output
        finally:
            os.chdir(old_cwd)

    def test_run_creates_case_dir(self, tmp_path):
        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(str(tmp_path))
            runner = CliRunner()
            result = runner.invoke(cli, ["case", "run", "newcase", "test", "--no-llm-decompose"])
            assert result.exit_code == 0
            # Case dir should be created even if no plugins
            case_dir = tmp_path / "shared" / "cases" / "newcase"
            assert case_dir.exists()
        finally:
            os.chdir(old_cwd)


class TestCaseHelp:
    def test_case_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["case", "--help"])
        assert result.exit_code == 0
        assert "create" in result.output
        assert "run" in result.output
        assert "plugins" in result.output

    def test_case_create_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["case", "create", "--help"])
        assert result.exit_code == 0

    def test_case_run_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["case", "run", "--help"])
        assert result.exit_code == 0
        assert "--model" in result.output


class TestMCPCommand:
    def test_mcp_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["mcp", "--help"])
        assert result.exit_code == 0
        assert "serve" in result.output
