from forhacker.task.sub_agent import SubAgentContext, SubAgentResult, SubAgentLifecycle
from forhacker.plugin.base import Tool


def test_sub_agent_context_fields():
    ctx = SubAgentContext(
        task_id="T-001",
        case_id="case-1",
        goal="analyze memory",
        evidence_paths=["/data/memory.dmp"],
        available_tools=[Tool(name="vol3", description="Volatility 3", domain="forensics", risk_level="MEDIUM")],
        dependency_findings=[],
        config={},
    )
    assert ctx.task_id == "T-001"
    assert len(ctx.available_tools) == 1
    assert ctx.dependency_findings == []


def test_sub_agent_result_done():
    result = SubAgentResult(
        findings=[],
        confidence="HIGH",
        artifacts=["/output/report.md"],
        status="done",
        error=None,
    )
    assert result.status == "done"
    assert result.confidence == "HIGH"


def test_sub_agent_result_failed():
    result = SubAgentResult(
        findings=[],
        confidence="LOW",
        artifacts=[],
        status="failed",
        error="tool timeout",
    )
    assert result.status == "failed"
    assert result.error == "tool timeout"


def test_sub_agent_lifecycle_states():
    states = list(SubAgentLifecycle)
    assert SubAgentLifecycle.INIT in states
    assert SubAgentLifecycle.EXECUTING in states
    assert SubAgentLifecycle.REPORTING in states
    assert SubAgentLifecycle.DONE in states
    assert SubAgentLifecycle.FAILED in states
