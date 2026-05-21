import pytest
from forhacker.plugin.base import BasePlugin, Tool


def test_tool_dataclass():
    t = Tool(name="strings", description="Extract strings from binary", domain="forensics", risk_level="LOW")
    assert t.name == "strings"
    assert t.domain == "forensics"
    assert t.risk_level == "LOW"


def test_cannot_instantiate_base_plugin():
    with pytest.raises(TypeError):
        BasePlugin()


def test_concrete_plugin_must_implement_methods():

    class IncompletePlugin(BasePlugin):
        name = "test"
        version = "0.1"
        domain = "forensics"
        risk_levels = {}

    with pytest.raises(TypeError):
        IncompletePlugin()
