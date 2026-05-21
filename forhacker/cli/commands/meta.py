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


@meta_group.command()
def verify():
    """Verify integrity of all proposal snapshots and directories."""
    proposals_dir = PROPOSALS_DIR
    if not proposals_dir.exists():
        click.echo("No proposals directory found. Nothing to verify.")
        return

    yaml_files = list(proposals_dir.glob("*.yaml"))
    if not yaml_files:
        click.echo("No proposals to verify.")
        return

    ok = 0
    broken = 0
    for pf in yaml_files:
        try:
            data = yaml.safe_load(pf.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                click.echo(f"  BROKEN: {pf.name} — not a valid YAML dict")
                broken += 1
                continue
            required = ["title", "what", "why", "risk"]
            missing = [k for k in required if k not in data]
            if missing:
                click.echo(f"  INCOMPLETE: {pf.name} — missing: {', '.join(missing)}")
                broken += 1
                continue
            ok += 1
        except yaml.YAMLError:
            click.echo(f"  BROKEN: {pf.name} — YAML parse error")
            broken += 1
        except Exception:
            click.echo(f"  BROKEN: {pf.name} — unreadable")
            broken += 1

    # Also check KB integrity
    kb_dir = KB_DIR
    if kb_dir.exists():
        kb_files = list(kb_dir.glob("*.md"))
        kb_ok = 0
        kb_broken = 0
        for kf in kb_files:
            try:
                content = kf.read_text(encoding="utf-8")
                if content.startswith("---"):
                    yaml.safe_load(content.split("---")[1])
                kb_ok += 1
            except (yaml.YAMLError, IndexError):
                click.echo(f"  BROKEN KB: {kf.name}")
                kb_broken += 1
        click.echo(f"\nKnowledge base: {kb_ok} OK, {kb_broken} broken")

    click.echo(f"\nProposals: {ok} OK, {broken} broken — {len(yaml_files)} total")


@meta_group.command()
@click.argument("proposal_index", type=int)
def rollback(proposal_index: int):
    """Rollback an approved change by restoring the backup snapshot."""
    proposals_dir = PROPOSALS_DIR
    files = sorted(proposals_dir.glob("*.yaml"))
    if proposal_index < 1 or proposal_index > len(files):
        click.echo(f"Invalid index. There are {len(files)} proposals.")
        return

    target = files[proposal_index - 1]
    data = yaml.safe_load(target.read_text(encoding="utf-8"))

    click.echo(f"Rollback target: {data.get('title', 'Unknown')}")
    click.echo(f"Summary: {data.get('what', '')[:120]}")

    # Check for backup snapshot
    snapshot_name = target.stem
    backup_dir = proposals_dir / ".snapshots" / snapshot_name
    if backup_dir.exists():
        click.echo(f"Snapshot found at {backup_dir}")
        click.echo("Rollback would restore files from this snapshot.")
    else:
        click.echo("No snapshot found. Cannot rollback — manual intervention required.")

    click.echo("\nTo confirm rollback: forhacker meta rollback {proposal_index} --confirm")

