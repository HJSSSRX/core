import importlib
import sys
from pathlib import Path

import click

from forhacker.plugin.base import BasePlugin
from forhacker.plugin.manager import PluginManager
from forhacker.plugin.marketplace import MARKETPLACE
from forhacker.task.capability import CapabilityRegistry


@click.group()
def plugin_group():
    """Plugin management — install, list, and discover Cell plugins."""
    pass


def _discover_plugins() -> PluginManager:
    registry = CapabilityRegistry()
    manager = PluginManager(registry=registry)
    cells_root = Path("cells")
    if not cells_root.exists():
        return manager
    project_root = str(cells_root.parent)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    for cell_dir in sorted(cells_root.iterdir()):
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
                if (isinstance(obj, type) and issubclass(obj, BasePlugin)
                        and obj is not BasePlugin):
                    manager.load_plugin(obj())
                    break
        except Exception as exc:
            click.echo(f"  Warning: {cell_dir.name} failed to load: {exc}", err=True)
    return manager


@plugin_group.command()
def list_plugins():
    """List installed plugins and their tools."""
    manager = _discover_plugins()
    registry = manager._registry

    if not manager.loaded_plugins:
        click.echo("No plugins installed. Create one in cells/<name>/plugin.py")
        click.echo("See cells/TUTORIAL.md for a quick start guide.")
        return

    for name in sorted(manager.loaded_plugins):
        click.echo(f"\n{name}")
        for domain in registry.list_domains():
            for tool in registry.query(domain=domain):
                click.echo(f"  {tool.name} [{tool.risk_level}] — {tool.description}")

    if manager.degraded_plugins:
        click.echo(f"\nDegraded: {', '.join(manager.degraded_plugins)}")


@plugin_group.command()
def marketplace():
    """Browse the plugin marketplace."""
    if not MARKETPLACE:
        click.echo("Marketplace is empty. Publish the first plugin!")
        return
    for entry in MARKETPLACE:
        click.echo(f"\n  {entry['name']} v{entry['version']}")
        click.echo(f"  {entry['description']}")
        click.echo(f"  Repo: {entry['repo_url']}")
        click.echo(f"  Author: {entry['author']}")


@plugin_group.command()
@click.argument("name")
def install(name: str):
    """Install a plugin from the marketplace."""
    for entry in MARKETPLACE:
        if entry["name"] == name:
            repo = entry["repo_url"]
            target = Path("cells") / name
            if target.exists():
                click.echo(f"Plugin '{name}' already installed at {target}")
                return
            click.echo(f"Clone {repo} into cells/{name}")
            click.echo("Run: git clone {repo} cells/{name}")
            return
    click.echo(f"Plugin '{name}' not found in marketplace.")
