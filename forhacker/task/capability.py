from __future__ import annotations

from forhacker.plugin.base import Tool


class CapabilityRegistry:
    """Tool/agent capability lookup owned by task/, populated by plugin/."""

    def __init__(self):
        self._tools: dict[str, dict[str, Tool]] = {}  # domain → {tool_name: Tool}

    def register(self, tool: Tool) -> None:
        self._tools.setdefault(tool.domain, {})[tool.name] = tool

    def query(self, domain: str) -> list[Tool]:
        domain_tools = self._tools.get(domain, {})
        return list(domain_tools.values())

    def list_domains(self) -> list[str]:
        return list(self._tools.keys())
