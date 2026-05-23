from __future__ import annotations

from forhacker.task.dag import DAG, AddTaskResult, TaskNode


def make_node(task_id: str, deps: list[str] | None = None) -> TaskNode:
    return TaskNode(task_id=task_id, type="analysis", depends_on=deps or [])


def test_add_root_task():
    dag = DAG()
    result = dag.add_task(make_node("T-001"))
    assert result == AddTaskResult.ADDED
    assert len(dag.tasks) == 1


def test_add_child_task():
    dag = DAG()
    dag.add_task(make_node("T-001"))
    result = dag.add_task(make_node("T-002", deps=["T-001"]))
    assert result == AddTaskResult.ADDED


def test_reject_cycle():
    dag = DAG()
    dag.add_task(make_node("T-001"))
    # Self-referencing creates a cycle
    result = dag.add_task(make_node("T-002", deps=["T-002"]))
    assert result == AddTaskResult.REJECTED_CYCLE


def test_reject_missing_dep():
    dag = DAG()
    result = dag.add_task(make_node("T-001", deps=["NONEXISTENT"]))
    assert result == AddTaskResult.REJECTED_MISSING_DEP


def test_reject_duplicate():
    dag = DAG()
    dag.add_task(make_node("T-001"))
    result = dag.add_task(make_node("T-001"))
    assert result == AddTaskResult.REJECTED_DUPLICATE


def test_topological_sort():
    dag = DAG()
    dag.add_task(make_node("T-000"))
    dag.add_task(make_node("T-001", deps=["T-000"]))
    dag.add_task(make_node("T-002", deps=["T-001"]))
    order = dag.topological_sort()
    ids = [t.task_id for t in order]
    assert ids.index("T-000") < ids.index("T-001") < ids.index("T-002")


def test_get_ready_tasks():
    dag = DAG()
    dag.add_task(make_node("T-000"))
    dag.add_task(make_node("T-001", deps=["T-000"]))
    dag.tasks["T-000"].status = "done"
    ready = dag.get_ready_tasks()
    assert len(ready) == 1
    assert ready[0].task_id == "T-001"
