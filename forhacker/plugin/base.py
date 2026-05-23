from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Tool:
    name: str
    description: str
    domain: str
    risk_level: str  # LOW | MEDIUM | HIGH
    applicable_extensions: tuple[str, ...] | None = field(default=None, compare=False)
    handler: Callable[[str], dict[str, Any]] | None = field(default=None, compare=False)


class BasePlugin(ABC):
    name: str
    version: str
    domain: str
    risk_levels: dict[str, str]  # tool_name → LOW|MEDIUM|HIGH

    @abstractmethod
    def register_tools(self) -> list[Tool]: ...
