from typing import Any


class MCPServer:
    def __init__(self):
        self._tools: list[dict[str, Any]] = []

    def register_tool(self, name: str, description: str, input_schema: dict):
        self._tools.append({"name": name, "description": description, "inputSchema": input_schema})

    def list_tools(self) -> list[dict[str, Any]]:
        return list(self._tools)
