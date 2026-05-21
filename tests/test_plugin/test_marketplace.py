from forhacker.plugin.marketplace import Marketplace, PluginEntry


def test_marketplace_register_and_list():
    mp = Marketplace()
    mp.register(PluginEntry(
        name="forensics-memory",
        version="0.1.0",
        domain="forensics",
        description="Memory forensics with Volatility 3",
        repo_url="https://github.com/forhacker/plugin-forensics-memory",
        owner_cell="plugin-forensics",
    ))
    plugins = mp.list_all()
    assert len(plugins) == 1
    assert plugins[0]["name"] == "forensics-memory"


def test_marketplace_query_by_domain():
    mp = Marketplace()
    mp.register(PluginEntry(name="f1", version="0.1", domain="forensics", description="d", repo_url="u", owner_cell="c"))
    mp.register(PluginEntry(name="p1", version="0.1", domain="pentest", description="d", repo_url="u", owner_cell="c"))
    results = mp.query(domain="pentest")
    assert len(results) == 1
    assert results[0]["name"] == "p1"
