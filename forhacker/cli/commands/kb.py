import click


@click.group()
def kb_group():
    """Knowledge base (backend deferred to Phase 6)."""
    pass

@kb_group.command()
@click.argument("query")
def search(query: str):
    """Search the knowledge base."""
    click.echo(f"No results for: {query}")
    click.echo("Knowledge base backend is deferred to Phase 6.")
