from __future__ import annotations

"""MCP Server — exposes forhacker Cell tools as Model Context Protocol tools.

Implements the JSON-RPC 2.0 transport over stdio for integration with
Claude Desktop and other MCP-compatible AI clients.

Spec: https://spec.modelcontextprotocol.io/
"""

import asyncio
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

MCP_VERSION = "2024-11-05"


class MCPServer:
    """MCP Server exposing forhacker tools to external AI systems via JSON-RPC over stdio."""

    def __init__(self):
        self._tools: list[dict[str, Any]] = []
        self._tool_handlers: dict[str, Callable] = {}
        self._resources: list[dict[str, Any]] = []
        self._server_info = {
            "name": "forhacker-mcp",
            "version": "0.1.0",
        }

    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: dict[str, Any],
        handler: Callable | None = None,
    ):
        """Register an MCP tool with optional execution handler."""
        tool = {
            "name": name,
            "description": description,
            "inputSchema": input_schema,
        }
        self._tools.append(tool)
        if handler:
            self._tool_handlers[name] = handler

    def register_from_plugins(self, plugin_manager) -> int:
        """Auto-register all Cell plugin tools from a PluginManager instance.

        Returns count of tools registered.
        """
        count = 0
        for plugin_name in sorted(plugin_manager.loaded_plugins):
            for tool in plugin_manager.get_plugin_tools(plugin_name):
                safe_name = f"{plugin_name}__{tool.name}"
                self.register_tool(
                    name=safe_name,
                    description=f"[{tool.domain}] {tool.description}",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "input": {
                                "type": "string",
                                "description": f"Input for {tool.name}",
                            }
                        },
                        "required": ["input"],
                    },
                )
                count += 1
        return count

    def register_resource(self, uri: str, name: str, mime_type: str, content: str):
        """Register a readable MCP resource."""
        self._resources.append(
            {
                "uri": uri,
                "name": name,
                "mimeType": mime_type,
            }
        )
        setattr(self, f"_resource_{hash(uri) % 10000}", content)

    def register_kb_resources(self, kb_dir: str | Path):
        """Register all KB entries as MCP resources."""
        kb_path = Path(kb_dir)
        if not kb_path.exists():
            return
        for md_file in sorted(kb_path.glob("*.md")):
            content = md_file.read_text(encoding="utf-8")
            title = content.split("\n")[0].lstrip("# ").strip() if content else md_file.stem
            self.register_resource(
                uri=f"kb://{md_file.stem}",
                name=f"KB: {title}",
                mime_type="text/markdown",
                content=content,
            )

    def list_tools(self) -> list[dict[str, Any]]:
        return list(self._tools)

    def list_resources(self) -> list[dict[str, Any]]:
        return list(self._resources)

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a registered tool by name.

        Returns MCP tool result dict with content items.
        """
        if name not in self._tool_handlers:
            available = ", ".join(sorted(self._tool_handlers.keys())) or "none"
            return {
                "content": [{"type": "text", "text": f"Tool '{name}' not found. Available: {available}"}],
                "isError": True,
            }
        handler = self._tool_handlers[name]
        try:
            result = handler(**arguments)
            return {
                "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, default=str)}],
            }
        except Exception as exc:
            return {
                "content": [{"type": "text", "text": f"Tool '{name}' failed: {exc}"}],
                "isError": True,
            }

    def _handle_request(self, request: dict[str, Any]) -> dict[str, Any] | None:
        """Process a single JSON-RPC request/notification. Returns response or None for notifications."""
        req_id = request.get("id")
        method = request.get("method", "")
        params = request.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": MCP_VERSION,
                    "serverInfo": self._server_info,
                    "capabilities": {
                        "tools": {},
                        "resources": {},
                    },
                },
            }

        if method == "notifications/initialized":
            return None

        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": self.list_tools()},
            }

        if method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            result = self.call_tool(tool_name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": result,
            }

        if method == "resources/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"resources": self.list_resources()},
            }

        if method == "resources/read":
            uri = params.get("uri", "")
            content = getattr(self, f"_resource_{hash(uri) % 10000}", None)
            if content is None:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32002, "message": f"Resource not found: {uri}"},
                }
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "contents": [
                        {"uri": uri, "text": content},
                    ]
                },
            }

        if method == "ping":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {},
            }

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }

    def serve(self):
        """Run the MCP JSON-RPC server over stdio. Blocking call."""
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self._serve_stdio(loop))

    async def _serve_stdio(self, loop):
        """Async stdio transport: read JSON-RPC from stdin, write responses to stdout."""
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)

        writer_transport, writer_protocol = await loop.connect_write_pipe(asyncio.streams.FlowControlMixin, sys.stdout)
        writer = asyncio.StreamWriter(writer_transport, writer_protocol, reader, loop)

        # Read loop — each message is one line of JSON
        while True:
            try:
                line = await reader.readline()
                if not line:
                    break
                request = json.loads(line.decode("utf-8"))
                response = self._handle_request(request)
                if response is not None:
                    writer.write((json.dumps(response, ensure_ascii=False) + "\n").encode("utf-8"))
                    await writer.drain()
            except json.JSONDecodeError:
                continue
            except Exception:
                break
