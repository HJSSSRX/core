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
        for tool in manager.get_plugin_tools(name):
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
            import subprocess
            click.echo(f"Cloning {repo} into cells/{name} ...")
            result = subprocess.run(
                ["git", "clone", repo, str(target)],
                capture_output=True, text=True,
            )
            if result.returncode == 0:
                click.echo(f"Plugin '{name}' installed successfully.")
            else:
                click.echo(f"Clone failed: {result.stderr}")
                click.echo(f"Manual install: git clone {repo} cells/{name}")
            return
    click.echo(f"Plugin '{name}' not found in marketplace.")


PLUGIN_SKELETON = '''"""
{name} — {description}
"""
from forhacker.plugin.base import BasePlugin
from forhacker.task.capability import Tool


class {class_name}(BasePlugin):
    name = "{name}"
    version = "0.1.0"
    domain = "{domain}"
    risk_levels = {{}}  # TODO: assign LOW|MEDIUM|HIGH per tool

    def register_tools(self) -> list[Tool]:
        return [
            Tool(
                name="{name}_example",
                description="Example tool — replace with real implementation",
                domain=self.domain,
                risk_level="LOW",
            ),
        ]
'''

TUTORIAL_SKELETON = """# {name} — Tutorial

## Quick Start

1. This Cell plugin auto-loads when you run `forhacker case run <case> "<goal>"`
2. Check that it's loaded: `forhacker plugin list`

## Adding Tools

Edit `plugin.py` and add entries to `register_tools()`:

```python
Tool(
    name="your_tool_name",
    description="What this tool does",
    domain=self.domain,
    risk_level="LOW",  # LOW | MEDIUM | HIGH
)
```

## Testing

```bash
# Run from the project root:
python3 -m pytest tests/

# Run just this Cell's tests:
python3 -m pytest tests/test_plugin/ -k {name}
```

## Tool Implementation

Each tool is a Python function or class in this directory.

## Risk Levels

- LOW: Safe to run in Docker (metadata extraction, hash computation, strings)
- MEDIUM: File parsing, archive extraction, log analysis
- HIGH: Malware analysis, exploit verification (requires Firecracker microVM, blocks if unavailable)

Default is HIGH for any tool not explicitly registered.
"""


@plugin_group.command()
@click.argument("name")
@click.option("--domain", default="", help="Plugin domain (default: derived from name)")
def create(name: str, domain: str):
    """Scaffold a new Cell plugin under cells/<name>/."""
    target = Path("cells") / name
    if target.exists():
        click.echo(f"Plugin directory already exists: {target}")
        return

    domain = domain or name.replace("_", "-")
    class_name = "".join(part.capitalize() for part in name.replace("-", "_").split("_")) + "Plugin"

    target.mkdir(parents=True, exist_ok=True)

    # plugin.py
    plugin_content = PLUGIN_SKELETON.format(
        name=name, domain=domain, class_name=class_name,
        description=f"Cell plugin: {name}",
    )
    (target / "plugin.py").write_text(plugin_content, encoding="utf-8")

    # TUTORIAL.md
    (target / "TUTORIAL.md").write_text(
        TUTORIAL_SKELETON.format(name=name), encoding="utf-8"
    )

    # README.md
    (target / "README.md").write_text(f"# {name}\n\nCell plugin for ForHacker.\n", encoding="utf-8")

    click.echo(f"Cell plugin '{name}' scaffolded at {target}")
    click.echo(f"  {target}/plugin.py")
    click.echo(f"  {target}/TUTORIAL.md")
    click.echo(f"  {target}/README.md")
    click.echo(f"\nNext: edit {target}/plugin.py to add your tools, then run 'forhacker plugin list'")
