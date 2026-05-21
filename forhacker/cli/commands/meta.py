import asyncio
from pathlib import Path

import click
import yaml

from forhacker.meta.evaluator import Evaluator
from forhacker.meta.scheduler import MetaScheduler

PROPOSALS_DIR = Path("shared") / "meta" / "proposals"
KB_DIR = Path("shared") / "kb"


@click.group()
def meta_group():
    """MetaAgent controls — self-improvement scans and proposals."""
    pass


@meta_group.command()
@click.option("--source", "-s", multiple=True, help="Add a custom source URL to scan")
def scan(source: tuple[str, ...]):
    """Trigger a MetaAgent scan of configured sources."""
    scheduler = MetaScheduler(KB_DIR, PROPOSALS_DIR)
    if source:
        for s in source:
            scheduler.add_source(name=s, url=s, category="manual")
    click.echo("Scanning sources...")
    result = asyncio.run(scheduler.scan_once())
    click.echo(f"Sources checked: {result['sources_checked']}")
    click.echo(f"Candidates: {result['candidates']}")
    click.echo(f"Passed evaluator: {result['passed']}")
    click.echo(f"Pending proposals: {result['pending_proposals']}")


@meta_group.command()
def proposals():
    """List pending MetaAgent improvement proposals."""
    scheduler = MetaScheduler(KB_DIR, PROPOSALS_DIR)
    items = scheduler.list_pending_proposals()
    if not items:
        click.echo("No pending proposals.")
        return
    for i, p in enumerate(items, 1):
        click.echo(f"\n  [{i}] {p.get('title', 'Untitled')}")
        click.echo(f"  Risk: {p.get('risk', '?')} | Relevance: {p.get('relevance_score', 0):.2f}")
        click.echo(f"  What: {p.get('what', '')[:120]}")
        click.echo(f"  Why: {p.get('why', '')[:120]}")


@meta_group.command()
def sources():
    """List configured MetaAgent sources."""
    scheduler = MetaScheduler(KB_DIR, PROPOSALS_DIR)
    for src in scheduler._agent.sources:
        click.echo(f"  {src.name} [{src.category}] — {src.url}")


@meta_group.command()
@click.argument("proposal_index", type=int)
@click.option("--approve", is_flag=True, help="Approve and apply this proposal")
@click.option("--reject", is_flag=True, help="Reject and delete this proposal")
def review(proposal_index: int, approve: bool, reject: bool):
    """Review a proposal: approve or reject."""
    proposals_dir = PROPOSALS_DIR
    files = sorted(proposals_dir.glob("*.yaml"))
    if proposal_index < 1 or proposal_index > len(files):
        click.echo(f"Invalid index. There are {len(files)} proposals.")
        return
    target = files[proposal_index - 1]
    data = yaml.safe_load(target.read_text(encoding="utf-8"))

    if approve:
        click.echo(f"Approved: {data.get('title', '')}")
        click.echo(f"Action: {data.get('what', '')}")
        target.unlink()
        click.echo("Proposal approved and removed from queue.")
    elif reject:
        click.echo(f"Rejected: {data.get('title', '')}")
        target.unlink()
        click.echo("Proposal rejected and removed.")
    else:
        click.echo(f"Title: {data.get('title')}")
        click.echo(f"What: {data.get('what')}")
        click.echo(f"Why: {data.get('why')}")
        click.echo(f"Risk: {data.get('risk')}")
        click.echo(f"Relevance: {data.get('relevance_score', 0):.2f}")
        click.echo(f"Quality: {data.get('quality_score', 0):.2f}")
        click.echo("\nUse --approve or --reject to act on this proposal.")


@meta_group.command()
def watchdog():
    """Check if the evaluator watchdog has triggered."""
    evaluator = Evaluator()
    if evaluator.should_alert():
        click.echo("WARNING: 7 days with zero passed proposals. Tune thresholds or add sources.")
    else:
        click.echo("Watchdog OK — proposals are flowing.")
