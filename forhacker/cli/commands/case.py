import click


@click.group()
def case_group():
    """Case management."""
    pass


@case_group.command()
@click.argument("name")
def create(name: str):
    """Create a new case."""
    from pathlib import Path
    case_dir = Path("shared") / "cases" / name
    case_dir.mkdir(parents=True, exist_ok=True)
    click.echo(f"Case '{name}' created.")


@case_group.command()
def status():
    """Show case status."""
    click.echo("No active case.")
