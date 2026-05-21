from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from forhacker.plugin.base import Tool


class SubAgentLifecycle(Enum):
    INIT = "initialized"
    EXECUTING = "executing"
    REPORTING = "reporting"
    DONE = "done"
    FAILED = "failed"


@dataclass(slots=True)
class SubAgentContext:
    task_id: str
    case_id: str
    goal: str
    evidence_paths: list[str]
    available_tools: list[Tool]
    dependency_findings: list[dict[str, Any]] = field(default_factory=list)
    config: dict = field(default_factory=dict)


@dataclass(slots=True)
class SubAgentResult:
    findings: list[dict[str, Any]]
    confidence: str  # HIGH | MEDIUM | LOW (task_confidence)
    artifacts: list[str]
    status: str  # "done" | "failed"
    error: str | None = None
