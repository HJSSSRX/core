"""log-parser Cell — tests."""

from plugin import LogParserPlugin


def test_plugin_registers_tools():
    plugin = LogParserPlugin()
    tools = plugin.register_tools()
    assert len(tools) >= 1
    assert all(t.name for t in tools)
    assert all(t.domain for t in tools)
    assert all(t.risk_level in ("LOW", "MEDIUM", "HIGH") for t in tools)


def test_plugin_metadata():
    plugin = LogParserPlugin()
    assert plugin.name == "log-parser"
    assert plugin.version
    assert plugin.domain == "forensics"
