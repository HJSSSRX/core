import logging

from forhacker.llm.backend import LLMBackend, Message
from forhacker.task.capability import CapabilityRegistry
from forhacker.task.dag import TaskNode
from forhacker.task.engine import TaskEngine
from forhacker.task.sub_agent import SubAgentContext, SubAgentResult

logger = logging.getLogger(__name__)

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

INTERPRET_PROMPT = """You are a digital forensics analyst. Interpret the tool execution results.

Task: {task_id} / Goal: {goal}
Evidence: {evidence_paths}
Previous: {dependency_findings}

Tool results:
{tool_results}

For each finding: what was discovered (cite tool output), why it matters forensically.
Confidence: verified (tool output proves it) | inferred (reasonable) | unknown (insufficient data).
Be concise."""


class SubAgentExecutor:
    """Executes a SubAgentContext: runs tool functions, then optionally interprets with LLM.

    Flow:
    1. Execute all tools with handlers, collecting raw output
    2. If LLM is available, send raw output to LLM for forensic interpretation
    3. Return findings with both raw tool data and (optionally) LLM interpretation
    """

    def __init__(self, llm: LLMBackend | None = None):
        self._llm = llm

    async def execute(self, ctx: SubAgentContext) -> SubAgentResult:
        if ctx.goal == "synthesis":
            return self._synthesize(ctx)

        if not ctx.available_tools:
            return SubAgentResult(
                findings=[{"error": "No tools available for this task"}],
                confidence="LOW", artifacts=[], status="failed", error="No tools available",
            )

        # Phase 1: Execute tool functions with real I/O
        tool_results: list[dict] = []
        for tool in ctx.available_tools:
            result = self._run_tool(tool, ctx.evidence_paths)
            tool_results.append(result)

        succeeded = sum(1 for r in tool_results if r.get("status") == "ok")
        tool_names_run = [r["tool"] for r in tool_results]

        # Phase 2: LLM interpretation of raw results
        llm_interpretation = None
        if self._llm is not None:
            try:
                llm_interpretation = await self._interpret_with_llm(ctx, tool_results)
            except Exception as e:
                logger.warning("LLM interpretation failed for %s: %s", ctx.task_id, e)

        finding: dict = {
            "task_id": ctx.task_id,
            "goal": ctx.goal,
            "tools_executed": tool_names_run,
            "tool_results": tool_results,
        }
        if llm_interpretation:
            finding["llm_interpretation"] = llm_interpretation

        return SubAgentResult(
            findings=[finding],
            confidence="MEDIUM" if succeeded > 0 else "LOW",
            artifacts=[f"finding/{ctx.task_id}.yaml"],
            status="done",
        )

    def _run_tool(self, tool, evidence_paths: list[str]) -> dict:
        """Execute a single tool's handler function with evidence input."""
        result: dict = {"tool": tool.name}
        if tool.handler is None:
            result["status"] = "no_handler"
            result["note"] = f"No handler function for tool '{tool.name}'"
            return result
        target = evidence_paths[0] if evidence_paths else ""
        try:
            output = tool.handler(target)
            result["status"] = "ok"
            result["output"] = output
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        return result

    def _synthesize(self, ctx: SubAgentContext) -> SubAgentResult:
        dep_summaries = []
        for f in ctx.dependency_findings:
            if isinstance(f, dict):
                dep_summaries.append({
                    "task_id": f.get("task_id", ""),
                    "tools_used": f.get("tools_executed", []),
                    "has_llm": "llm_interpretation" in f,
                })
        return SubAgentResult(
            findings=[{
                "task_id": ctx.task_id,
                "type": "synthesis",
                "upstream_tasks": dep_summaries,
                "summary": f"Aggregated {len(ctx.dependency_findings)} upstream findings.",
            }],
            confidence="MEDIUM",
            artifacts=[f"finding/{ctx.task_id}.yaml"],
            status="done",
        )

    async def _interpret_with_llm(self, ctx: SubAgentContext, tool_results: list[dict]) -> dict:
        assert self._llm is not None
        results_text = "\n\n".join(
            f"Tool: {r['tool']}\nStatus: {r.get('status')}\nOutput: {r.get('output', r.get('error', r.get('note')))}"
            for r in tool_results
        )
        prompt = INTERPRET_PROMPT.format(
            task_id=ctx.task_id,
            goal=ctx.goal,
            evidence_paths=", ".join(ctx.evidence_paths) if ctx.evidence_paths else "none",
            dependency_findings=ctx.dependency_findings or "none",
            tool_results=results_text,
        )
        response = await self._llm.complete([Message(role="user", content=prompt)])
        return {"model": response.model, "text": response.text}


class Supervisor:
    """Task decomposition and dispatch. Optionally uses an LLM for smarter planning."""

    def __init__(self, engine: TaskEngine, registry: CapabilityRegistry, case_id: str, llm: LLMBackend | None = None):
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

        tools_summary = "\n".join(f"- {d}: {[t.name for t in self.registry.query(d)]}" for d in domains)
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

    def get_pending_contexts(self, evidence_paths: list[str] | None = None) -> list[SubAgentContext]:
        if evidence_paths is None:
            evidence_paths = []
        ready = self.engine.get_ready_tasks()
        contexts = []
        for node in ready:
            if node.type == "synthesis":
                tools = []  # synthesis aggregates findings, no tools needed
            else:
                tools = self.registry.query(domain=node.type.split("_")[0])
            ctx = SubAgentContext(
                task_id=node.task_id,
                case_id=self.case_id,
                goal=node.type,
                evidence_paths=list(evidence_paths),
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
