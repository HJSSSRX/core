from dataclasses import dataclass


@dataclass
class Source:
    name: str
    url: str
    category: str  # github | papers | chinese | official
    check_interval_hours: int = 24


DEFAULT_SOURCES = [
    Source(name="github-trending", url="https://github.com/trending", category="github", check_interval_hours=24),
    Source(name="arxiv-cs-cr", url="https://arxiv.org/list/cs.CR/recent", category="papers", check_interval_hours=168),
    Source(name="arxiv-cs-ai", url="https://arxiv.org/list/cs.AI/recent", category="papers", check_interval_hours=168),
    Source(name="freebuf", url="https://www.freebuf.com/", category="chinese", check_interval_hours=24),
    Source(name="claude-code-releases", url="https://github.com/anthropics/claude-code/releases", category="official", check_interval_hours=24),
]
