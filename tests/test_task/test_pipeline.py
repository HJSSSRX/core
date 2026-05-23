from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from typing import Any

import pytest

from forhacker.collab.shared import read_findings
from forhacker.llm.backend import LLMBackend, LLMResponse, Message
from forhacker.plugin.base import Tool
from forhacker.task.capability import CapabilityRegistry
from forhacker.task.pipeline import Pipeline


class MockLLMBackend(LLMBackend):
    """Mock backend that returns predefined YAML decomposition."""

    def __init__(self, model: str = "mock", decompose_yaml: str = ""):
        self._model = model
        self._yaml = decompose_yaml
        self.complete_calls: list[dict] = []

    @property
    def model_name(self) -> str:
        return self._model

    async def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        self.complete_calls.append({"messages": messages, "tools": tools, "kwargs": kwargs})
        if self._yaml:
            return LLMResponse(text=self._yaml, model=self._model, tokens_used=100, finish_reason="stop")
        return LLMResponse(text="No YAML configured", model=self._model, tokens_used=10, finish_reason="stop")


@pytest.fixture
def registry_with_tools():
    reg = CapabilityRegistry()
    reg.register(Tool(name="volatility3", description="Memory forensics", domain="forensics", risk_level="MEDIUM"))
    reg.register(Tool(name="bulk_extractor", description="File carving", domain="forensics", risk_level="LOW"))
    return reg


@pytest.fixture
def case_dir():
    with tempfile.TemporaryDirectory() as td:
        case_dir = Path(td) / "cases" / "test-case"
        case_dir.mkdir(parents=True)
        yield case_dir


@pytest.fixture
def decompose_yaml():
    return """```yaml
tasks:
  - task_id: memory-scan
    type: forensics
    depends_on: []
  - task_id: file-carve
    type: forensics
    depends_on: []
  - task_id: synthesize
    type: synthesis
    depends_on: [memory-scan, file-carve]
```"""


def test_pipeline_decompose_with_llm(case_dir, registry_with_tools, decompose_yaml):
    llm = MockLLMBackend(decompose_yaml=decompose_yaml)
    pipeline = Pipeline(case_dir=case_dir, llm=llm, registry=registry_with_tools, case_id="test")

    report = asyncio.run(pipeline.run("analyze memory dump", use_llm_decompose=True))

    assert report.status == "completed"
    assert report.total_tasks == 3
    assert report.completed == 3
    assert report.failed == 0
    assert len(llm.complete_calls) >= 3  # 1 decompose + 2 sub-agent analyses (synthesis skips LLM)


def test_pipeline_decompose_rule_based(case_dir, registry_with_tools):
    llm = MockLLMBackend()
    pipeline = Pipeline(case_dir=case_dir, llm=llm, registry=registry_with_tools, case_id="test")

    report = asyncio.run(pipeline.run("analyze memory", use_llm_decompose=False))

    assert report.status == "completed"
    assert report.total_tasks >= 2  # 1 domain task + synthesis
    assert report.completed >= 2


def test_pipeline_writes_findings(case_dir, registry_with_tools, decompose_yaml):
    llm = MockLLMBackend(decompose_yaml=decompose_yaml)
    pipeline = Pipeline(case_dir=case_dir, llm=llm, registry=registry_with_tools, case_id="test")

    report = asyncio.run(pipeline.run("analyze memory dump"))

    assert report.status == "completed"
    assert len(report.findings) > 0
    # Verify findings written to disk
    all_findings = []
    for task_id in ["memory-scan", "file-carve", "synthesize"]:
        all_findings.extend(read_findings(case_dir, task_id))
    assert len(all_findings) > 0


def test_pipeline_empty_registry_fails(case_dir):
    llm = MockLLMBackend()
    pipeline = Pipeline(case_dir=case_dir, llm=llm, registry=CapabilityRegistry(), case_id="test")

    report = asyncio.run(pipeline.run("analyze memory"))
    assert report.status == "failed"
    assert "No tools available" in report.errors[0]


def test_pipeline_concurrent_execution(case_dir, registry_with_tools, decompose_yaml):
    llm = MockLLMBackend(decompose_yaml=decompose_yaml)
    pipeline = Pipeline(case_dir=case_dir, llm=llm, registry=registry_with_tools, case_id="test", max_concurrency=2)

    report = asyncio.run(pipeline.run("test concurrency"))
    assert report.status == "completed"


def test_pipeline_dag_state_persisted(case_dir, registry_with_tools, decompose_yaml):
    llm = MockLLMBackend(decompose_yaml=decompose_yaml)
    pipeline = Pipeline(case_dir=case_dir, llm=llm, registry=registry_with_tools, case_id="test")

    asyncio.run(pipeline.run("test persistence"))

    dag_path = case_dir / "dag_state.yaml"
    assert dag_path.exists()
    content = dag_path.read_text()
    assert "memory-scan" in content
    assert "synthesize" in content


def test_pipeline_with_kb_ingestion(case_dir, registry_with_tools, decompose_yaml):
    from forhacker.kb.store import KBStore

    llm = MockLLMBackend(decompose_yaml=decompose_yaml)
    kb = KBStore(case_dir / "kb")
    pipeline = Pipeline(case_dir=case_dir, llm=llm, registry=registry_with_tools, case_id="test", kb=kb)

    report = asyncio.run(pipeline.run("analyze for kb"))

    assert report.status == "completed"
    # KB entries should have been auto-ingested for each task
    entries = kb.list_all()
    assert len(entries) >= 1
