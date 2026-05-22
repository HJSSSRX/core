from datetime import datetime, timezone
from pathlib import Path

import click

from forhacker.collab.shared import check_heartbeat, read_dag_checkpoint
from forhacker.collab.syncthing import SyncthingHealth, check_conflicts, resolve_conflict


@click.group()
def collab_group():
    """Collaboration tools — shared state and Syncthing status."""
    pass


@collab_group.command()
def status():
    """Check shared state and agent heartbeats."""
    shared = Path("shared")
    cases_dir = shared / "cases"

    click.echo("=== Shared State ===")
    if cases_dir.exists():
        cases = [d for d in cases_dir.iterdir() if d.is_dir()]
        if cases:
            for case in cases:
                dag = read_dag_checkpoint(case)
                click.echo(f"\n  Case: {case.name}")
                click.echo(f"  Tasks: {len(dag)}")
                done = sum(1 for t in dag if t.get("status") == "done")
                running = sum(1 for t in dag if t.get("status") == "running")
                click.echo(f"    done={done} running={running}")
        else:
            click.echo("  No active cases.")
    else:
        click.echo("  No shared directory. Run forhacker case create first.")

    # Check for Syncthing conflicts
    conflicts = check_conflicts(shared)
    if conflicts:
        click.echo(f"\n⚠ {len(conflicts)} Syncthing conflict file(s) detected!")
        for cf in conflicts:
            click.echo(f"  {cf}")
        click.echo("  Run 'forhacker collab conflicts' to review.")
    else:
        click.echo("\n  No Syncthing conflicts detected.")

    click.echo("\n=== Agents ===")
    agents_dir = shared / "agents"
    if agents_dir.exists():
        for agent_dir in agents_dir.iterdir():
            if agent_dir.is_dir():
                alive = check_heartbeat(shared, agent_dir.name)
                status_str = "alive" if alive else "stale"
                click.echo(f"  {agent_dir.name}: {status_str}")
    else:
        click.echo("  No registered agents.")


@collab_group.command()
def conflicts():
    """List all Syncthing conflict files with details."""
    shared = Path("shared")
    found = check_conflicts(shared)
    if not found:
        click.echo("No Syncthing conflict files found.")
        return

    click.echo(f"{len(found)} conflict file(s):\n")
    for cf in found:
        stat = cf.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
        click.echo(f"  {cf}")
        click.echo(f"    Modified: {mtime.isoformat()}")
        click.echo(f"    Size: {stat.st_size} bytes")

        # Extract member-id from filename if it's a findings file
        parent = cf.parent.name
        if parent == "findings":
            member_id = cf.name.split(".sync-conflict-")[0]
            click.echo(f"    Member file conflict (owner: {member_id})")
            click.echo(f"    → Auto-resolve: keep {member_id}'s version")


@collab_group.command()
@click.argument("conflict_path")
@click.option("--keep", default="", help="Member ID whose version to keep")
@click.option("--force", is_flag=True, help="Skip confirmation prompt")
def resolve(conflict_path: str, keep: str, force: bool):
    """Resolve a Syncthing conflict file.

    CONFLICT_PATH: path to the .sync-conflict- file
    """
    cf = Path(conflict_path)
    if not cf.exists():
        click.echo(f"File not found: {cf}")
        return

    if ".sync-conflict-" not in cf.name:
        click.echo(f"Not a Syncthing conflict file: {cf}")
        return

    # Auto-resolve for per-member findings files
    stem = cf.name.split(".sync-conflict-")[0]
    parent = cf.parent.name
    is_findings = parent == "findings" and cf.parent.parent.parent.name == "cases"

    if is_findings:
        auto_keep = stem
        if keep and keep != auto_keep:
            click.echo(f"Warning: findings file belongs to {auto_keep}, ignoring --keep={keep}")
        keep = auto_keep
        click.echo(f"Auto-resolving findings file (owner: {keep})")

    # Check for critical files
    if cf.name.startswith("dag_state") or cf.name.startswith("answers"):
        click.echo("⚠ This is a critical shared state file (dag_state/answers).")
        click.echo("  Only the Supervisor or team lead should resolve this.")
        if not force:
            return

    if not keep:
        click.echo("Specify --keep <member-id> to choose which version to keep.")
        return

    if not force:
        click.echo(f"This will discard the non-{keep} version of:")
        click.echo(f"  {cf}")
        click.confirm("Continue?", abort=True)

    resolve_conflict(cf, keep)
    click.echo(f"Resolved: {cf} → kept {keep}'s version")


@collab_group.command()
def syncthing():
    """Check Syncthing health."""
    import asyncio
    health = SyncthingHealth()
    result = asyncio.run(health.check())
    click.echo(f"Syncthing: {result['status']}")
    click.echo(f"  API: {result['api_accessible']}")
    click.echo(f"  Connected devices: {result['connected_devices']}")
    click.echo(f"  Pending: {result['pending_items']}")


@collab_group.command()
@click.option("--folder", default="shared", help="Syncthing folder ID to rescan")
def sync(folder: str):
    """Trigger Syncthing to rescan the shared folder."""
    import asyncio
    health = SyncthingHealth()
    result = asyncio.run(health.rescan(folder_id=folder))
    click.echo(f"Sync rescan: {result['status']}")
    if result.get("message"):
        click.echo(f"  {result['message']}")
