import click
from forhacker.cli.commands.case import case_group


@click.group()
def cli():
    """forhacker — AI-Native Digital Forensics Platform."""
    pass


cli.add_command(case_group, name="case")
