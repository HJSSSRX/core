import logging

from forhacker.plugin.base import BasePlugin, Tool
from forhacker.task.capability import CapabilityRegistry

logger = logging.getLogger(__name__)


class PluginManager:
    def __init__(self, registry: CapabilityRegistry):
        self._registry = registry
        self._plugins: dict[str, BasePlugin] = {}
        self._plugin_tools: dict[str, list[Tool]] = {}
        self.degraded_plugins: list[str] = []

    def load_plugin(self, plugin: BasePlugin) -> None:
        try:
            tools = plugin.register_tools()
            for tool in tools:
                self._registry.register(tool)
            self._plugins[plugin.name] = plugin
            self._plugin_tools[plugin.name] = tools
        except Exception as e:
            logger.error("Plugin %s failed to load: %s", plugin.name, e)
            self.degraded_plugins.append(plugin.name)

    @property
    def loaded_plugins(self) -> list[str]:
        return list(self._plugins.keys())

    def get_plugin_tools(self, plugin_name: str) -> list[Tool]:
        return self._plugin_tools.get(plugin_name, [])
