from __future__ import annotations

from pathlib import Path

import click

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
    manager.load_from_cells("cells")
    return manager


@plugin_group.command()
def list_plugins():
    """List installed plugins and their tools."""
    manager = _discover_plugins()

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
        click.echo(f"  Owner: {entry['owner_cell']}")


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
                capture_output=True,
                text=True,
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


def run_{python_name}_example(target: str) -> dict:
    """Example tool implementation — replace with real logic."""
    return {{"target": target, "status": "ok", "confidence": "verified"}}
'''

TEST_CONFTEST = '''"""{name} Cell — test configuration."""

import sys
from pathlib import Path

_cell_dir = Path(__file__).resolve().parent.parent
if str(_cell_dir) not in sys.path:
    sys.path.insert(0, str(_cell_dir))

# In monorepo: also ensure the core project root is importable (forhacker dependency)
_project_root = _cell_dir.parent.parent
if (_project_root / "forhacker" / "__init__.py").exists():
    if str(_project_root) not in sys.path:
        sys.path.insert(0, str(_project_root))
'''

TEST_SKELETON = '''"""{name} Cell — tests."""

from plugin import {class_name}, run_{python_name}_example


def test_plugin_registers_tools():
    plugin = {class_name}()
    tools = plugin.register_tools()
    assert len(tools) >= 1
    assert all(t.name for t in tools)


def test_example_tool_runs(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("hello")
    result = run_{python_name}_example(str(f))
    assert result.get("status") == "ok"
'''

PYPROJECT_SKELETON = """[project]
name = "forhacker-plugin-{name}"
version = "0.1.0"
description = "{name} Cell plugin for ForHacker"
requires-python = ">=3.12"
dependencies = ["forhacker"]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=4.0",
]
"""

README_SKELETON = """# {name}

{description} — Cell plugin for [ForHacker](https://github.com/forhacker/core).

## Install

```bash
pip install -e .
# or via forhacker CLI:
forhacker plugin install {name}
```

## Tools

See `plugin.py` → `register_tools()` for the tool list.

## Development

```bash
pip install -e ".[dev]"
pytest
```
"""

TUTORIAL_SKELETON = """# {name} — Tutorial

## 5-Minute Quick Start

1. This Cell auto-loads when you run `forhacker case run <case> "<goal>"`
2. Verify it's loaded: `forhacker plugin list-plugins`

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

Then implement the tool function in this directory. The function signature is `run_<tool_name>(target: str) -> dict`.

## Testing

```bash
pip install -e ".[dev]"
pytest tests/
```

## Risk Levels

| Level | Meaning | Isolation |
|-------|---------|-----------|
| LOW   | Read-only, safe operations | None |
| MEDIUM | Reads untrusted files | Docker |
| HIGH  | Executes untrusted code | Firecracker VM |

Default is HIGH for any tool not explicitly registered in `risk_levels`.
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

    python_name = name.replace("-", "_")  # safe Python identifier (no hyphens)
    domain = domain or python_name
    class_name = "".join(part.capitalize() for part in python_name.split("_")) + "Plugin"

    target.mkdir(parents=True, exist_ok=True)
    (target / "tests").mkdir(exist_ok=True)
    (target / "knowledge").mkdir(exist_ok=True)

    # plugin.py
    (target / "plugin.py").write_text(
        PLUGIN_SKELETON.format(
            name=name,
            python_name=python_name,
            domain=domain,
            class_name=class_name,
            description=f"Cell plugin: {name}",
        ),
        encoding="utf-8",
    )

    # pyproject.toml
    (target / "pyproject.toml").write_text(PYPROJECT_SKELETON.format(name=name), encoding="utf-8")

    # tests/conftest.py — makes Cell self-contained for standalone testing
    (target / "tests" / "conftest.py").write_text(TEST_CONFTEST.format(name=name), encoding="utf-8")
    # tests/__init__.py
    (target / "tests" / "__init__.py").write_text("", encoding="utf-8")
    # tests/test_plugin.py
    (target / "tests" / "test_plugin.py").write_text(
        TEST_SKELETON.format(name=name, python_name=python_name, class_name=class_name), encoding="utf-8"
    )

    # README.md
    (target / "README.md").write_text(
        README_SKELETON.format(name=name, description=f"Cell plugin: {name}"), encoding="utf-8"
    )

    # TUTORIAL.md
    (target / "TUTORIAL.md").write_text(TUTORIAL_SKELETON.format(name=name), encoding="utf-8")

    # knowledge/.gitkeep (for KB CI auto-ingestion)
    (target / "knowledge" / ".gitkeep").write_text("", encoding="utf-8")

    click.echo(f"Cell plugin '{name}' scaffolded at {target}/")
    for p in sorted(target.rglob("*")):
        if p.is_file():
            click.echo(f"  {p.relative_to(target.parent)}")
    click.echo(f"\nNext: cd cells/{name} && pip install -e '.[dev]' && pytest")
