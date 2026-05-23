from __future__ import annotations

"""registry-analyzer Cell — tests."""

from plugin import RegistryAnalyzerPlugin


def test_plugin_registers_tools():
    plugin = RegistryAnalyzerPlugin()
    tools = plugin.register_tools()
    assert len(tools) >= 1
    assert all(t.name for t in tools)
    assert all(t.domain for t in tools)
    assert all(t.risk_level in ("LOW", "MEDIUM", "HIGH") for t in tools)


def test_plugin_metadata():
    plugin = RegistryAnalyzerPlugin()
    assert plugin.name == "registry-analyzer"
    assert plugin.version
    assert plugin.domain == "forensics"
