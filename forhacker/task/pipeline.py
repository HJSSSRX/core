import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from forhacker.collab.shared import write_finding
from forhacker.kb.entry import KBEntry
from forhacker.kb.store import KBStore
from forhacker.llm.backend import LLMBackend
from forhacker.task.capability import CapabilityRegistry
from forhacker.task.engine import TaskEngine
from forhacker.task.sub_agent import SubAgentContext
from forhacker.task.supervisor import SubAgentExecutor, Supervisor

logger = logging.getLogger(__name__)


@dataclass
class PipelineReport:
    status: str  # "completed" | "partial" | "failed"
    goal: str
    total_tasks: int
    completed: int
    failed: int
    findings: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class Pipeline:
    """End-to-end forensics pipeline: decompose → execute → collect findings.

    Usage:
        pipeline = Pipeline(case_dir, llm=deepseek, registry=registry)
        report = await pipeline.run("analyze memory dump for malware")
    """

    def __init__(
        self,
        case_dir: Path,
        llm: LLMBackend,
        registry: CapabilityRegistry,
        case_id: str = "default",
        max_concurrency: int = 3,
        kb: KBStore | None = None,
    ):
        self._case_dir = case_dir
        self._llm = llm
        self._registry = registry
        self._case_id = case_id
        self._max_concurrency = max_concurrency
        self._kb = kb

        self._engine = TaskEngine(case_dir=case_dir)
        self._supervisor = Supervisor(
            engine=self._engine,
            registry=registry,
            case_id=case_id,
            llm=llm,
        )
        self._executor = SubAgentExecutor(llm=llm)

    async def run(
        self, goal: str, evidence_paths: list[str] | None = None, use_llm_decompose: bool = True
    ) -> PipelineReport:
        if evidence_paths is None:
            evidence_paths = []
        findings: list[dict[str, Any]] = []
        errors: list[str] = []

        # Phase 1: Decompose
        if use_llm_decompose:
            result = await self._supervisor.decompose_with_llm(goal)
        else:
            result = self._supervisor.decompose(goal)

        if result["status"] == "error":
            return PipelineReport(
                status="failed",
                goal=goal,
                total_tasks=0,
                completed=0,
                failed=0,
                errors=[result.get("message", "Decomposition failed")],
            )

        all_tasks = self._engine.get_all_tasks()
        logger.info("Pipeline decomposed %d tasks: %s", len(all_tasks), list(all_tasks.keys()))

        # Phase 2: Execute tasks in waves (topological order)
        completed = 0
        failed = 0
        total = len(all_tasks)
        semaphore = asyncio.Semaphore(self._max_concurrency)

        while True:
            pending_contexts = self._supervisor.get_pending_contexts(evidence_paths=evidence_paths)
            if not pending_contexts:
                # No pending tasks — check if any are still running
                running = [n for n in all_tasks.values() if n.status == "running"]
                if not running:
                    break
                await asyncio.sleep(0.5)
                continue

            async def execute_one(ctx: SubAgentContext) -> None:
                async with semaphore:
                    if not self._engine.claim_task(ctx.task_id, "pipeline"):
                        return
                    try:
                        result = await self._executor.execute(ctx)
                        if result.status == "done":
                            self._engine.update_status(ctx.task_id, "done")
                            for f in result.findings:
                                write_finding(self._case_dir, ctx.task_id, f)
                                findings.append(f)
                            if self._kb:
                                self._ingest_to_kb(ctx.task_id, ctx.goal, result.findings)
                        else:
                            self._engine.update_status(ctx.task_id, "failed")
                            self._supervisor._cascade_block(ctx.task_id)
                            errors.append(f"Task {ctx.task_id} failed: {result.error}")
                    except Exception as exc:
                        self._engine.update_status(ctx.task_id, "failed")
                        self._supervisor._cascade_block(ctx.task_id)
                        errors.append(f"Task {ctx.task_id} crashed: {exc}")

            tasks = [execute_one(ctx) for ctx in pending_contexts]
            await asyncio.gather(*tasks)

        # Tally final state
        for node in all_tasks.values():
            if node.status == "done":
                completed += 1
            elif node.status == "failed":
                failed += 1

        status = "completed" if failed == 0 else ("partial" if completed > 0 else "failed")
        return PipelineReport(
            status=status,
            goal=goal,
            total_tasks=total,
            completed=completed,
            failed=failed,
            findings=findings,
            errors=errors,
        )

    def _ingest_to_kb(self, task_id: str, goal: str, findings: list[dict]) -> None:
        """Auto-ingest pipeline findings into the knowledge base."""
        assert self._kb is not None
        entry = KBEntry(
            title=f"[{self._case_id}] {goal[:80]}",
            tags=["auto-ingest", self._case_id, task_id],
            source=f"case/{self._case_id}",
            content=f"Task: {task_id}\nGoal: {goal}\n\nFindings:\n" + "\n".join(f"- {f}" for f in findings),
            confidence="medium",
        )
        self._kb.add(entry)
