import pytest
from forhacker.plugin.base import BasePlugin, Tool
from forhacker.plugin.manager import PluginManager
from forhacker.task.capability import CapabilityRegistry


class FakePlugin(BasePlugin):
    name = "fake-forensics"
    version = "0.1.0"
    domain = "forensics"
    risk_levels = {"fake_tool": "MEDIUM"}

    def register_tools(self) -> list[Tool]:
        return [Tool(name="fake_tool", description="A fake tool", domain="forensics", risk_level="MEDIUM")]


class FailingPlugin(BasePlugin):
    name = "failing-plugin"
    version = "0.1.0"
    domain = "osint"
    risk_levels = {}

    def register_tools(self) -> list[Tool]:
        raise RuntimeError("simulated load failure")


@pytest.mark.asyncio
async def test_plugin_manager_loads_plugin():
    registry = CapabilityRegistry()
    manager = PluginManager(registry=registry)
    manager.load_plugin(FakePlugin())
    tools = registry.query(domain="forensics")
    assert len(tools) == 1
    assert tools[0].name == "fake_tool"


@pytest.mark.asyncio
async def test_plugin_manager_isolates_failure():
    registry = CapabilityRegistry()
    manager = PluginManager(registry=registry)
    manager.load_plugin(FailingPlugin())
    manager.load_plugin(FakePlugin())
    assert "failing-plugin" in manager.degraded_plugins
    tools = registry.query(domain="forensics")
    assert len(tools) == 1
