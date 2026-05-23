from __future__ import annotations

"""Tests for MCP Server — JSON-RPC 2.0 over stdio transport."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from forhacker.plugin.base import Tool
from forhacker.plugin.mcp_server import MCP_VERSION, MCPServer


@pytest.fixture
def server():
    return MCPServer()


@pytest.fixture
def mock_plugin_manager():
    mgr = MagicMock()
    mgr.loaded_plugins = ["test_plugin"]
    tool = Tool(name="example", description="An example tool", domain="test", risk_level="LOW")
    mgr.get_plugin_tools.return_value = [tool]
    return mgr


class TestMCPServerInit:
    def test_default_server_info(self, server):
        assert server._server_info["name"] == "forhacker-mcp"
        assert server._server_info["version"] == "0.1.0"

    def test_empty_tools_on_init(self, server):
        assert server.list_tools() == []

    def test_empty_resources_on_init(self, server):
        assert server.list_resources() == []


class TestRegisterTool:
    def test_register_tool_adds_to_list(self, server):
        server.register_tool(
            name="test_tool",
            description="A test tool",
            input_schema={"type": "object", "properties": {"input": {"type": "string"}}},
        )
        tools = server.list_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "test_tool"
        assert tools[0]["description"] == "A test tool"

    def test_register_tool_with_handler(self, server):
        handler = MagicMock(return_value={"result": "ok"})
        server.register_tool(
            name="exec_tool",
            description="Executable tool",
            input_schema={"type": "object"},
            handler=handler,
        )
        result = server.call_tool("exec_tool", {"param": "value"})
        handler.assert_called_once_with(param="value")
        assert "result" in result["content"][0]["text"]

    def test_register_multiple_tools(self, server):
        for i in range(5):
            server.register_tool(
                name=f"tool_{i}",
                description=f"Tool {i}",
                input_schema={"type": "object"},
            )
        assert len(server.list_tools()) == 5


class TestRegisterFromPlugins:
    def test_register_from_plugins(self, server, mock_plugin_manager):
        count = server.register_from_plugins(mock_plugin_manager)
        assert count == 1
        tools = server.list_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "test_plugin__example"
        assert "[test]" in tools[0]["description"]

    def test_register_from_plugins_sorts_by_name(self, server):
        mgr = MagicMock()
        mgr.loaded_plugins = ["zzz_plugin", "aaa_plugin"]
        tool_a = Tool(name="tool_a", description="A", domain="alpha", risk_level="LOW")
        tool_z = Tool(name="tool_z", description="Z", domain="zeta", risk_level="LOW")
        mgr.get_plugin_tools.side_effect = lambda name: [tool_a] if name == "aaa_plugin" else [tool_z]

        count = server.register_from_plugins(mgr)
        assert count == 2
        tools = server.list_tools()
        assert tools[0]["name"] == "aaa_plugin__tool_a"
        assert tools[1]["name"] == "zzz_plugin__tool_z"

    def test_register_from_empty_plugins(self, server):
        mgr = MagicMock()
        mgr.loaded_plugins = []
        count = server.register_from_plugins(mgr)
        assert count == 0


class TestResources:
    def test_register_resource(self, server):
        server.register_resource(
            uri="test://example",
            name="Test Resource",
            mime_type="text/plain",
            content="Hello, World!",
        )
        resources = server.list_resources()
        assert len(resources) == 1
        assert resources[0]["uri"] == "test://example"
        assert resources[0]["name"] == "Test Resource"
        assert resources[0]["mimeType"] == "text/plain"

    def test_register_kb_resources(self, server, tmp_path):
        kb_dir = tmp_path / "kb"
        kb_dir.mkdir()
        (kb_dir / "entry1.md").write_text("# First Entry\nContent of first entry.", encoding="utf-8")
        (kb_dir / "entry2.md").write_text("# Second Entry\nContent of second entry.", encoding="utf-8")

        server.register_kb_resources(kb_dir)
        resources = server.list_resources()
        assert len(resources) == 2
        uris = {r["uri"] for r in resources}
        assert "kb://entry1" in uris
        assert "kb://entry2" in uris
        names = {r["name"] for r in resources}
        assert "KB: First Entry" in names

    def test_register_kb_resources_empty_dir(self, server, tmp_path):
        kb_dir = tmp_path / "empty_kb"
        kb_dir.mkdir()
        server.register_kb_resources(kb_dir)
        assert server.list_resources() == []

    def test_register_kb_resources_nonexistent_dir(self, server):
        server.register_kb_resources(Path("/nonexistent_kb_dir_999"))
        assert server.list_resources() == []


class TestCallTool:
    def test_call_tool_success_returns_content(self, server):
        server.register_tool(
            name="greet",
            description="Greet someone",
            input_schema={"type": "object"},
            handler=lambda name="World": {"greeting": f"Hello, {name}!"},
        )
        result = server.call_tool("greet", {"name": "Alice"})
        assert "isError" not in result
        content = json.loads(result["content"][0]["text"])
        assert content["greeting"] == "Hello, Alice!"

    def test_call_tool_not_found(self, server):
        result = server.call_tool("nonexistent", {})
        assert result["isError"] is True
        assert "not found" in result["content"][0]["text"]

    def test_call_tool_handler_raises(self, server):
        def failing_handler(**kwargs):
            raise ValueError("something went wrong")

        server.register_tool(
            name="broken",
            description="Always fails",
            input_schema={"type": "object"},
            handler=failing_handler,
        )
        result = server.call_tool("broken", {})
        assert result["isError"] is True
        assert "failed" in result["content"][0]["text"]

    def test_call_tool_without_handler(self, server):
        server.register_tool(
            name="no_handler",
            description="No handler registered",
            input_schema={"type": "object"},
        )
        result = server.call_tool("no_handler", {})
        assert result["isError"] is True
        assert "not found" in result["content"][0]["text"]


class TestHandleRequest:
    def test_initialize(self, server):
        request = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        response = server._handle_request(request)
        assert response["id"] == 1
        result = response["result"]
        assert result["protocolVersion"] == MCP_VERSION
        assert result["serverInfo"]["name"] == "forhacker-mcp"
        assert "tools" in result["capabilities"]
        assert "resources" in result["capabilities"]

    def test_initialized_notification(self, server):
        request = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        response = server._handle_request(request)
        assert response is None

    def test_tools_list(self, server):
        server.register_tool(
            name="tool_a",
            description="First tool",
            input_schema={"type": "object"},
        )
        request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        response = server._handle_request(request)
        assert response["id"] == 2
        assert len(response["result"]["tools"]) == 1

    def test_tools_call(self, server):
        server.register_tool(
            name="echo",
            description="Echo input",
            input_schema={"type": "object"},
            handler=lambda message="": {"echo": message},
        )
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "echo", "arguments": {"message": "hi"}},
        }
        response = server._handle_request(request)
        assert response["id"] == 3
        content = response["result"]["content"][0]
        assert content["type"] == "text"
        assert "hi" in content["text"]

    def test_tools_call_not_found(self, server):
        request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "ghost", "arguments": {}},
        }
        response = server._handle_request(request)
        assert response["result"]["isError"] is True

    def test_resources_list(self, server):
        server.register_resource("uri://a", "Resource A", "text/plain", "content")
        request = {"jsonrpc": "2.0", "id": 5, "method": "resources/list", "params": {}}
        response = server._handle_request(request)
        assert len(response["result"]["resources"]) == 1

    def test_resources_read(self, server):
        server.register_resource("uri://test", "Test", "text/plain", "hello world")
        request = {"jsonrpc": "2.0", "id": 8, "method": "resources/read", "params": {"uri": "uri://test"}}
        response = server._handle_request(request)
        assert response["id"] == 8
        contents = response["result"]["contents"]
        assert len(contents) == 1
        assert contents[0]["uri"] == "uri://test"
        assert contents[0]["text"] == "hello world"

    def test_resources_read_not_found(self, server):
        request = {"jsonrpc": "2.0", "id": 9, "method": "resources/read", "params": {"uri": "kb://nonexistent"}}
        response = server._handle_request(request)
        assert response["error"]["code"] == -32002
        assert "not found" in response["error"]["message"]

    def test_ping(self, server):
        request = {"jsonrpc": "2.0", "id": 6, "method": "ping", "params": {}}
        response = server._handle_request(request)
        assert response["id"] == 6
        assert response["result"] == {}

    def test_unknown_method(self, server):
        request = {"jsonrpc": "2.0", "id": 7, "method": "unknown/thing", "params": {}}
        response = server._handle_request(request)
        assert response["id"] == 7
        assert response["error"]["code"] == -32601
        assert "Method not found" in response["error"]["message"]


class TestCallToolEdgeCases:
    def test_call_tool_with_complex_nested_result(self, server):
        server.register_tool(
            name="complex",
            description="Returns nested data",
            input_schema={"type": "object"},
            handler=lambda: {"nested": {"deep": [1, 2, 3], "value": None}},
        )
        result = server.call_tool("complex", {})
        data = json.loads(result["content"][0]["text"])
        assert data["nested"]["deep"] == [1, 2, 3]

    def test_call_tool_ensure_ascii_false_preserves_unicode(self, server):
        server.register_tool(
            name="unicode_test",
            description="Returns unicode",
            input_schema={"type": "object"},
            handler=lambda: {"message": "你好世界"},
        )
        result = server.call_tool("unicode_test", {})
        assert "你好世界" in result["content"][0]["text"]
