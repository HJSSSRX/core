import click
from forhacker.cli.commands.case import case_group
from forhacker.cli.commands.plugin import plugin_group
from forhacker.cli.commands.meta import meta_group
from forhacker.cli.commands.kb import kb_group
from forhacker.cli.commands.collab import collab_group


@click.group()
def cli():
    """forhacker — AI-Native Digital Forensics Platform."""
    pass


cli.add_command(case_group, name="case")
cli.add_command(plugin_group, name="plugin")
cli.add_command(meta_group, name="meta")
cli.add_command(kb_group, name="kb")
cli.add_command(collab_group, name="collab")
