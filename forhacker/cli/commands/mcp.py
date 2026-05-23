"""MCP CLI — start the Model Context Protocol server for AI client integration."""

import click

from forhacker.cli.commands.plugin import _discover_plugins
from forhacker.plugin.mcp_server import MCPServer


@click.group()
def mcp_group():
    """MCP server — expose tools to AI clients via Model Context Protocol."""
    pass


@mcp_group.command()
def serve():
    """Start the MCP JSON-RPC server over stdio.

    Connects Claude Desktop and other MCP-compatible clients
    to all installed Cell plugin tools.
    """
    manager = _discover_plugins()
    server = MCPServer()
    count = server.register_from_plugins(manager)
    click.echo(f"MCP Server starting with {count} tools from {len(manager.loaded_plugins)} plugins", err=True)
    server.serve()
