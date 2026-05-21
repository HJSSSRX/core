from forhacker.llm.backend import LLMBackend, Message
from forhacker.task.capability import CapabilityRegistry
from forhacker.task.dag import TaskNode
from forhacker.task.engine import TaskEngine
from forhacker.task.sub_agent import SubAgentContext, SubAgentResult

DECOMPOSE_PROMPT = """You are a forensics task planner. Decompose the given goal into a task DAG.

Available domains and their tools:
{tools_summary}

Goal: {goal}

Output YAML list of tasks. Each task has:
- task_id: short kebab-case id (e.g. "memory-acquisition")
- type: one of {domains}
- depends_on: list of task_ids that must complete first

Return ONLY the YAML, no other text. Example:
```yaml
tasks:
  - task_id: acquire-memory
    type: forensics
    depends_on: []
  - task_id: synthesize
    type: synthesis
    depends_on: [acquire-memory]
```"""


class SubAgentExecutor:
    """Executes a SubAgentContext by calling tools and optionally using an LLM for reasoning."""

    def __init__(self, llm: LLMBackend | None = None):
        self._llm = llm

    async def execute(self, ctx: SubAgentContext) -> SubAgentResult:
        findings: list[dict] = []
        artifacts: list[str] = []

        for tool in ctx.available_tools:
            if self._llm is not None:
                result = await self._run_with_llm(tool, ctx)
            else:
                result = {"tool": tool.name, "status": "no_llm_available", "output": None}
            findings.append({"tool": tool.name, "domain": tool.domain, "result": result})
            artifacts.append(f"finding/{tool.name}.yaml")

        return SubAgentResult(
            findings=findings,
            confidence="MEDIUM",
            artifacts=artifacts,
            status="done",
        )

    async def _run_with_llm(self, tool: object, ctx: SubAgentContext) -> dict:
        prompt = (
            f"You are using the tool '{getattr(tool, 'name', 'unknown')}' "
            f"({getattr(tool, 'description', '')}) in domain '{getattr(tool, 'domain', '')}'.\n"
            f"Task goal: {ctx.goal}\n"
            f"Evidence paths: {ctx.evidence_paths}\n"
            f"Previous findings: {ctx.dependency_findings}\n\n"
            f"Describe what analysis you would perform using this tool and what results you expect."
        )
        assert self._llm is not None
        response = await self._llm.complete([Message(role="user", content=prompt)])
        return {"tool": getattr(tool, 'name', ''), "analysis": response.text, "model": response.model}


class Supervisor:
    """Task decomposition and dispatch. Optionally uses an LLM for smarter planning."""

    def __init__(self, engine: TaskEngine, registry: CapabilityRegistry, case_id: str,
                 llm: LLMBackend | None = None):
        self.engine = engine
        self.registry = registry
        self.case_id = case_id
        self._llm = llm

    def decompose(self, goal: str) -> dict:
        domains = self.registry.list_domains()
        if not domains:
            return {"status": "error", "message": "No tools available for any domain. Register plugins first."}

        task_ids = []
        for i, domain in enumerate(domains):
            tid = f"T-{i:03d}"
            node = TaskNode(task_id=tid, type=f"{domain}_analysis", depends_on=[])
            self.engine.add_task(node)
            task_ids.append(tid)

        syn_tid = f"T-{len(task_ids):03d}"
        syn_node = TaskNode(task_id=syn_tid, type="synthesis", depends_on=list(task_ids))
        self.engine.add_task(syn_node)
        task_ids.append(syn_tid)

        return {"status": "ok", "task_ids": task_ids, "goal": goal}

    async def decompose_with_llm(self, goal: str) -> dict:
        domains = self.registry.list_domains()
        if not domains:
            return {"status": "error", "message": "No tools available. Register plugins first."}
        if self._llm is None:
            return self.decompose(goal)

        tools_summary = "\n".join(
            f"- {d}: {[t.name for t in self.registry.query(d)]}" for d in domains
        )
        prompt = DECOMPOSE_PROMPT.format(tools_summary=tools_summary, goal=goal, domains=domains)
        response = await self._llm.complete([Message(role="user", content=prompt)])

        import yaml
        try:
            text = response.text
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("yaml"):
                    text = text[4:]
            data = yaml.safe_load(text)
            task_ids = []
            for t in data.get("tasks", []):
                node = TaskNode(
                    task_id=t["task_id"],
                    type=t.get("type", "analysis"),
                    depends_on=t.get("depends_on", []),
                )
                result = self.engine.add_task(node)
                if result.name.startswith("ADDED"):
                    task_ids.append(t["task_id"])
            return {"status": "ok", "task_ids": task_ids, "goal": goal, "llm_model": response.model}
        except Exception as e:
            return {"status": "error", "message": f"LLM decomposition failed: {e}"}

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
        for _, node in self.engine.get_all_tasks().items():
            if failed_task_id in node.depends_on and node.status == "pending":
                node.status = "blocked"
        self.engine._write_through()
