from forhacker.kb.entry import KBEntry
from forhacker.kb.store import KBStore


def test_add_and_get(tmp_path):
    kb_dir = tmp_path / "kb"
    store = KBStore(kb_dir)
    entry = KBEntry(title="Test", tags=["test"], source="unittest", content="Hello world")
    path = store.add(entry)
    assert path.exists()
    assert path.suffix == ".md"

    retrieved = store.get(entry.id)
    assert retrieved is not None
    assert retrieved.title == "Test"
    assert retrieved.content == "Hello world"


def test_get_nonexistent(tmp_path):
    store = KBStore(tmp_path / "kb")
    assert store.get("nonexistent") is None


def test_list_all(tmp_path):
    store = KBStore(tmp_path / "kb")
    store.add(KBEntry(title="A", tags=["a"], source="test", content="aaa"))
    store.add(KBEntry(title="B", tags=["b"], source="test", content="bbb"))
    entries = store.list_all()
    assert len(entries) == 2


def test_delete(tmp_path):
    store = KBStore(tmp_path / "kb")
    entry = KBEntry(title="Del", tags=["test"], source="test", content="xxx")
    store.add(entry)
    assert store.delete(entry.id) is True
    assert store.get(entry.id) is None
    assert store.delete("nonexistent") is False


def test_search_by_keyword(tmp_path):
    store = KBStore(tmp_path / "kb")
    store.add(KBEntry(title="Memory Dump", tags=["forensics"], source="case/1", content="Found malware"))
    store.add(KBEntry(title="Network Log", tags=["network"], source="case/2", content="Suspicious DNS"))
    results = store.search(keyword="malware")
    assert len(results) == 1
    assert results[0].title == "Memory Dump"


def test_search_by_tag(tmp_path):
    store = KBStore(tmp_path / "kb")
    store.add(KBEntry(title="Mem", tags=["forensics", "memory"], source="case/1", content="..."))
    store.add(KBEntry(title="DNS", tags=["network"], source="case/2", content="..."))
    results = store.search(tags=["forensics"])
    assert len(results) == 1
    assert results[0].title == "Mem"


def test_search_combined(tmp_path):
    store = KBStore(tmp_path / "kb")
    store.add(KBEntry(title="Malware", tags=["forensics", "malware"], source="case/1", content="trojan found"))
    store.add(KBEntry(title="Clean", tags=["forensics"], source="case/2", content="no issues"))
    results = store.search(keyword="trojan", tags=["forensics"])
    assert len(results) == 1
    assert results[0].title == "Malware"


def test_search_empty_store(tmp_path):
    store = KBStore(tmp_path / "kb")
    assert store.search(keyword="anything") == []


def test_list_empty_store(tmp_path):
    store = KBStore(tmp_path / "kb")
    assert store.list_all() == []
