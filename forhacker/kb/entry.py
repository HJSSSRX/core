from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass, field

import yaml


@dataclass
class KBEntry:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    title: str = ""
    tags: list[str] = field(default_factory=list)
    source: str = ""  # e.g. "case/memory-dump-001" or "cell/forensics-core"
    content: str = ""
    confidence: str = "medium"  # high | medium | low
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    source_url: str = ""

    def to_frontmatter_md(self) -> str:
        meta = {
            "id": self.id,
            "title": self.title,
            "tags": self.tags,
            "source": self.source,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "source_url": self.source_url or None,
        }
        meta_str = yaml.dump({k: v for k, v in meta.items() if v is not None}, allow_unicode=True)
        return f"---\n{meta_str}---\n\n{self.content}\n"

    @classmethod
    def from_frontmatter_md(cls, text: str) -> "KBEntry":
        if not text.startswith("---"):
            return cls(content=text.strip())
        parts = text.split("---", 2)
        if len(parts) < 3:
            return cls(content=text.strip())
        meta = yaml.safe_load(parts[1]) or {}
        return cls(
            id=meta.get("id", ""),
            title=meta.get("title", ""),
            tags=meta.get("tags", []),
            source=meta.get("source", ""),
            confidence=meta.get("confidence", "medium"),
            created_at=meta.get("created_at", ""),
            source_url=meta.get("source_url", ""),
            content=parts[2].strip(),
        )
