from forhacker.task.engine import TaskEngine
from forhacker.task.capability import CapabilityRegistry
from forhacker.task.dag import TaskNode
from forhacker.task.sub_agent import SubAgentContext


class Supervisor:
    def __init__(self, engine: TaskEngine, registry: CapabilityRegistry, case_id: str):
        self.engine = engine
        self.registry = registry
        self.case_id = case_id

    def decompose(self, goal: str) -> dict:
        domains = self.registry.list_domains()
        if not domains:
            return {"status": "error", "message": "No tools available for any domain. Register plugins first."}

        # Simple decomposition: one task per relevant domain + a synthesis task
        task_ids = []
        for i, domain in enumerate(domains):
            tid = f"T-{i:03d}"
            node = TaskNode(task_id=tid, type=f"{domain}_analysis", depends_on=[])
            self.engine.add_task(node)
            task_ids.append(tid)

        # Synthesis task depends on all domain tasks
        syn_tid = f"T-{len(task_ids):03d}"
        syn_node = TaskNode(task_id=syn_tid, type="synthesis", depends_on=list(task_ids))
        self.engine.add_task(syn_node)
        task_ids.append(syn_tid)

        return {"status": "ok", "task_ids": task_ids, "goal": goal}

    def get_pending_contexts(self) -> list[SubAgentContext]:
        ready = self.engine.get_ready_tasks()
        contexts = []
        for node in ready:
            tools = self.registry.query(domain=node.type.split("_")[0])
            ctx = SubAgentContext(
                task_id=node.task_id,
                case_id=self.case_id,
                goal=node.type,
                evidence_paths=[],
                available_tools=tools,
                dependency_findings=[],
            )
            contexts.append(ctx)
        return contexts

    def _cascade_block(self, failed_task_id: str):
        # Intentionally private: only called internally after task failure detection.
        # Public API is engine.get_ready_tasks() which naturally excludes blocked nodes.
        for _, node in self.engine.get_all_tasks().items():
            if failed_task_id in node.depends_on and node.status == "pending":
                node.status = "blocked"
        self.engine._write_through()
