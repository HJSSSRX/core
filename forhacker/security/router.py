from __future__ import annotations

class IsolationRouter:
    def __init__(self, kvm_available: bool = False):
        self._kvm_available = kvm_available

    def select(self, task_type: str, risk_level: str) -> str:
        if risk_level in ("HIGH", "UNKNOWN"):
            if self._kvm_available:
                return "firecracker"
            return "BLOCKED"
        if risk_level == "MEDIUM":
            return "docker"
        return "docker"  # LOW
