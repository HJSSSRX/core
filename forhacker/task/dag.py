from collections import deque
from dataclasses import dataclass, field
from enum import Enum


class AddTaskResult(Enum):
    ADDED = "added"
    REJECTED_CYCLE = "rejected_cycle"
    REJECTED_DUPLICATE = "rejected_duplicate"
    REJECTED_MISSING_DEP = "rejected_missing_dep"


@dataclass
class TaskNode:
    task_id: str
    type: str
    depends_on: list[str] = field(default_factory=list)
    status: str = "pending"
    assigned_to: str | None = None
    artifacts: list[str] = field(default_factory=list)
    confidence: str = "MEDIUM"


class DAG:
    def __init__(self) -> None:
        self.tasks: dict[str, TaskNode] = {}

    def add_task(self, node: TaskNode) -> AddTaskResult:
        if node.task_id in self.tasks:
            return AddTaskResult.REJECTED_DUPLICATE
        # Self-reference is always a cycle
        if node.task_id in node.depends_on:
            return AddTaskResult.REJECTED_CYCLE
        # Validate all dependencies exist (prevents permanently stuck tasks)
        for dep in node.depends_on:
            if dep not in self.tasks:
                return AddTaskResult.REJECTED_MISSING_DEP
        # Check for cycles: temporarily add and check
        self.tasks[node.task_id] = node
        if self._has_cycle():
            del self.tasks[node.task_id]
            return AddTaskResult.REJECTED_CYCLE
        return AddTaskResult.ADDED

    def _has_cycle(self) -> bool:
        visited = set()
        rec_stack = set()

        def dfs(tid: str) -> bool:
            visited.add(tid)
            rec_stack.add(tid)
            node = self.tasks.get(tid)
            if node is not None:
                for dep in node.depends_on:
                    if dep not in self.tasks:
                        continue  # skip dangling references (validated at add time)
                    if dep not in visited:
                        if dfs(dep):
                            return True
                    elif dep in rec_stack:
                        return True
            rec_stack.discard(tid)
            return False

        for tid in self.tasks:
            if tid not in visited:
                if dfs(tid):
                    return True
        return False

    def topological_sort(self) -> list[TaskNode]:
        in_degree: dict[str, int] = {tid: 0 for tid in self.tasks}
        for tid, node in self.tasks.items():
            for dep in node.depends_on:
                if dep in in_degree:
                    in_degree[tid] += 1
        queue = deque(tid for tid, deg in in_degree.items() if deg == 0)
        result = []
        while queue:
            tid = queue.popleft()
            result.append(self.tasks[tid])
            for other_id, other_node in self.tasks.items():
                if tid in other_node.depends_on:
                    in_degree[other_id] -= 1
                    if in_degree[other_id] == 0:
                        queue.append(other_id)
        return result

    def get_ready_tasks(self) -> list[TaskNode]:
        ready = []
        for node in self.tasks.values():
            if node.status != "pending":
                continue
            deps_satisfied = all(self.tasks.get(dep) and self.tasks[dep].status == "done" for dep in node.depends_on)
            if deps_satisfied:
                ready.append(node)
        return ready
