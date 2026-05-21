import os
from pathlib import Path

from forhacker.kb.entry import KBEntry


class KBStore:
    """File-system based knowledge base using Markdown + YAML frontmatter files."""

    def __init__(self, kb_dir: Path):
        self._dir = kb_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    @property
    def path(self) -> Path:
        return self._dir

    def add(self, entry: KBEntry) -> Path:
        filename = f"{entry.id}.md"
        filepath = self._dir / filename
        self._write_atomic(filepath, entry.to_frontmatter_md())
        return filepath

    def get(self, entry_id: str) -> KBEntry | None:
        filepath = self._dir / f"{entry_id}.md"
        if not filepath.exists():
            return None
        return KBEntry.from_frontmatter_md(filepath.read_text(encoding="utf-8"))

    def list_all(self) -> list[KBEntry]:
        entries = []
        for p in sorted(self._dir.glob("*.md")):
            entry = KBEntry.from_frontmatter_md(p.read_text(encoding="utf-8"))
            entries.append(entry)
        return entries

    def delete(self, entry_id: str) -> bool:
        filepath = self._dir / f"{entry_id}.md"
        if not filepath.exists():
            return False
        filepath.unlink()
        return True

    def search(self, keyword: str = "", tags: list[str] | None = None) -> list[KBEntry]:
        results = []
        kw_lower = keyword.lower()
        for entry in self.list_all():
            if tags and not any(t in entry.tags for t in tags):
                continue
            if kw_lower:
                in_title = kw_lower in entry.title.lower()
                in_content = kw_lower in entry.content.lower()
                in_tags = any(kw_lower in t.lower() for t in entry.tags)
                if not (in_title or in_content or in_tags):
                    continue
            results.append(entry)
        return results

    @staticmethod
    def _write_atomic(filepath: Path, content: str) -> None:
        tmp = filepath.with_suffix(".tmp")
        tmp.write_text(content, encoding="utf-8")
        os.replace(tmp, filepath)
