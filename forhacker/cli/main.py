from __future__ import annotations

import logging
import sys

import click

from forhacker.cli.commands.case import case_group
from forhacker.cli.commands.collab import collab_group
from forhacker.cli.commands.evidence import evidence_group
from forhacker.cli.commands.kb import kb_group
from forhacker.cli.commands.mcp import mcp_group
from forhacker.cli.commands.meta import meta_group
from forhacker.cli.commands.plugin import plugin_group
from forhacker.cli.commands.system import system_group
from forhacker.exceptions import ForHackerError

logger = logging.getLogger(__name__)


@click.group()
@click.option("--debug", "-d", is_flag=True, help="Enable debug logging and full tracebacks.")
def cli(debug: bool = False):
    """forhacker — AI-Native Digital Forensics Platform."""
    if debug:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s [%(name)s] %(message)s")
        logger.debug("Debug mode enabled")


cli.add_command(case_group, name="case")
cli.add_command(evidence_group, name="evidence")
cli.add_command(plugin_group, name="plugin")
cli.add_command(meta_group, name="meta")
cli.add_command(kb_group, name="kb")
cli.add_command(collab_group, name="collab")
cli.add_command(system_group, name="system")
cli.add_command(mcp_group, name="mcp")


def main():
    """Entry point with unified error handling."""
    try:
        cli()
    except ForHackerError as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        sys.exit(1)
    except Exception:
        click.secho("An unexpected internal error occurred.", fg="red", err=True)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
