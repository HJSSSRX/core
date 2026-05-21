import click

@click.group()
def meta_group():
    """MetaAgent controls."""
    pass

@meta_group.command()
def scan():
    """Trigger a manual MetaAgent scan."""
    click.echo("Scan started. Check proposals with 'forhacker meta proposals'.")

@meta_group.command()
def proposals():
    """List pending MetaAgent proposals."""
    click.echo("No pending proposals.")
