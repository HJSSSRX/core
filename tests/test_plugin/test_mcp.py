from forhacker.plugin.mcp_server import MCPServer


def test_mcp_server_list_tools_empty():
    server = MCPServer()
    tools = server.list_tools()
    assert tools == []


def test_mcp_server_register_and_list():
    server = MCPServer()
    server.register_tool(name="vol3", description="Run Volatility 3", input_schema={"type": "object"})
    tools = server.list_tools()
    assert len(tools) == 1
    assert tools[0]["name"] == "vol3"
