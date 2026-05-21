import tempfile
from pathlib import Path

import pytest

from forhacker.plugin.base import Tool
from forhacker.task.capability import CapabilityRegistry
from forhacker.task.engine import TaskEngine
from forhacker.task.sub_agent import SubAgentContext
from forhacker.task.supervisor import Supervisor


@pytest.fixture
def supervisor(tmp_shared_dir):
    case_dir = tmp_shared_dir / "cases" / "test-case"
    case_dir.mkdir(parents=True)
    engine = TaskEngine(case_dir=case_dir)
    registry = CapabilityRegistry()
    registry.register(Tool(name="vol3", description="Volatility 3", domain="forensics", risk_level="MEDIUM"))
    return Supervisor(engine=engine, registry=registry, case_id="test-case")


def test_supervisor_empty_registry_returns_error():
    with tempfile.TemporaryDirectory() as td:
        case_dir = Path(td) / "cases" / "empty-case"
        case_dir.mkdir(parents=True)
        engine = TaskEngine(case_dir=case_dir)
        sv = Supervisor(engine=engine, registry=CapabilityRegistry(), case_id="empty-case")
        result = sv.decompose("analyze memory")
        assert result["status"] == "error"
        assert "No tools available" in result["message"]


def test_supervisor_decompose_creates_tasks(supervisor):
    result = supervisor.decompose("analyze memory image for malware")
    assert result["status"] == "ok"
    assert len(result["task_ids"]) > 0


def test_supervisor_get_pending_contexts(supervisor):
    supervisor.decompose("analyze memory")
    contexts = supervisor.get_pending_contexts()
    assert len(contexts) > 0
    assert isinstance(contexts[0], SubAgentContext)
    assert contexts[0].case_id == "test-case"


def test_supervisor_cascade_failure(supervisor):
    supervisor.decompose("multi-step analysis")
    # Mark one task failed
    task_ids = supervisor.engine.get_all_tasks()
    first_id = next(iter(task_ids))
    supervisor.engine.update_status(first_id, "failed")
    supervisor._cascade_block(first_id)
    # Downstream tasks should be blocked
    for tid, node in supervisor.engine.get_all_tasks().items():
        if first_id in node.depends_on:
            assert node.status == "blocked"
