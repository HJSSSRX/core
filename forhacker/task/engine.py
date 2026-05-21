import os
from pathlib import Path
import yaml
from forhacker.task.dag import DAG, TaskNode, AddTaskResult


class TaskEngine:
    def __init__(self, case_dir: Path):
        self._case_dir = case_dir
        self._dag_path = case_dir / "dag_state.yaml"
        self._dag = self._load_or_create()

    @property
    def dag(self) -> DAG:
        """Read-only access to the DAG. Mutate via engine methods, not through this property."""
        return self._dag

    def get_ready_tasks(self) -> list[TaskNode]:
        """Return tasks whose dependencies are all done."""
        return self._dag.get_ready_tasks()

    def get_all_tasks(self) -> dict[str, TaskNode]:
        """Return all tasks keyed by task_id."""
        return dict(self._dag.tasks)

    def _load_or_create(self) -> DAG:
        dag = DAG()
        if self._dag_path.exists():
            try:
                data = yaml.safe_load(self._dag_path.read_text(encoding="utf-8")) or {}
            except yaml.YAMLError:
                import logging
                logging.getLogger(__name__).warning(
                    "Corrupted dag_state.yaml at %s, falling back to empty DAG", self._dag_path
                )
                return dag
            for task_data in data.get("tasks", []):
                node = TaskNode(
                    task_id=task_data["task_id"],
                    type=task_data["type"],
                    depends_on=task_data.get("depends_on", []),
                    status=task_data.get("status", "pending"),
                    assigned_to=task_data.get("assigned_to"),
                    confidence=task_data.get("confidence", "MEDIUM"),
                    artifacts=task_data.get("artifacts", []),
                )
                dag.tasks[node.task_id] = node
            # Validate acyclicity on load (YAML hand-edits or bugs)
            if dag._has_cycle():
                raise RuntimeError("Loaded dag_state.yaml contains a cycle — refusing to proceed")
        return dag

    def add_task(self, node: TaskNode) -> AddTaskResult:
        result = self._dag.add_task(node)
        if result == AddTaskResult.ADDED:
            self._write_through()
        return result

    def update_status(self, task_id: str, new_status: str) -> None:
        """Atomically update task status AND persist to disk."""
        if task_id not in self._dag.tasks:
            raise KeyError(f"Task {task_id} not found")
        self._dag.tasks[task_id].status = new_status
        self._write_through()

    def claim_task(self, task_id: str, claimant_id: str) -> bool:
        """Atomically claim a pending task for execution. Returns False if already claimed."""
        node = self._dag.tasks.get(task_id)
        if node is None or node.status != "pending":
            return False
        node.status = "running"
        node.assigned_to = claimant_id
        self._write_through()
        return True

    def _write_through(self):
        tasks_data = []
        for node in self._dag.tasks.values():
            tasks_data.append({
                "task_id": node.task_id,
                "type": node.type,
                "depends_on": node.depends_on,
                "status": node.status,
                "assigned_to": node.assigned_to,
                "confidence": node.confidence,
                "artifacts": node.artifacts,
            })
        payload = yaml.dump({"schema_version": 1, "tasks": tasks_data}, allow_unicode=True)
        # Atomic write: temp file + rename
        tmp_path = self._dag_path.with_suffix(".tmp")
        tmp_path.write_text(payload, encoding="utf-8")
        os.replace(tmp_path, self._dag_path)
