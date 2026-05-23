import importlib
import logging

from forhacker.plugin.base import BasePlugin, Tool
from forhacker.task.capability import CapabilityRegistry

logger = logging.getLogger(__name__)


class PluginManager:
    def __init__(self, registry: CapabilityRegistry):
        self._registry = registry
        self._plugins: dict[str, BasePlugin] = {}
        self._plugin_tools: dict[str, list[Tool]] = {}
        self._plugin_modules: dict[str, object] = {}
        self.degraded_plugins: list[str] = []

    def load_plugin(self, plugin: BasePlugin, plugin_module: object | None = None) -> None:
        try:
            tools = plugin.register_tools()
            # Auto-bind handler functions: convention run_<tool_name>(target: str) -> dict
            if plugin_module is not None:
                for tool in tools:
                    handler_name = f"run_{tool.name}"
                    handler = getattr(plugin_module, handler_name, None)
                    if callable(handler):
                        tool.handler = handler
            for tool in tools:
                self._registry.register(tool)
            self._plugins[plugin.name] = plugin
            self._plugin_tools[plugin.name] = tools
            if plugin_module is not None:
                self._plugin_modules[plugin.name] = plugin_module
        except Exception as e:
            logger.error("Plugin %s failed to load: %s", plugin.name, e)
            self.degraded_plugins.append(plugin.name)

    @property
    def loaded_plugins(self) -> list[str]:
        return list(self._plugins.keys())

    def get_plugin_tools(self, plugin_name: str) -> list[Tool]:
        return self._plugin_tools.get(plugin_name, [])

    def load_from_cells(self, cells_root: str = "cells") -> None:
        """Auto-discover and load all Cell plugins from a directory.

        Scans cells/<dir>/plugin.py for BasePlugin subclasses.
        Each Cell plugin.py should define: a BasePlugin subclass + run_<tool>() functions.
        """
        import sys
        from pathlib import Path

        cells_dir = Path(cells_root)
        if not cells_dir.is_dir():
            return

        project_root = str(cells_dir.parent)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        for cell_dir in sorted(cells_dir.iterdir()):
            if not cell_dir.is_dir() or cell_dir.name.startswith("_") or cell_dir.name.startswith("."):
                continue
            plugin_file = cell_dir / "plugin.py"
            if not plugin_file.exists():
                continue
            try:
                module_path = f"cells.{cell_dir.name}.plugin"
                module = importlib.import_module(module_path)
                for attr in dir(module):
                    obj = getattr(module, attr)
                    if isinstance(obj, type) and issubclass(obj, BasePlugin) and obj is not BasePlugin:
                        self.load_plugin(obj(), plugin_module=module)
                        break
            except Exception as exc:
                logger.warning("Cell %s failed to load: %s", cell_dir.name, exc)
                self.degraded_plugins.append(cell_dir.name)
