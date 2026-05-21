from forhacker.plugin.base import Tool
from forhacker.task.capability import CapabilityRegistry


def test_register_and_query_by_domain():
    registry = CapabilityRegistry()
    registry.register(Tool(name="vol3", description="Volatility 3", domain="forensics", risk_level="MEDIUM"))
    registry.register(Tool(name="nmap", description="Network scanner", domain="pentest", risk_level="LOW"))
    results = registry.query(domain="forensics")
    assert len(results) == 1
    assert results[0].name == "vol3"


def test_query_unknown_domain_returns_empty():
    registry = CapabilityRegistry()
    results = registry.query(domain="nonexistent")
    assert results == []


def test_list_domains():
    registry = CapabilityRegistry()
    registry.register(Tool(name="t1", description="d1", domain="forensics", risk_level="LOW"))
    registry.register(Tool(name="t2", description="d2", domain="pentest", risk_level="LOW"))
    domains = registry.list_domains()
    assert "forensics" in domains
    assert "pentest" in domains


def test_duplicate_tool_overwrites():
    registry = CapabilityRegistry()
    registry.register(Tool(name="dup", description="first", domain="test", risk_level="LOW"))
    registry.register(Tool(name="dup", description="second", domain="test", risk_level="MEDIUM"))
    tools = registry.query(domain="test")
    assert len(tools) == 1
    assert tools[0].description == "second"
