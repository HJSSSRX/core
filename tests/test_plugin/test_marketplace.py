from __future__ import annotations

from forhacker.plugin.marketplace import Marketplace, PluginEntry


def test_marketplace_register_and_list():
    mp = Marketplace()
    initial_count = len(mp)
    mp.register(
        PluginEntry(
            name="forensics-memory",
            version="0.1.0",
            domain="forensics",
            description="Memory forensics with Volatility 3",
            repo_url="https://github.com/forhacker/plugin-forensics-memory",
            owner_cell="plugin-forensics",
        )
    )
    plugins = mp.list_all()
    assert len(plugins) == initial_count + 1
    names = [p["name"] for p in plugins]
    assert "forensics-memory" in names


def test_marketplace_query_by_domain():
    mp = Marketplace()
    initial_forensics = len(mp.query(domain="forensics"))
    mp.register(
        PluginEntry(name="f1", version="0.1", domain="forensics", description="d", repo_url="u", owner_cell="c")
    )
    new_forensics = mp.query(domain="forensics")
    assert len(new_forensics) == initial_forensics + 1
    names = [r["name"] for r in new_forensics]
    assert "f1" in names
