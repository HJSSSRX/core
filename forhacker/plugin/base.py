from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class Tool:
    name: str
    description: str
    domain: str
    risk_level: str  # LOW | MEDIUM | HIGH


class BasePlugin(ABC):
    name: str
    version: str
    domain: str
    risk_levels: dict[str, str]  # tool_name → LOW|MEDIUM|HIGH

    @abstractmethod
    def register_tools(self) -> list[Tool]:
        ...
