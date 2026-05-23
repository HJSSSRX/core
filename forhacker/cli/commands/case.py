import asyncio
import importlib
import os
import sys
from pathlib import Path

import click

from forhacker.llm.deepseek import DeepSeekBackend
from forhacker.plugin.base import BasePlugin
from forhacker.plugin.manager import PluginManager
from forhacker.task.capability import CapabilityRegistry
from forhacker.task.pipeline import Pipeline


def _discover_cell_plugins(cells_root: Path, registry: CapabilityRegistry) -> PluginManager:
    """Auto-discover and load Cell plugins from cells/ directory."""
    manager = PluginManager(registry=registry)
    if not cells_root.exists():
        return manager

    # Add project root to path for cell imports
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
                if isinstance(obj, type) and issubclass(obj, BasePlugin) and obj is not BasePlugin:
                    manager.load_plugin(obj())
                    break
        except Exception:
            click.echo(f"  Warning: failed to load plugin from {cell_dir.name}", err=True)

    return manager


@click.group()
def case_group():
    """Case management."""
    pass


@case_group.command()
@click.argument("name")
def create(name: str):
    """Create a new case."""
    case_dir = Path("shared") / "cases" / name
    case_dir.mkdir(parents=True, exist_ok=True)
    click.echo(f"Case '{name}' created at {case_dir}")


@case_group.command()
def status():
    """Show case status."""
    shared_cases = Path("shared") / "cases"
    if shared_cases.exists():
        cases = list(shared_cases.iterdir())
        if cases:
            for c in cases:
                click.echo(f"  {c.name}")
        else:
            click.echo("No cases found.")
    else:
        click.echo("No cases found.")


@case_group.command()
@click.argument("name")
@click.argument("goal")
@click.option("--model", default="deepseek-chat", help="LLM model")
@click.option("--api-key", default="", help="API key (or set DEEPSEEK_API_KEY env var)")
@click.option("--no-llm-decompose", is_flag=True, help="Use rule-based decomposition")
def run(name: str, goal: str, model: str, api_key: str, no_llm_decompose: bool):
    """Run a forensics pipeline on a case."""
    api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
    case_dir = Path("shared") / "cases" / name
    case_dir.mkdir(parents=True, exist_ok=True)

    registry = CapabilityRegistry()
    cells_root = Path("cells")
    manager = _discover_cell_plugins(cells_root, registry)

    if not manager.loaded_plugins:
        click.echo("No Cell plugins loaded. Create a plugin in cells/<name>/plugin.py")
        return

    click.echo(f"Loaded {len(manager.loaded_plugins)} plugin(s): {', '.join(manager.loaded_plugins)}")
    click.echo(f"Available tools: {sum(len(registry.query(d)) for d in registry.list_domains())}")

    llm = DeepSeekBackend(model=model, api_key=api_key)
    pipeline = Pipeline(case_dir=case_dir, llm=llm, registry=registry, case_id=name)

    click.echo(f"Running pipeline for '{name}' with goal: {goal}")
    report = asyncio.run(pipeline.run(goal, use_llm_decompose=not no_llm_decompose))

    click.echo(f"\nPipeline: {report.status}")
    click.echo(f"  Tasks: {report.completed}/{report.total_tasks} done, {report.failed} failed")
    click.echo(f"  Findings: {len(report.findings)}")
    if report.errors:
        for err in report.errors:
            click.echo(f"  Error: {err}")


@case_group.command()
def plugins():
    """List discovered Cell plugins and their tools."""
    registry = CapabilityRegistry()
    manager = _discover_cell_plugins(Path("cells"), registry)

    if not manager.loaded_plugins:
        click.echo("No plugins found in cells/")
        return

    for name in manager.loaded_plugins:
        tools = []
        for domain in registry.list_domains():
            tools.extend(registry.query(domain=domain))
        click.echo(f"\n{name} ({len(tools)} tools):")
        for t in tools:
            click.echo(f"  {t.name} [{t.risk_level}] — {t.description}")
    if manager.degraded_plugins:
        click.echo(f"\nDegraded: {', '.join(manager.degraded_plugins)}")
