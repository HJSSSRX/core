from forhacker.kb.entry import KBEntry


def test_entry_to_frontmatter_md():
    entry = KBEntry(
        id="abc123",
        title="Test Entry",
        tags=["forensics", "memory"],
        source="case/test",
        content="Analysis findings here.",
        confidence="high",
    )
    md = entry.to_frontmatter_md()
    assert md.startswith("---")
    assert "Test Entry" in md
    assert "forensics" in md
    assert "Analysis findings here." in md
    assert md.endswith("\n")


def test_entry_from_frontmatter_md():
    md = """---
id: test001
title: Memory Analysis
tags: [forensics, memory]
source: case/memdump
confidence: high
created_at: "2026-01-01T00:00:00"
---
Found suspicious process at PID 1234."""
    entry = KBEntry.from_frontmatter_md(md)
    assert entry.id == "test001"
    assert entry.title == "Memory Analysis"
    assert entry.tags == ["forensics", "memory"]
    assert entry.source == "case/memdump"
    assert entry.confidence == "high"
    assert "PID 1234" in entry.content


def test_from_frontmatter_no_yaml():
    entry = KBEntry.from_frontmatter_md("Just plain text content.")
    assert entry.content == "Just plain text content."
    assert entry.title == ""


def test_from_frontmatter_empty():
    entry = KBEntry.from_frontmatter_md("")
    assert entry.content == ""


def test_entry_roundtrip():
    original = KBEntry(title="Roundtrip", tags=["test"], source="unittest", content="Roundtrip content")
    md = original.to_frontmatter_md()
    restored = KBEntry.from_frontmatter_md(md)
    assert restored.title == original.title
    assert restored.tags == original.tags
    assert restored.content == original.content
