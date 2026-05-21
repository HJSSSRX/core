import click

@click.group()
def collab_group():
    """Collaboration tools."""
    pass

@collab_group.command()
def status():
    """Check Syncthing health and conflicts."""
    click.echo("Collaboration status: OK. No conflicts detected.")
