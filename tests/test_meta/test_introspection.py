import tempfile
from pathlib import Path

from forhacker.meta.introspection import IntrospectionAgent, PlatformIntrospection


def test_introspection_scans_python_files():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "module").mkdir()
        (root / "module" / "target.py").write_text(
            "def _unused_helper():\n    pass\n\ndef public_api():\n    return _unused_helper()\n"
        )
        agent = IntrospectionAgent()
        issues = agent.scan(root)
        unused = [i for i in issues if i.category == "unused_code"]
        assert len(unused) == 0


def test_introspection_detects_syntax_error():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "broken.py").write_text("def foo(: pass\n")
        agent = IntrospectionAgent()
        issues = agent.scan(root)
        assert len(issues) == 1
        assert issues[0].severity == "HIGH"
        assert "syntax" in issues[0].description.lower()


def test_introspection_skips_pycache():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cache = root / "__pycache__"
        cache.mkdir()
        (cache / "cached.py").write_text("def _x():\n    pass\n")
        agent = IntrospectionAgent()
        issues = agent.scan(root)
        assert len(issues) == 0


def test_introspection_empty_directory():
    with tempfile.TemporaryDirectory() as td:
        agent = IntrospectionAgent()
        issues = agent.scan(Path(td))
        assert issues == []


def test_introspection_flags_truly_unused_private():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "mod.py").write_text("def _unused():\n    pass\n\ndef used():\n    pass\n")
        agent = IntrospectionAgent()
        issues = agent.scan(root)
        unused = [i for i in issues if i.category == "unused_code" and "_unused" in i.description]
        assert len(unused) == 1


def test_introspection_implements_abc():
    agent = IntrospectionAgent()
    assert isinstance(agent, PlatformIntrospection)


def test_list_registered_plugins_empty(tmp_path):
    agent = IntrospectionAgent(root=tmp_path)
    plugins = agent.list_registered_plugins()
    assert isinstance(plugins, list)


def test_get_skill_configurations():
    agent = IntrospectionAgent()
    config = agent.get_skill_configurations()
    assert isinstance(config, dict)
    assert "skills" in config
    assert "hooks" in config


def test_get_recent_metrics():
    agent = IntrospectionAgent()
    metrics = agent.get_recent_metrics()
    assert isinstance(metrics, dict)
    assert "test_count" in metrics
    assert "plugin_count" in metrics
    assert "kb_entry_count" in metrics
