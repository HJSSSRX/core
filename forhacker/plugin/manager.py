import logging

from forhacker.plugin.base import BasePlugin
from forhacker.task.capability import CapabilityRegistry

logger = logging.getLogger(__name__)


class PluginManager:
    def __init__(self, registry: CapabilityRegistry):
        self._registry = registry
        self._plugins: dict[str, BasePlugin] = {}
        self.degraded_plugins: list[str] = []

    def load_plugin(self, plugin: BasePlugin) -> None:
        try:
            for tool in plugin.register_tools():
                self._registry.register(tool)
            self._plugins[plugin.name] = plugin
        except Exception as e:
            logger.error("Plugin %s failed to load: %s", plugin.name, e)
            self.degraded_plugins.append(plugin.name)

    @property
    def loaded_plugins(self) -> list[str]:
        return list(self._plugins.keys())
