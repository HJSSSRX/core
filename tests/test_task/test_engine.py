from __future__ import annotations

import pytest

from forhacker.task.dag import TaskNode
from forhacker.task.engine import TaskEngine


@pytest.fixture
def engine(tmp_shared_dir):
    case_dir = tmp_shared_dir / "cases" / "test-case"
    case_dir.mkdir(parents=True)
    return TaskEngine(case_dir=case_dir)


def test_engine_add_task(engine):
    result = engine.add_task(TaskNode(task_id="T-001", type="analysis"))
    assert result.name == "ADDED"
    assert "T-001" in engine.dag.tasks


def test_engine_persists_dag_state(engine, tmp_shared_dir):
    engine.add_task(TaskNode(task_id="T-001", type="analysis"))
    dag_file = tmp_shared_dir / "cases" / "test-case" / "dag_state.yaml"
    assert dag_file.exists()


def test_engine_loads_existing_dag(tmp_shared_dir):
    case_dir = tmp_shared_dir / "cases" / "test-case"
    case_dir.mkdir(parents=True)
    engine1 = TaskEngine(case_dir=case_dir)
    engine1.add_task(TaskNode(task_id="T-001", type="analysis"))

    engine2 = TaskEngine(case_dir=case_dir)
    assert "T-001" in engine2.dag.tasks


def test_engine_update_status_persists(tmp_shared_dir):
    case_dir = tmp_shared_dir / "cases" / "test-case"
    case_dir.mkdir(parents=True)
    engine = TaskEngine(case_dir=case_dir)
    engine.add_task(TaskNode(task_id="T-001", type="analysis"))
    engine.update_status("T-001", "running")
    # Simulate crash by creating a fresh engine
    engine2 = TaskEngine(case_dir=case_dir)
    assert engine2.dag.tasks["T-001"].status == "running"


def test_engine_claim_task_atomic(tmp_shared_dir):
    case_dir = tmp_shared_dir / "cases" / "test-case"
    case_dir.mkdir(parents=True)
    engine = TaskEngine(case_dir=case_dir)
    engine.add_task(TaskNode(task_id="T-001", type="analysis"))
    # First claim succeeds
    assert engine.claim_task("T-001", "agent-A") is True
    assert engine.dag.tasks["T-001"].assigned_to == "agent-A"
    assert engine.dag.tasks["T-001"].status == "running"
    # Second claim on already-claimed task fails
    assert engine.claim_task("T-001", "agent-B") is False


def test_engine_corrupted_yaml_recovery(tmp_shared_dir):
    case_dir = tmp_shared_dir / "cases" / "test-case"
    case_dir.mkdir(parents=True)
    (case_dir / "dag_state.yaml").write_text("{{{ bad yaml", encoding="utf-8")
    # Engine must not crash; fall back to empty DAG
    engine = TaskEngine(case_dir=case_dir)
    assert len(engine.dag.tasks) == 0
