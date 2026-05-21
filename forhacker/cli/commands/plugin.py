import click

@click.group()
def plugin_group():
    """Plugin management."""
    pass

@plugin_group.command()
@click.argument("name")
def install(name: str):
    """Install a plugin from the marketplace."""
    click.echo(f"Plugin '{name}' installed.")

@plugin_group.command()
def list_plugins():
    """List installed plugins."""
    click.echo("No plugins installed.")
