from __future__ import annotations

from forhacker.security.router import IsolationRouter


def test_high_risk_requires_firecracker():
    router = IsolationRouter(kvm_available=False)
    result = router.select(task_type="malware_analysis", risk_level="HIGH")
    assert result == "BLOCKED"


def test_low_risk_uses_docker():
    router = IsolationRouter(kvm_available=False)
    result = router.select(task_type="strings", risk_level="LOW")
    assert result == "docker"


def test_unknown_risk_defaults_high():
    router = IsolationRouter(kvm_available=False)
    result = router.select(task_type="new_tool", risk_level="UNKNOWN")
    assert result == "BLOCKED"


def test_high_risk_with_kvm_uses_firecracker():
    router = IsolationRouter(kvm_available=True)
    result = router.select(task_type="malware_analysis", risk_level="HIGH")
    assert result == "firecracker"
