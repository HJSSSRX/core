import asyncio
import os
from pathlib import Path

import click

from forhacker.llm.deepseek import DeepSeekBackend
from forhacker.plugin.base import Tool
from forhacker.task.capability import CapabilityRegistry
from forhacker.task.pipeline import Pipeline


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
@click.option("--model", default="deepseek-chat", help="LLM model for decomposition and execution")
@click.option("--api-key", default="", help="API key (defaults to DEEPSEEK_API_KEY env var)")
@click.option("--no-llm-decompose", is_flag=True, help="Use rule-based instead of LLM decomposition")
def run(name: str, goal: str, model: str, api_key: str, no_llm_decompose: bool):
    """Run a forensics pipeline on a case with a given goal."""
    api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
    case_dir = Path("shared") / "cases" / name
    case_dir.mkdir(parents=True, exist_ok=True)

    registry = CapabilityRegistry()
    # Register built-in analysis tools
    registry.register(Tool(name="volatility3", description="Memory forensics with Volatility 3",
                           domain="forensics", risk_level="MEDIUM"))
    registry.register(Tool(name="bulk_extractor", description="File carving and extraction",
                           domain="forensics", risk_level="LOW"))
    registry.register(Tool(name="yara_scanner", description="YARA rule-based malware scanning",
                           domain="forensics", risk_level="MEDIUM"))

    llm = DeepSeekBackend(model=model, api_key=api_key)
    pipeline = Pipeline(case_dir=case_dir, llm=llm, registry=registry, case_id=name)

    click.echo(f"Running pipeline for case '{name}' with goal: {goal}")
    report = asyncio.run(pipeline.run(goal, use_llm_decompose=not no_llm_decompose))

    click.echo(f"\nPipeline complete: {report.status}")
    click.echo(f"  Tasks: {report.completed}/{report.total_tasks} completed, {report.failed} failed")
    click.echo(f"  Findings: {len(report.findings)}")
    if report.errors:
        click.echo(f"  Errors: {len(report.errors)}")
        for err in report.errors:
            click.echo(f"    - {err}")
