from __future__ import annotations

"""timeline-analyzer Cell — tests."""

from plugin import TimelineAnalyzerPlugin


def test_plugin_registers_tools():
    plugin = TimelineAnalyzerPlugin()
    tools = plugin.register_tools()
    assert len(tools) >= 1
    assert all(t.name for t in tools)
    assert all(t.domain for t in tools)
    assert all(t.risk_level in ("LOW", "MEDIUM", "HIGH") for t in tools)


def test_plugin_metadata():
    plugin = TimelineAnalyzerPlugin()
    assert plugin.name == "timeline-analyzer"
    assert plugin.version
    assert plugin.domain == "forensics"
