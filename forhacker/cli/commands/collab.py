from pathlib import Path

import click

from forhacker.collab.shared import check_heartbeat, read_dag_checkpoint
from forhacker.collab.syncthing import SyncthingHealth


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
def syncthing():
    """Check Syncthing health."""
    import asyncio
    health = SyncthingHealth()
    result = asyncio.run(health.check())
    click.echo(f"Syncthing: {result['status']}")
    click.echo(f"  API: {result['api_accessible']}")
    click.echo(f"  Connected devices: {result['connected_devices']}")
    click.echo(f"  Pending: {result['pending_items']}")
