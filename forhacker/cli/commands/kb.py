from __future__ import annotations

from pathlib import Path

import click

from forhacker.kb.entry import KBEntry
from forhacker.kb.store import KBStore

KB_DIR = Path("shared") / "kb"


@click.group()
def kb_group():
    """Knowledge base management."""
    pass


@kb_group.command()
@click.argument("query")
@click.option("--tag", "-t", multiple=True, help="Filter by tag(s)")
def search(query: str, tag: tuple[str, ...]):
    """Search the knowledge base."""
    store = KBStore(KB_DIR)
    results = store.search(keyword=query, tags=list(tag) if tag else None)
    if not results:
        click.echo(f"No results for: {query}")
        return
    click.echo(f"Found {len(results)} result(s):\n")
    for entry in results:
        tags_str = ", ".join(entry.tags) if entry.tags else "none"
        click.echo(f"  [{entry.id}] {entry.title}")
        click.echo(f"  Tags: {tags_str} | Confidence: {entry.confidence}")
        click.echo(f"  {entry.content[:200]}...\n")


@kb_group.command()
@click.option("--title", "-t", prompt="Title", help="Entry title")
@click.option("--tag", "-g", multiple=True, help="Tags for categorization")
@click.option("--source", "-s", default="manual", help="Source of this knowledge")
@click.option("--content", "-c", prompt="Content", help="Entry body (Markdown)")
@click.option("--confidence", default="medium", type=click.Choice(["high", "medium", "low"]))
def add(title: str, tag: tuple[str, ...], source: str, content: str, confidence: str):
    """Add a knowledge entry."""
    store = KBStore(KB_DIR)
    entry = KBEntry(
        title=title,
        tags=list(tag),
        source=source,
        content=content,
        confidence=confidence,
    )
    path = store.add(entry)
    click.echo(f"Entry [{entry.id}] saved to {path}")


@kb_group.command(name="list")
def list_entries():
    """List all knowledge base entries."""
    store = KBStore(KB_DIR)
    entries = store.list_all()
    if not entries:
        click.echo("Knowledge base is empty.")
        return
    for entry in entries:
        tags_str = ", ".join(entry.tags) if entry.tags else "none"
        click.echo(f"  [{entry.id}] {entry.title} ({len(entry.content)} chars) [{tags_str}]")


@kb_group.command()
@click.argument("entry_id")
def show(entry_id: str):
    """Show full content of a knowledge entry."""
    store = KBStore(KB_DIR)
    entry = store.get(entry_id)
    if entry is None:
        click.echo(f"Entry {entry_id} not found.")
        return
    click.echo(f"Title: {entry.title}")
    click.echo(f"Tags: {', '.join(entry.tags) or 'none'}")
    click.echo(f"Source: {entry.source}")
    click.echo(f"Confidence: {entry.confidence}")
    click.echo(f"Created: {entry.created_at}")
    click.echo(f"\n{entry.content}")


@kb_group.command()
@click.argument("entry_id")
@click.confirmation_option(prompt="Delete this entry?")
def delete(entry_id: str):
    """Delete a knowledge entry."""
    store = KBStore(KB_DIR)
    if store.delete(entry_id):
        click.echo(f"Deleted {entry_id}.")
    else:
        click.echo(f"Entry {entry_id} not found.")
