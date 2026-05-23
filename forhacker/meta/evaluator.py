from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass
class Proposal:
    title: str
    what: str
    why: str
    impact: str
    risk: str  # LOW | MEDIUM | HIGH
    requires_coordination: bool
    relevance_score: float
    quality_score: float


class Evaluator:
    def __init__(self, relevance_threshold: float = 0.6, quality_threshold: float = 0.6):
        self.relevance_threshold = relevance_threshold
        self.quality_threshold = quality_threshold
        self._daily_history: deque[dict] = deque(maxlen=7)

    def passes(self, proposal: Proposal) -> bool:
        return proposal.relevance_score >= self.relevance_threshold and proposal.quality_score >= self.quality_threshold

    def record_day(self, candidates: int, passed: int):
        self._daily_history.append({"candidates": candidates, "passed": passed})

    def should_alert(self) -> bool:
        if len(self._daily_history) < 7:
            return False
        return all(day["candidates"] > 0 and day["passed"] == 0 for day in self._daily_history)
