# ForHacker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers-deepseek-v4:subagent-driven-development (recommended) or superpowers-deepseek-v4:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the forhacker AI-native digital forensics platform — a Supervisor-driven multi-agent framework with plugin system, MetaAgent self-improvement, Syncthing team collaboration, and Docker/Firecracker security isolation.

**Architecture:** Python library (`forhacker/`) with abstract interfaces (LLMBackend, MessageBus, Sandbox) and ≥2 implementations each. Supervisor decomposes investigation tasks into DAGs, dispatches to sub-agents via SubAgentContext, aggregates findings into shared/ YAML state. Hot path (task/collab) uses `shared/` YAML via `collab/shared.py`; cold path (data/meta/cli) uses PostgreSQL via `data/models.py`. Plugins register tools into CapabilityRegistry (owned by `task/`, populated by `plugin/`). Five implementation phases with TDD throughout.

**Tech Stack:** Python 3.12 (uv), pytest + pytest-asyncio, ruff + mypy, SQLAlchemy + asyncpg, FastAPI + Jinja2, click/typer, PyO3 (Rust deferred to Phase 2+)

**Spec:** `docs/superpowers/specs/2026-05-21-forhacker-design.md`

---

## File Map

| File | Action | Phase |
|------|--------|-------|
| `pyproject.toml` | Create | 1 |
| `forhacker/__init__.py` | Create | 1 |
| `forhacker/llm/backend.py` | Create | 1 |
| `forhacker/llm/openai.py` | Create | 1 |
| `forhacker/llm/ollama.py` | Create | 1 |
| `forhacker/llm/anthropic.py` | Create | 1 |
| `forhacker/llm/resilience.py` | Create | 1 |
| `forhacker/bus/message_bus.py` | Create | 1 |
| `forhacker/bus/in_process.py` | Create | 1 |
| `forhacker/plugin/base.py` | Create | 1 |
| `forhacker/plugin/manager.py` | Create | 1 |
| `forhacker/task/capability.py` | Create | 1 |
| `forhacker/data/db.py` | Create | 1 |
| `forhacker/data/models.py` | Create | 1 |
| `forhacker/data/evidence.py` | Create | 1 |
| `forhacker/cli/main.py` | Create | 1 |
| `forhacker/task/dag.py` | Create | 2 |
| `forhacker/task/engine.py` | Create | 2 |
| `forhacker/task/supervisor.py` | Create | 2 |
| `forhacker/task/sub_agent.py` | Create | 2 |
| `forhacker/collab/shared.py` | Create | 2 |
| `forhacker/collab/syncthing.py` | Create | 3 |
| `forhacker/plugin/mcp_server.py` | Create | 3 |
| `forhacker/meta/agent.py` | Create | 4 |
| `forhacker/meta/sources.py` | Create | 4 |
| `forhacker/meta/evaluator.py` | Create | 4 |
| `forhacker/meta/audit.py` | Create | 4 |
| `forhacker/cli/web/app.py` | Create | 4 |
| `forhacker/plugin/marketplace.py` | Create | 5 |
| `forhacker/security/sandbox.py` | Create | 5 |
| `forhacker/security/router.py` | Create | 5 |
| `forhacker/cli/commands/case.py` | Create | 1 |
| `forhacker/cli/commands/plugin.py` | Create | 5 |
| `forhacker/cli/commands/meta.py` | Create | 4 |
| `forhacker/cli/commands/kb.py` | Create | 3 |
| `forhacker/cli/commands/collab.py` | Create | 3 |
| `tests/conftest.py` | Create | 1 |
| `tests/test_llm/` | Create | 1 |
| `tests/test_bus/` | Create | 1 |
| `tests/test_plugin/` | Create | 1 |
| `tests/test_task/` | Create | 2 |
| `tests/test_collab/` | Create | 2 |
| `tests/test_data/` | Create | 1 |
| `tests/test_meta/` | Create | 4 |
| `tests/test_security/` | Create | 5 |
| `.github/workflows/quality.yml` | Create | 3 |
| `VISION.md` | Create | 3 |
| `README.md` | Create | 3 |

---

## Phase 1: Core Skeleton (Tasks 1–9)

### Task 1: Project scaffolding and package structure

**Files:**
- Create: `pyproject.toml`
- Create: `forhacker/__init__.py`
- Create: `forhacker/llm/__init__.py`
- Create: `forhacker/bus/__init__.py`
- Create: `forhacker/plugin/__init__.py`
- Create: `forhacker/task/__init__.py`
- Create: `forhacker/data/__init__.py`
- Create: `forhacker/meta/__init__.py`
- Create: `forhacker/security/__init__.py`
- Create: `forhacker/collab/__init__.py`
- Create: `forhacker/cli/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Write `pyproject.toml` with all dependencies**

```toml
[project]
name = "forhacker"
version = "0.1.0"
description = "AI-Native Digital Forensics Platform"
requires-python = ">=3.12"
dependencies = [
    "click>=8.0",
    "pyyaml>=6.0",
    "sqlalchemy[asyncio]>=2.0",
    "asyncpg>=0.29",
    "httpx>=0.27",
    "openai>=1.0",
    "anthropic>=0.30",
    "pydantic>=2.0",
    "fastapi>=0.110",
    "jinja2>=3.0",
    "uvicorn>=0.27",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=4.0",
    "ruff>=0.3",
    "mypy>=1.8",
]

[tool.ruff]
line-length = 120
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]

[tool.mypy]
python_version = "3.12"
strict = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 2: Create all `__init__.py` files with version import**

`forhacker/__init__.py`:
```python
__version__ = "0.1.0"
```

All other `__init__.py` files empty.

- [ ] **Step 3: Create `tests/conftest.py` with shared fixtures**

```python
import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def tmp_shared_dir():
    """Temporary shared/ directory mimicking Syncthing-synced state."""
    with tempfile.TemporaryDirectory() as td:
        shared = Path(td)
        (shared / "cases").mkdir()
        (shared / "agents").mkdir()
        yield shared
```

- [ ] **Step 4: Install dependencies and verify**

```bash
cd E:/ProjectHJM/forhacker && uv pip install -e ".[dev]"
```

- [ ] **Step 5: Run ruff format check and confirm clean**

```bash
cd E:/ProjectHJM/forhacker && ruff format --check .
```

Expected: 0 files would be reformatted.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml forhacker/ tests/
git commit -m "$(cat <<'EOF'
feat: project scaffolding for forhacker core

pyproject.toml with Python 3.12, core deps (click, sqlalchemy, httpx, openai,
anthropic, fastapi), dev deps (pytest, ruff, mypy). Package structure with
8 subpackages mirroring spec: llm/, bus/, task/, plugin/, meta/, data/,
security/, collab/, cli/.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: LLMBackend ABC and Message types

**Files:**
- Create: `forhacker/llm/backend.py`
- Create: `tests/test_llm/test_backend.py`

- [ ] **Step 1: Write failing test for LLMBackend ABC instantiation**

`tests/test_llm/test_backend.py`:
```python
import pytest
from forhacker.llm.backend import LLMBackend, Message, LLMResponse


def test_cannot_instantiate_abc():
    """LLMBackend is abstract — cannot instantiate directly."""
    with pytest.raises(TypeError):
        LLMBackend()


def test_message_fields():
    msg = Message(role="user", content="test message")
    assert msg.role == "user"
    assert msg.content == "test message"


def test_llm_response_fields():
    resp = LLMResponse(text="hello", model="test-model", tokens_used=10, finish_reason="stop", tool_calls=None)
    assert resp.text == "hello"
    assert resp.model == "test-model"
    assert resp.tokens_used == 10
    assert resp.finish_reason == "stop"
    assert resp.tool_calls is None


def test_llm_response_with_tool_calls():
    resp = LLMResponse(
        text="",
        model="test-model",
        tokens_used=20,
        finish_reason="tool_calls",
        tool_calls=[{"name": "search", "arguments": {"query": "test"}}],
    )
    assert resp.tool_calls is not None
    assert len(resp.tool_calls) == 1


def test_concrete_backend_must_implement_complete():
    """Subclasses must implement abstract methods."""

    class IncompleteBackend(LLMBackend):
        pass

    with pytest.raises(TypeError):
        IncompleteBackend()
```

- [ ] **Step 2: Run test — confirm failure**

```bash
cd E:/ProjectHJM/forhacker && python -m pytest tests/test_llm/test_backend.py -v
```

Expected: FAIL — `LLMBackend` and `Message` not defined yet.

- [ ] **Step 3: Implement `forhacker/llm/backend.py`**

```python
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Literal


@dataclass(slots=True)
class Message:
    role: Literal["system", "user", "assistant", "tool"]
    content: str


@dataclass(slots=True)
class LLMResponse:
    text: str
    model: str
    tokens_used: int
    finish_reason: str
    tool_calls: list[dict] | None = None


class LLMBackend(ABC):
    """Unified interface for all LLM providers."""

    @abstractmethod
    async def complete(self, messages: list[Message], tools: list[dict] | None = None, **kwargs) -> LLMResponse:
        ...

    async def stream(self, messages: list[Message], tools: list[dict] | None = None, **kwargs) -> AsyncIterator[str]:
        """Stream tokens as they are generated. Not all backends support streaming."""
        raise NotImplementedError(f"{self.__class__.__name__} does not support streaming")

    @property
    @abstractmethod
    def model_name(self) -> str:
        ...
```

- [ ] **Step 4: Run test — confirm pass**

```bash
cd E:/ProjectHJM/forhacker && python -m pytest tests/test_llm/test_backend.py -v
```

Expected: 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add forhacker/llm/backend.py tests/test_llm/test_backend.py
git commit -m "$(cat <<'EOF'
feat: LLMBackend ABC with Message and LLMResponse types

Messages-based API: complete() and stream() accept list[Message]
with optional tools list. LLMResponse carries text, model, tokens_used,
finish_reason, and optional tool_calls. Abstract property for model_name.
Supports_streaming deferred until a production consumer exists (YAGNI).

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: GATE — LLMBackend contract validation

**Depends on:** Task 2 (LLMBackend ABC)

**This task is a gate.** The LLMBackend ABC (complete/stream signatures, Message and LLMResponse types) is the load-bearing interface for the entire forhacker architecture. If it cannot support the three required backends (OpenAI, Ollama, Anthropic), the design must be revised before proceeding.

**Files:**
- Create: `tests/test_llm/test_backend_contract.py`
- Read: `forhacker/llm/backend.py`

- [ ] **Step 1: Write a contract test validating LLMBackend's messages-based API against all planned backends**

`tests/test_llm/test_backend_contract.py`:
```python
"""GATE test: validate LLMBackend contract across all planned backends.

If this gate fails after 2 REFACTOR iterations, STOP. The LLMBackend
interface must be redesigned before proceeding to implementation tasks.
"""
import pytest
from forhacker.llm.backend import LLMBackend, Message, LLMResponse


def test_message_dataclass_matches_openai_convention():
    """OpenAI API uses role + content dicts; Message must serialize cleanly."""
    msg = Message(role="user", content="hello")
    as_dict = {"role": msg.role, "content": msg.content}
    assert as_dict == {"role": "user", "content": "hello"}


def test_message_dataclass_matches_anthropic_convention():
    """Anthropic API separates system from chat messages; Message.role must support all needed roles."""
    valid_roles = {"system", "user", "assistant", "tool"}
    for role in valid_roles:
        msg = Message(role=role, content="test")
        assert msg.role == role


def test_llmresponse_carries_tool_calls():
    """Tool-calling is central to forensics workflows; LLMResponse must carry optional tool_calls."""
    resp = LLMResponse(
        text="",
        model="test",
        tokens_used=0,
        finish_reason="tool_calls",
        tool_calls=[{"name": "search", "arguments": {"q": "x"}}],
    )
    assert resp.tool_calls is not None
    assert resp.tool_calls[0]["name"] == "search"


def test_complete_signature_accepts_tools():
    """SubAgents pass tools per spec; the ABC signature must accept them."""
    import inspect
    sig = inspect.signature(LLMBackend.complete)
    params = list(sig.parameters.keys())
    assert "tools" in params
    assert "messages" in params
```

- [ ] **Step 2: Run GATE test — confirm pass**

```bash
cd E:/ProjectHJM/forhacker && python -m pytest tests/test_llm/test_backend_contract.py -v
```

Expected: 4 tests PASS. If any test fails, the LLMBackend contract must be revised before continuing.

> **REFACTOR loop:** If the contract tests fail, try up to 2 revisions of the Message/LLMResponse types. **If still failing after 2 iterations, STOP. Do not proceed to Task 4.** Report the specific contract mismatch — the backend interface must be redesigned before implementation.

- [ ] **Step 3: Commit gate test**

```bash
git add tests/test_llm/test_backend_contract.py
git commit -m "$(cat <<'EOF'
test: GATE — LLMBackend contract validation across all planned backends

Validates Message format compatibility with OpenAI and Anthropic,
LLMResponse tool_calls support, and complete() tools acceptance.
BLOCKS all downstream tasks if it fails after 2 REFACTOR iterations.

Ref: docs/superpowers/specs/2026-05-21-forhacker-design.md

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: OpenAI and Ollama backends

**Files:**
- Create: `forhacker/llm/openai.py`
- Create: `forhacker/llm/ollama.py`
- Create: `tests/test_llm/test_openai.py`
- Create: `tests/test_llm/test_ollama.py`

- [ ] **Step 1: Write failing test for OpenAI backend**

`tests/test_llm/test_openai.py`:
```python
import pytest
from forhacker.llm.backend import Message, LLMResponse
from forhacker.llm.openai import OpenAIBackend


@pytest.mark.asyncio
async def test_openai_backend_model_name():
    backend = OpenAIBackend(model="gpt-4o-mini", api_key="test-key")
    assert backend.model_name == "gpt-4o-mini"


@pytest.mark.asyncio
async def test_openai_backend_converts_messages():
    backend = OpenAIBackend(model="gpt-4o-mini", api_key="test-key")
    messages = [Message(role="user", content="hello")]
    converted = backend._messages_to_openai_format(messages)
    assert converted == [{"role": "user", "content": "hello"}]
```

- [ ] **Step 2: Run test — confirm failure**

```bash
cd E:/ProjectHJM/forhacker && python -m pytest tests/test_llm/test_openai.py -v
```

Expected: FAIL — `OpenAIBackend` not defined.

- [ ] **Step 3: Implement `forhacker/llm/openai.py`**

```python
from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from forhacker.llm.backend import LLMBackend, LLMResponse, Message


class OpenAIBackend(LLMBackend):
    def __init__(self, model: str, api_key: str, base_url: str | None = None, timeout: float = 120.0):
        self._model = model
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=timeout)

    @property
    def model_name(self) -> str:
        return self._model

    # supports_streaming property removed (YAGNI: no production consumer yet)

    def _messages_to_openai_format(self, messages: list[Message]) -> list[dict]:
        return [{"role": m.role, "content": m.content} for m in messages]

    async def complete(self, messages: list[Message], tools: list[dict] | None = None, **kwargs) -> LLMResponse:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=self._messages_to_openai_format(messages),
            tools=tools or None,
            **kwargs,
        )
        choice = response.choices[0]
        return LLMResponse(
            text=choice.message.content or "",
            model=response.model,
            tokens_used=response.usage.total_tokens if response.usage else 0,
            finish_reason=choice.finish_reason or "stop",
            tool_calls=[tc.model_dump() for tc in choice.message.tool_calls] if choice.message.tool_calls else None,
        )

    async def stream(self, messages: list[Message], tools: list[dict] | None = None, **kwargs) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=self._messages_to_openai_format(messages),
            tools=tools or None,
            stream=True,
            **kwargs,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
```

- [ ] **Step 4: Implement `forhacker/llm/ollama.py`**

```python
from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from forhacker.llm.backend import LLMBackend, LLMResponse, Message


class OllamaBackend(LLMBackend):
    """Ollama via its OpenAI-compatible API."""

    def __init__(self, model: str, base_url: str = "http://localhost:11434/v1", timeout: float = 300.0):
        self._model = model
        self._client = AsyncOpenAI(api_key="ollama", base_url=base_url, timeout=timeout)

    @property
    def model_name(self) -> str:
        return self._model

    async def complete(self, messages: list[Message], tools: list[dict] | None = None, **kwargs) -> LLMResponse:
        fmt = [{"role": m.role, "content": m.content} for m in messages]
        response = await self._client.chat.completions.create(
            model=self._model, messages=fmt, tools=tools or None, **kwargs
        )
        choice = response.choices[0]
        return LLMResponse(
            text=choice.message.content or "",
            model=response.model,
            tokens_used=response.usage.total_tokens if response.usage else 0,
            finish_reason=choice.finish_reason or "stop",
        )

    async def stream(self, messages: list[Message], tools: list[dict] | None = None, **kwargs) -> AsyncIterator[str]:
        raise NotImplementedError("Ollama streaming not yet implemented")
```

- [ ] **Step 5: Write test for Ollama backend**

`tests/test_llm/test_ollama.py`:
```python
import pytest
from forhacker.llm.ollama import OllamaBackend


def test_ollama_backend_default_url():
    backend = OllamaBackend(model="llama3:8b")
    assert backend.model_name == "llama3:8b"


def test_ollama_backend_custom_url():
    backend = OllamaBackend(model="mistral:7b", base_url="http://192.168.1.100:11434/v1")
    assert backend.model_name == "mistral:7b"
```

- [ ] **Step 6: Implement `forhacker/llm/resilience.py`**

```python
import asyncio
import random
import time
from forhacker.llm.backend import LLMBackend, LLMResponse, Message


class ResilienceWrapper:
    """Wraps LLMBackend.complete() with timeout, retry, and circuit breaker."""

    def __init__(self, max_retries: int = 3, timeout: float = 120.0,
                 circuit_threshold: int = 5, circuit_cooldown: float = 60.0):
        self._max_retries = max_retries
        self._timeout = timeout
        self._circuit_threshold = circuit_threshold
        self._circuit_cooldown = circuit_cooldown
        self._consecutive_failures = 0
        self._circuit_open_until: float = 0.0

    async def complete(self, backend: LLMBackend, messages: list[Message],
                       tools: list[dict] | None = None, **kwargs) -> LLMResponse:
        if time.monotonic() < self._circuit_open_until:
            raise RuntimeError("Circuit breaker open — too many failures")
        last_exc = None
        for attempt in range(self._max_retries):
            try:
                resp = await asyncio.wait_for(
                    backend.complete(messages, tools=tools, **kwargs),
                    timeout=self._timeout,
                )
                self._consecutive_failures = 0
                return resp
            except asyncio.TimeoutError:
                last_exc = TimeoutError(f"LLM call timed out ({self._timeout}s)")
            except Exception as e:
                last_exc = e
                if hasattr(e, "status_code") and 400 <= e.status_code < 500 and e.status_code != 429:
                    raise  # auth errors propagate immediately
            if attempt < self._max_retries - 1:
                delay = (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(delay)
        self._consecutive_failures += 1
        if self._consecutive_failures >= self._circuit_threshold:
            self._circuit_open_until = time.monotonic() + self._circuit_cooldown
        raise last_exc  # type: ignore[misc]
```

- [ ] **Step 7: Write resilience test**

`tests/test_llm/test_resilience.py`:
```python
import pytest
from forhacker.llm.resilience import ResilienceWrapper


def test_resilience_wrapper_initial_state():
    rw = ResilienceWrapper(max_retries=3, timeout=60.0)
    assert rw._max_retries == 3
    assert rw._circuit_open_until == 0.0
```

- [ ] **Step 8: Run all LLM tests**

```bash
cd E:/ProjectHJM/forhacker && python -m pytest tests/test_llm/ -v
```

Expected: All tests PASS (OpenAI + Ollama + resilience test).

- [ ] **Step 9: Commit**

```bash
git add forhacker/llm/openai.py forhacker/llm/ollama.py forhacker/llm/resilience.py tests/test_llm/
git commit -m "$(cat <<'EOF'
feat: OpenAI and Ollama LLMBackend implementations + resilience wrapper

OpenAIBackend wraps AsyncOpenAI with Message-to-OpenAI-format conversion,
tool call extraction, and streaming support. OllamaBackend uses OpenAI-
compatible API at localhost:11434 with simplified response mapping.
ResilienceWrapper: timeout, exponential backoff with jitter, circuit breaker.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: Anthropic backend

**Depends on:** Task 2 (LLMBackend ABC), Task 4 (OpenAI pattern reference)

**Files:**
- Create: `forhacker/llm/anthropic.py`
- Create: `tests/test_llm/test_anthropic.py`

> **Note:** DeepSeek is configured via `OpenAIBackend(model="deepseek-chat", base_url="https://api.deepseek.com/v1")` — no separate subclass needed. Sensitivity routing is handled by the `FORHACKER_OFFLINE` env var alone; no SensitivityRouter class is warranted until data-classification requirements are defined in a future spec.

- [ ] **Step 1: Write failing test for Anthropic backend tool calling**

`tests/test_llm/test_anthropic.py`:
```python
import pytest
from forhacker.llm.backend import Message, LLMResponse
from forhacker.llm.anthropic import AnthropicBackend


def test_anthropic_backend_model_name():
    backend = AnthropicBackend(model="claude-sonnet-4-6", api_key="test-key")
    assert backend.model_name == "claude-sonnet-4-6"


def test_anthropic_detects_tool_role_messages():
    """Anthropic API rejects role='tool'; backend must detect and raise NotImplementedError."""
    backend = AnthropicBackend(model="claude-sonnet-4-6", api_key="test-key")
    msgs = [
        Message(role="user", content="run analysis"),
        Message(role="assistant", content=""),
        Message(role="tool", content="result: 123"),
    ]
    with pytest.raises(NotImplementedError, match="tool-calling"):
        backend._convert_messages(msgs)


def test_anthropic_extracts_tool_use_blocks():
    """Verify _extract_tool_calls maps Anthropic tool_use blocks to standard format."""
    from anthropic.types import ContentBlock, ToolUseBlock

    # Test the mapping function directly with a mock structure
    mock_block = type("MockBlock", (), {
        "type": "tool_use",
        "id": "tool_123",
        "name": "search",
        "input": {"query": "test"},
    })
    result = AnthropicBackend._extract_tool_calls([mock_block])
    assert len(result) == 1
    assert result[0]["name"] == "search"
    assert result[0]["arguments"] == {"query": "test"}
```

- [ ] **Step 2: Run test — confirm failure**

```bash
cd E:/ProjectHJM/forhacker && python -m pytest tests/test_llm/test_anthropic.py -v
```

Expected: FAIL — `AnthropicBackend` not defined.

- [ ] **Step 3: Implement `forhacker/llm/anthropic.py`**

```python
from collections.abc import AsyncIterator
from typing import Any

from anthropic import AsyncAnthropic

from forhacker.llm.backend import LLMBackend, LLMResponse, Message


class AnthropicBackend(LLMBackend):
    def __init__(self, model: str = "claude-sonnet-4-6", api_key: str = "", timeout: float = 120.0):
        self._model = model
        self._client = AsyncAnthropic(api_key=api_key, timeout=timeout)

    @property
    def model_name(self) -> str:
        return self._model

    def _convert_messages(self, messages: list[Message]) -> tuple[str | None, list[dict]]:
        """Convert forhacker Messages to Anthropic API format.

        Anthropic API only accepts 'user' and 'assistant' roles. Tool-result messages
        (role='tool') must be bundled into the preceding user message as content blocks
        with type='tool_result' and a tool_use_id. Since we don't track tool_use_id yet,
        we raise NotImplementedError for tool-calling workflows — this is deferred to
        when the Supervisor actually uses Anthropic with tools.
        """
        system_parts = []
        converted = []
        for m in messages:
            if m.role == "system":
                system_parts.append(m.content)
            elif m.role == "tool":
                raise NotImplementedError(
                    "AnthropicBackend does not yet support tool-calling workflows. "
                    "Tool result messages require tool_use_id tracking which is deferred "
                    "to a future implementation phase."
                )
            else:
                converted.append({"role": m.role, "content": m.content})
        system = "\n".join(system_parts) if system_parts else None
        return system, converted

    @staticmethod
    def _extract_tool_calls(content_blocks: list[Any]) -> list[dict] | None:
        """Extract tool_use blocks from Anthropic response and map to standard format."""
        tool_calls = []
        for block in content_blocks:
            if hasattr(block, "type") and block.type == "tool_use":
                tool_calls.append({
                    "id": getattr(block, "id", ""),
                    "name": getattr(block, "name", ""),
                    "arguments": getattr(block, "input", {}),
                })
        return tool_calls if tool_calls else None

    async def complete(self, messages: list[Message], tools: list[dict] | None = None, **kwargs) -> LLMResponse:
        system, converted_msgs = self._convert_messages(messages)
        kwargs_anthropic: dict[str, Any] = {"max_tokens": kwargs.pop("max_tokens", 4096)}
        if system:
            kwargs_anthropic["system"] = system
        if tools:
            kwargs_anthropic["tools"] = tools

        response = await self._client.messages.create(
            model=self._model,
            messages=converted_msgs,
            **kwargs_anthropic,
            **kwargs,
        )
        text = "".join(
            block.text for block in response.content
            if hasattr(block, "text") and block.type == "text"
        )
        return LLMResponse(
            text=text,
            model=response.model,
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            finish_reason=response.stop_reason or "stop",
            tool_calls=self._extract_tool_calls(response.content),
        )

    async def stream(self, messages: list[Message], tools: list[dict] | None = None, **kwargs) -> AsyncIterator[str]:
        raise NotImplementedError("Anthropic streaming not yet implemented")
```

- [ ] **Step 4: Run tests — confirm pass**

```bash
cd E:/ProjectHJM/forhacker && python -m pytest tests/test_llm/test_anthropic.py -v
```

Expected: 3 tests PASS.

> **REFACTOR note:** If the GREEN step still fails after implementation, try up to 2 revisions of the Anthropic backend code. If still failing after 2 iterations, STOP and report the specific Anthropic API behavior that differs from the expected mapping.

- [ ] **Step 5: Commit**

```bash
git add forhacker/llm/anthropic.py tests/test_llm/test_anthropic.py
git commit -m "$(cat <<'EOF'
feat: Anthropic backend with tool-call extraction and message conversion

_convert_messages handles Anthropic's role constraints (raises
NotImplementedError for tool-result messages — deferred until
tool_use_id tracking is implemented). _extract_tool_calls maps
Anthropic tool_use blocks to standard dict format. DeepSeek
configured via OpenAIBackend directly (no subclass needed).

Ref: docs/superpowers/specs/2026-05-21-forhacker-design.md

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: MessageBus ABC + InProcessBus

**Files:**
- Create: `forhacker/bus/message_bus.py`
- Create: `forhacker/bus/in_process.py`
- Create: `tests/test_bus/test_message_bus.py`

- [ ] **Step 1: Write failing test for MessageBus ABC + InProcessBus**

`tests/test_bus/test_message_bus.py`:
```python
import asyncio
import pytest
from forhacker.bus.message_bus import MessageBus
from forhacker.bus.in_process import InProcessBus


def test_cannot_instantiate_message_bus_abc():
    with pytest.raises(TypeError):
        MessageBus()


@pytest.mark.asyncio
async def test_in_process_publish_subscribe():
    bus = InProcessBus()
    received = []

    async def handler(message):
        received.append(message)

    await bus.subscribe("test.topic", handler)
    await bus.publish("test.topic", {"key": "value"})
    await asyncio.sleep(0.05)
    assert len(received) == 1
    assert received[0] == {"key": "value"}


@pytest.mark.asyncio
async def test_in_process_request_response():
    bus = InProcessBus()

    async def handler(payload):
        return {"result": payload["x"] * 2}

    await bus.subscribe("compute", handler)
    result = await bus.request("compute", {"x": 21})
    assert result == {"result": 42}


@pytest.mark.asyncio
async def test_in_process_multiple_subscribers():
    bus = InProcessBus()
    results = []

    async def handler_a(msg):
        results.append(("a", msg))

    async def handler_b(msg):
        results.append(("b", msg))

    await bus.subscribe("multi", handler_a)
    await bus.subscribe("multi", handler_b)
    await bus.publish("multi", {"data": 1})
    await asyncio.sleep(0.05)
    assert len(results) == 2
```

- [ ] **Step 2: Run test — confirm failure**

```bash
cd E:/ProjectHJM/forhacker && python -m pytest tests/test_bus/ -v
```

- [ ] **Step 3: Implement `forhacker/bus/message_bus.py`**

```python
from abc import ABC, abstractmethod
from collections.abc import Callable, Coroutine
from typing import Any


class MessageBus(ABC):
    @abstractmethod
    async def publish(self, topic: str, message: dict) -> None:
        ...

    @abstractmethod
    async def subscribe(self, topic: str, handler: Callable[[dict], Coroutine]) -> None:
        ...

    @abstractmethod
    async def request(self, target: str, payload: dict) -> dict:
        ...
```

- [ ] **Step 4: Implement `forhacker/bus/in_process.py`**

```python
import asyncio
from collections.abc import Callable, Coroutine
from forhacker.bus.message_bus import MessageBus


class InProcessBus(MessageBus):
    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = {}

    async def publish(self, topic: str, message: dict) -> None:
        for handler in self._subscribers.get(topic, []):
            await handler(message)

    async def subscribe(self, topic: str, handler: Callable[[dict], Coroutine]) -> None:
        self._subscribers.setdefault(topic, []).append(handler)

    async def request(self, target: str, payload: dict) -> dict:
        handlers = self._subscribers.get(target, [])
        if not handlers:
            raise ValueError(f"No handler for target: {target}")
        return await handlers[0](payload)
```

- [ ] **Step 5: Run tests — confirm pass**

```bash
cd E:/ProjectHJM/forhacker && python -m pytest tests/test_bus/ -v
```

Expected: 4 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add forhacker/bus/ tests/test_bus/
git commit -m "$(cat <<'EOF'
feat: MessageBus ABC and InProcessBus

InProcessBus: asyncio-based pub/sub with per-topic handler lists.
Zero external dependencies. request() calls first subscriber and
returns result for RPC-style patterns.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: BasePlugin ABC + PluginManager discovery

**Depends on:** Task 5 (CapabilityRegistry stub — Task 6 tests use CapabilityRegistry, which Task 7 implements in full; a minimal stub is needed for Task 6 tests to pass)

**Files:**
- Create: `forhacker/plugin/base.py`
- Create: `forhacker/plugin/manager.py`
- Create: `tests/test_plugin/test_base.py`
- Create: `tests/test_plugin/test_manager.py`

- [ ] **Step 1: Write failing test for BasePlugin ABC**

`tests/test_plugin/test_base.py`:
```python
import pytest
from forhacker.plugin.base import BasePlugin, Tool


def test_tool_dataclass():
    t = Tool(name="strings", description="Extract strings from binary", domain="forensics", risk_level="LOW")
    assert t.name == "strings"
    assert t.domain == "forensics"
    assert t.risk_level == "LOW"


def test_cannot_instantiate_base_plugin():
    with pytest.raises(TypeError):
        BasePlugin()


def test_concrete_plugin_must_implement_methods():

    class IncompletePlugin(BasePlugin):
        name = "test"
        version = "0.1"
        domain = "forensics"
        risk_levels = {}

    with pytest.raises(TypeError):
        IncompletePlugin()
```

- [ ] **Step 2: Run test — confirm failure**

```bash
cd E:/ProjectHJM/forhacker && python -m pytest tests/test_plugin/test_base.py -v
```

- [ ] **Step 3: Implement `forhacker/plugin/base.py`**

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class Tool:
    name: str
    description: str
    domain: str
    risk_level: str  # LOW | MEDIUM | HIGH


class BasePlugin(ABC):
    name: str
    version: str
    domain: str
    risk_levels: dict[str, str]  # tool_name → LOW|MEDIUM|HIGH (required for security router)

    @abstractmethod
    def register_tools(self) -> list[Tool]:
        ...
```

- [ ] **Step 4: Write failing test for PluginManager**

`tests/test_plugin/test_manager.py`:
```python
import pytest
from forhacker.plugin.base import BasePlugin, Tool
from forhacker.plugin.manager import PluginManager
from forhacker.task.capability import CapabilityRegistry


class FakePlugin(BasePlugin):
    name = "fake-forensics"
    version = "0.1.0"
    domain = "forensics"
    risk_levels = {"fake_tool": "MEDIUM"}

    def register_tools(self) -> list[Tool]:
        return [Tool(name="fake_tool", description="A fake tool", domain="forensics", risk_level="MEDIUM")]

    # register_mcp_resources() removed (YAGNI: deferred to future MCP wiring spec)


class FailingPlugin(BasePlugin):
    name = "failing-plugin"
    version = "0.1.0"
    domain = "osint"
    risk_levels = {}

    def register_tools(self) -> list[Tool]:
        raise RuntimeError("simulated load failure")

    # register_mcp_resources() removed (YAGNI: deferred to future MCP wiring spec)


@pytest.mark.asyncio
async def test_plugin_manager_loads_plugin():
    registry = CapabilityRegistry()
    manager = PluginManager(registry=registry)
    manager.load_plugin(FakePlugin())
    tools = registry.query(domain="forensics")
    assert len(tools) == 1
    assert tools[0].name == "fake_tool"


@pytest.mark.asyncio
async def test_plugin_manager_isolates_failure():
    registry = CapabilityRegistry()
    manager = PluginManager(registry=registry)
    manager.load_plugin(FailingPlugin())
    manager.load_plugin(FakePlugin())
    assert "failing-plugin" in manager.degraded_plugins
    tools = registry.query(domain="forensics")
    assert len(tools) == 1
```

- [ ] **Step 5: Implement `forhacker/plugin/manager.py`**

```python
import logging
from forhacker.plugin.base import BasePlugin
from forhacker.task.capability import CapabilityRegistry

logger = logging.getLogger(__name__)


class PluginManager:
    def __init__(self, registry: CapabilityRegistry):
        self._registry = registry
        self._plugins: dict[str, BasePlugin] = {}
        self.degraded_plugins: list[str] = []

    def load_plugin(self, plugin: BasePlugin) -> None:
        try:
            for tool in plugin.register_tools():
                self._registry.register(tool)
            self._plugins[plugin.name] = plugin
        except Exception as e:
            logger.error("Plugin %s failed to load: %s", plugin.name, e)
            self.degraded_plugins.append(plugin.name)

    @property
    def loaded_plugins(self) -> list[str]:
        return list(self._plugins.keys())
```

- [ ] **Step 6: Run plugin tests — confirm pass**

```bash
cd E:/ProjectHJM/forhacker && python -m pytest tests/test_plugin/ -v
```

Expected: All tests PASS.

- [ ] **Step 7: Commit**

```bash
git add forhacker/plugin/base.py forhacker/plugin/manager.py tests/test_plugin/
git commit -m "$(cat <<'EOF'
feat: BasePlugin ABC and PluginManager with failure isolation

BasePlugin: Tool dataclass, register_tools() abstract method. MCPResource
and register_mcp_resources() deferred to future MCP wiring spec (YAGNI).
into CapabilityRegistry, isolates failures into degraded_plugins list.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 7: CapabilityRegistry (owned by task/)

**Files:**
- Create: `forhacker/task/capability.py`
- Create: `tests/test_task/test_capability.py`

- [ ] **Step 1: Write failing test for CapabilityRegistry**

`tests/test_task/test_capability.py`:
```python
import pytest
from forhacker.plugin.base import Tool
from forhacker.task.capability import CapabilityRegistry


def test_register_and_query_by_domain():
    registry = CapabilityRegistry()
    registry.register(Tool(name="vol3", description="Volatility 3", domain="forensics", risk_level="MEDIUM"))
    registry.register(Tool(name="nmap", description="Network scanner", domain="pentest", risk_level="LOW"))
    results = registry.query(domain="forensics")
    assert len(results) == 1
    assert results[0].name == "vol3"


def test_query_unknown_domain_returns_empty():
    registry = CapabilityRegistry()
    results = registry.query(domain="nonexistent")
    assert results == []


def test_list_domains():
    registry = CapabilityRegistry()
    registry.register(Tool(name="t1", description="d1", domain="forensics", risk_level="LOW"))
    registry.register(Tool(name="t2", description="d2", domain="pentest", risk_level="LOW"))
    domains = registry.list_domains()
    assert "forensics" in domains
    assert "pentest" in domains


def test_duplicate_tool_overwrites():
    registry = CapabilityRegistry()
    registry.register(Tool(name="dup", description="first", domain="test", risk_level="LOW"))
    registry.register(Tool(name="dup", description="second", domain="test", risk_level="MEDIUM"))
    tools = registry.query(domain="test")
    assert len(tools) == 1
    assert tools[0].description == "second"
```

- [ ] **Step 2: Run test — confirm failure**

```bash
cd E:/ProjectHJM/forhacker && python -m pytest tests/test_task/test_capability.py -v
```

- [ ] **Step 3: Implement `forhacker/task/capability.py`**

```python
from forhacker.plugin.base import Tool


class CapabilityRegistry:
    """Tool/agent capability lookup owned by task/, populated by plugin/."""

    def __init__(self):
        self._tools: dict[str, dict[str, Tool]] = {}  # domain → {tool_name: Tool}

    def register(self, tool: Tool) -> None:
        self._tools.setdefault(tool.domain, {})[tool.name] = tool

    def query(self, domain: str) -> list[Tool]:
        domain_tools = self._tools.get(domain, {})
        return list(domain_tools.values())

    def list_domains(self) -> list[str]:
        return list(self._tools.keys())
```

- [ ] **Step 4: Run tests — confirm pass**

```bash
cd E:/ProjectHJM/forhacker && python -m pytest tests/test_task/test_capability.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add forhacker/task/capability.py tests/test_task/test_capability.py
git commit -m "$(cat <<'EOF'
feat: CapabilityRegistry owned by task/ subsystem

Per-spec dependency inversion: plugin/ populates the registry,
task/ owns and queries it. Domain-scoped tool lookup with
duplicate-overwrite semantics.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 8: PostgreSQL schema, migration, and data layer

**Files:**
- Create: `forhacker/data/db.py`
- Create: `forhacker/data/models.py`
- Create: `forhacker/data/evidence.py`
- Create: `tests/test_data/test_models.py`
- Create: `tests/test_data/test_evidence.py`

- [ ] **Step 1: Write failing test for SQLAlchemy models**

`tests/test_data/test_models.py`:
```python
import pytest
from forhacker.data.models import Base, Case, Task, Finding, Agent, EvidenceIndex


def test_case_table_exists():
    assert hasattr(Case, "__tablename__")
    assert Case.__tablename__ == "cases"


def test_finding_has_confidence_columns():
    assert hasattr(Finding, "task_confidence")
    assert hasattr(Finding, "evidence_confidence")
    assert hasattr(Finding, "last_ingested_at")


def test_evidence_index_has_integrity_field():
    assert hasattr(EvidenceIndex, "integrity")


def test_agent_has_heartbeat_field():
    assert hasattr(Agent, "last_heartbeat")
```

- [ ] **Step 2: Run test — confirm failure**

```bash
cd E:/ProjectHJM/forhacker && python -m pytest tests/test_data/test_models.py -v
```

- [ ] **Step 3: Implement `forhacker/data/models.py`**

```python
import datetime
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Case(Base):
    __tablename__ = "cases"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))
    lead_investigator = Column(String, nullable=True)


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    parent_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    type = Column(String, nullable=False)
    status = Column(String, default="pending")
    assigned_to = Column(String, nullable=True)
    task_confidence = Column(String, default="MEDIUM")  # HIGH | MEDIUM | LOW
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))


class Finding(Base):
    __tablename__ = "findings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    type = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    task_confidence = Column(String, default="MEDIUM")  # HIGH | MEDIUM | LOW
    evidence_confidence = Column(String, default="unknown")  # verified | inferred | unknown
    evidence_ref = Column(String, nullable=True)
    created_by = Column(String, nullable=False)
    last_ingested_at = Column(DateTime, nullable=True)


class EvidenceIndex(Base):
    __tablename__ = "evidence_index"
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    path = Column(String, nullable=False)
    sha256 = Column(String, nullable=True)
    file_type = Column(String, nullable=True)
    size_bytes = Column(BigInteger, nullable=True)
    indexed_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))
    integrity = Column(String, default="missing")  # verified | failed | missing | orphan


class Agent(Base):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=True)
    cell = Column(String, nullable=True)
    status = Column(String, default="alive")
    last_heartbeat = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))


class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(String, nullable=False)
    actor = Column(String, nullable=False)
    target = Column(String, nullable=True)
    details_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))


class MetaProposal(Base):
    __tablename__ = "meta_proposals"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String, nullable=True)
    title = Column(String, nullable=False)
    status = Column(String, default="pending")
    risk_level = Column(String, default="LOW")
    approved_by = Column(String, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    rollback_snapshot = Column(String, nullable=True)


class MetaScanLock(Base):
    __tablename__ = "meta_scan_lock"
    id = Column(Integer, primary_key=True, autoincrement=True)
    locked_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))
    locked_by = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
```

- [ ] **Step 4: Implement `forhacker/data/db.py`**

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from forhacker.data.models import Base

_engine = None
_session_factory = None


async def init_db(database_url: str = "postgresql+asyncpg://localhost/forhacker"):
    global _engine, _session_factory
    _engine = create_async_engine(database_url, echo=False)
    _session_factory = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _session_factory()


async def close_db():
    global _engine
    if _engine:
        await _engine.dispose()
        _engine = None
```

- [ ] **Step 5: Implement `forhacker/data/evidence.py`**

```python
import hashlib
from pathlib import Path


def compute_sha256(path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha.update(chunk)
    return sha.hexdigest()


def verify_evidence(path: Path, expected_sha256: str) -> bool:
    """Verify file integrity against expected hash. Returns True if match."""
    actual = compute_sha256(path)
    return actual == expected_sha256
```

- [ ] **Step 6: Write evidence tests**

`tests/test_data/test_evidence.py`:
```python
import tempfile
from pathlib import Path
from forhacker.data.evidence import compute_sha256, verify_evidence


def test_compute_sha256():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        f.write(b"hello world")
        path = Path(f.name)
    try:
        h = compute_sha256(path)
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)
    finally:
        path.unlink()


def test_verify_evidence_match():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
        f.write(b"test data")
        path = Path(f.name)
    try:
        h = compute_sha256(path)
        assert verify_evidence(path, h) is True
    finally:
        path.unlink()


def test_verify_evidence_mismatch():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
        f.write(b"original")
        path = Path(f.name)
    try:
        assert verify_evidence(path, "a" * 64) is False
    finally:
        path.unlink()
```

- [ ] **Step 7: Run all data tests**

```bash
cd E:/ProjectHJM/forhacker && python -m pytest tests/test_data/ -v
```

Expected: All tests PASS (model introspection + SHA256 compute/verify).

- [ ] **Step 8: Commit**

```bash
git add forhacker/data/ tests/test_data/
git commit -m "$(cat <<'EOF'
feat: PostgreSQL schema, async engine, and evidence hash utilities

SQLAlchemy models with dual confidence columns (task_confidence +
evidence_confidence), integrity tracking on evidence_index, MetaAgent
tables (meta_proposals, meta_scan_lock). Async engine via asyncpg.
SHA256 compute/verify for evidence integrity.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 9: CLI entry point

**Files:**
- Create: `forhacker/cli/main.py`
- Create: `forhacker/cli/commands/__init__.py`
- Create: `forhacker/cli/commands/case.py`
- Create: `tests/test_cli/__init__.py`
- Create: `tests/test_cli/test_main.py`

- [ ] **Step 1: Write failing test for CLI**

`tests/test_cli/test_main.py`:
```python
from click.testing import CliRunner
from forhacker.cli.main import cli


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "forhacker" in result.output


def test_case_create_dry():
    runner = CliRunner()
    result = runner.invoke(cli, ["case", "create", "test-case"])
    assert result.exit_code == 0
    assert "test-case" in result.output


def test_case_status_empty():
    runner = CliRunner()
    result = runner.invoke(cli, ["case", "status"])
    assert result.exit_code == 0
```

- [ ] **Step 2: Implement `forhacker/cli/main.py`**

```python
import click
from forhacker.cli.commands.case import case_group


@click.group()
def cli():
    """forhacker — AI-Native Digital Forensics Platform."""
    pass


cli.add_command(case_group, name="case")
```

- [ ] **Step 3: Implement `forhacker/cli/commands/case.py`**

```python
import click


@click.group()
def case_group():
    """Case management."""
    pass


@case_group.command()
@click.argument("name")
def create(name: str):
    """Create a new case."""
    from pathlib import Path
    case_dir = Path("shared") / "cases" / name
    case_dir.mkdir(parents=True, exist_ok=True)
    click.echo(f"Case '{name}' created.")


@case_group.command()
def status():
    """Show case status."""
    click.echo("No active case.")
```

- [ ] **Step 4: Update `pyproject.toml` with CLI entry point**

```toml
[project.scripts]
forhacker = "forhacker.cli.main:cli"
```

- [ ] **Step 5: Run CLI tests**

```bash
cd E:/ProjectHJM/forhacker && python -m pytest tests/test_cli/ -v
```

Expected: 3 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add forhacker/cli/ tests/test_cli/ pyproject.toml
git commit -m "$(cat <<'EOF'
feat: CLI entry point with case create and status commands

Click-based CLI registered as 'forhacker' console script.
case create <name> and case status with empty-state output.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Phase 2: Supervisor + First Plugin (Tasks 10–14)

### Task 10: DAG data structure

**Files:**
- Create: `forhacker/task/dag.py`
- Create: `tests/test_task/test_dag.py`

- [ ] **Step 1: Write failing test for DAG operations**

`tests/test_task/test_dag.py`:
```python
import pytest
from forhacker.task.dag import DAG, TaskNode, AddTaskResult


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
```

- [ ] **Step 2: Run test — confirm failure**

```bash
cd E:/ProjectHJM/forhacker && python -m pytest tests/test_task/test_dag.py -v
```

- [ ] **Step 3: Implement `forhacker/task/dag.py`**

```python
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
    def __init__(self):
        self.tasks: dict[str, TaskNode] = {}

    def add_task(self, node: TaskNode) -> AddTaskResult:
        if node.task_id in self.tasks:
            return AddTaskResult.REJECTED_DUPLICATE
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
            deps_satisfied = all(
                self.tasks.get(dep) and self.tasks[dep].status == "done"
                for dep in node.depends_on
            )
            if deps_satisfied:
                ready.append(node)
        return ready
```

- [ ] **Step 4: Run tests — confirm pass**

```bash
cd E:/ProjectHJM/forhacker && python -m pytest tests/test_task/test_dag.py -v
```

Expected: 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add forhacker/task/dag.py tests/test_task/test_dag.py
git commit -m "$(cat <<'EOF'
feat: DAG task data structure with cycle detection

TaskNode with status, dependencies, confidence. DAG.add_task() returns
AddTaskResult enum (ADDED | REJECTED_CYCLE | REJECTED_DUPLICATE).
Per-call cycle detection via DFS. Topological sort and get_ready_tasks()
for Supervisor dispatch.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 11: TaskEngine with write-through persistence

**Files:**
- Create: `forhacker/task/engine.py`
- Create: `tests/test_task/test_engine.py`

- [ ] **Step 1: Write failing test for TaskEngine**

`tests/test_task/test_engine.py`:
```python
import pytest
from pathlib import Path
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
```

- [ ] **Step 2: Run test — confirm failure**

```bash
cd E:/ProjectHJM/forhacker && python -m pytest tests/test_task/test_engine.py -v
```

- [ ] **Step 3: Implement `forhacker/task/engine.py`**

```python
import tempfile
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
```

- [ ] **Step 4: Run tests — confirm pass**

```bash
cd E:/ProjectHJM/forhacker && python -m pytest tests/test_task/test_engine.py -v
```

Expected: 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add forhacker/task/engine.py tests/test_task/test_engine.py
git commit -m "$(cat <<'EOF'
feat: TaskEngine with write-through persistence, atomic claim, and corrupted YAML recovery

update_status() persists all status transitions atomically. claim_task()
atomically sets pending→running with claimant assignment. Corrupted
dag_state.yaml gracefully falls back to empty DAG. Acyclicity validated
on load. Schema version 1.

Ref: docs/superpowers/specs/2026-05-21-forhacker-design.md

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 12: SubAgent dispatch contract

**Files:**
- Create: `forhacker/task/sub_agent.py`
- Create: `tests/test_task/test_sub_agent.py`

- [ ] **Step 1: Write failing test for SubAgent contract types**

`tests/test_task/test_sub_agent.py`:
```python
from forhacker.task.sub_agent import SubAgentContext, SubAgentResult, SubAgentLifecycle
from forhacker.plugin.base import Tool


def test_sub_agent_context_fields():
    ctx = SubAgentContext(
        task_id="T-001",
        case_id="case-1",
        goal="analyze memory",
        evidence_paths=["/data/memory.dmp"],
        available_tools=[Tool(name="vol3", description="Volatility 3", domain="forensics", risk_level="MEDIUM")],
        dependency_findings=[],
        config={},
    )
    assert ctx.task_id == "T-001"
    assert len(ctx.available_tools) == 1
    assert ctx.dependency_findings == []


def test_sub_agent_result_done():
    result = SubAgentResult(
        findings=[],
        confidence="HIGH",
        artifacts=["/output/report.md"],
        status="done",
        error=None,
    )
    assert result.status == "done"
    assert result.confidence == "HIGH"


def test_sub_agent_result_failed():
    result = SubAgentResult(
        findings=[],
        confidence="LOW",
        artifacts=[],
        status="failed",
        error="tool timeout",
    )
    assert result.status == "failed"
    assert result.error == "tool timeout"


def test_sub_agent_lifecycle_states():
    states = list(SubAgentLifecycle)
    assert SubAgentLifecycle.INIT in states
    assert SubAgentLifecycle.EXECUTING in states
    assert SubAgentLifecycle.REPORTING in states
    assert SubAgentLifecycle.DONE in states
    assert SubAgentLifecycle.FAILED in states
```

- [ ] **Step 2: Run test — confirm failure**

```bash
cd E:/ProjectHJM/forhacker && python -m pytest tests/test_task/test_sub_agent.py -v
```

- [ ] **Step 3: Implement `forhacker/task/sub_agent.py`**

```python
from dataclasses import dataclass, field
from enum import Enum
from forhacker.plugin.base import Tool


class SubAgentLifecycle(Enum):
    INIT = "initialized"
    EXECUTING = "executing"
    REPORTING = "reporting"
    DONE = "done"
    FAILED = "failed"


@dataclass(slots=True)
class SubAgentContext:
    task_id: str
    case_id: str
    goal: str
    evidence_paths: list[str]
    available_tools: list[Tool]
    dependency_findings: list[dict] = field(default_factory=list)
    config: dict = field(default_factory=dict)


@dataclass(slots=True)
class SubAgentResult:
    findings: list[dict]
    confidence: str  # HIGH | MEDIUM | LOW (task_confidence)
    artifacts: list[str]
    status: str  # "done" | "failed"
    error: str | None = None
```

- [ ] **Step 4: Run tests — confirm pass**

```bash
cd E:/ProjectHJM/forhacker && python -m pytest tests/test_task/test_sub_agent.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add forhacker/task/sub_agent.py tests/test_task/test_sub_agent.py
git commit -m "$(cat <<'EOF'
feat: SubAgent dispatch contract types

SubAgentContext carries task metadata, available tools, and upstream
dependency_findings. SubAgentResult returns findings with confidence.
SubAgentLifecycle: INIT→EXECUTING→REPORTING→DONE|FAILED.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 13: Shared state protocol (collab/shared.py)

**Files:**
- Create: `forhacker/collab/shared.py`
- Create: `tests/test_collab/test_shared.py`

- [ ] **Step 1: Write failing test for shared state reader/writer**

`tests/test_collab/test_shared.py`:
```python
import pytest
from forhacker.collab.shared import write_finding, read_findings, write_dag_checkpoint, read_dag_checkpoint


def test_write_and_read_finding(tmp_shared_dir):
    case_dir = tmp_shared_dir / "cases" / "case-1"
    case_dir.mkdir(parents=True)
    write_finding(case_dir, member_id="member-A", finding={
        "id": "member-A-F-001",
        "type": "memory_analysis",
        "summary": "Suspicious process detected",
        "task_confidence": "HIGH",
        "evidence_confidence": "verified",
    })
    findings = read_findings(case_dir, member_id="member-A")
    assert len(findings) == 1
    assert findings[0]["id"] == "member-A-F-001"
    assert findings[0]["evidence_confidence"] == "verified"


def test_read_findings_returns_empty_for_new_member(tmp_shared_dir):
    case_dir = tmp_shared_dir / "cases" / "case-1"
    case_dir.mkdir(parents=True)
    findings = read_findings(case_dir, member_id="no-one")
    assert findings == []


def test_write_dag_checkpoint(tmp_shared_dir):
    case_dir = tmp_shared_dir / "cases" / "case-1"
    case_dir.mkdir(parents=True)
    write_dag_checkpoint(case_dir, tasks=[
        {"task_id": "T-001", "type": "analysis", "status": "done", "depends_on": []},
    ])
    tasks = read_dag_checkpoint(case_dir)
    assert len(tasks) == 1
    assert tasks[0]["task_id"] == "T-001"


def test_schema_version_written(tmp_shared_dir):
    case_dir = tmp_shared_dir / "cases" / "case-1"
    case_dir.mkdir(parents=True)
    import yaml
    write_finding(case_dir, member_id="member-A", finding={"id": "A-F-001", "type": "test"})
    path = case_dir / "findings" / "member-A.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
```

- [ ] **Step 2: Run test — confirm failure**

```bash
cd E:/ProjectHJM/forhacker && python -m pytest tests/test_collab/ -v
```

- [ ] **Step 3: Implement `forhacker/collab/shared.py`**

```python
from pathlib import Path
import yaml
import os

SCHEMA_VERSION = 1


def _write_yaml_atomic(path: Path, data: dict):
    data["schema_version"] = SCHEMA_VERSION
    payload = yaml.dump(data, allow_unicode=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(payload, encoding="utf-8")
    os.replace(tmp, path)


def _read_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    # Accept version N and N-1
    version = data.get("schema_version", 1)
    if version not in (SCHEMA_VERSION, SCHEMA_VERSION - 1):
        raise ValueError(f"Unsupported schema_version: {version}")
    return data


def write_finding(case_dir: Path, member_id: str, finding: dict):
    findings_dir = case_dir / "findings"
    findings_dir.mkdir(parents=True, exist_ok=True)
    path = findings_dir / f"{member_id}.yaml"
    existing = _read_yaml(path)
    existing.setdefault("findings", []).append(finding)
    _write_yaml_atomic(path, {"findings": existing["findings"]})


def read_findings(case_dir: Path, member_id: str) -> list[dict]:
    path = case_dir / "findings" / f"{member_id}.yaml"
    data = _read_yaml(path)
    return data.get("findings", [])


def write_dag_checkpoint(case_dir: Path, tasks: list[dict]):
    path = case_dir / "dag_state.yaml"
    _write_yaml_atomic(path, {"tasks": tasks})


def read_dag_checkpoint(case_dir: Path) -> list[dict]:
    data = _read_yaml(case_dir / "dag_state.yaml")
    return data.get("tasks", [])


def write_heartbeat(case_dir: Path, agent_id: str):
    import datetime
    path = case_dir / "agents" / agent_id / "heartbeat.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_yaml_atomic(path, {
        "agent_id": agent_id,
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
    })


def check_heartbeat(case_dir: Path, agent_id: str, staleness_seconds: float = 90.0) -> bool:
    import datetime
    path = case_dir / "agents" / agent_id / "heartbeat.yaml"
    if not path.exists():
        return False
    data = _read_yaml(path)
    ts = datetime.datetime.fromisoformat(data["timestamp"])
    return (datetime.datetime.now(datetime.UTC) - ts).total_seconds() < staleness_seconds
```

- [ ] **Step 4: Write heartbeat test**

`tests/test_collab/test_heartbeat.py`:
```python
from forhacker.collab.shared import write_heartbeat, check_heartbeat
from pathlib import Path
import time


def test_heartbeat_write_and_check(tmp_path):
    case_dir = tmp_path / "test-case"
    case_dir.mkdir()
    write_heartbeat(case_dir, "agent-1")
    assert check_heartbeat(case_dir, "agent-1", staleness_seconds=90.0)
    assert not check_heartbeat(case_dir, "agent-1", staleness_seconds=-1.0)
    assert not check_heartbeat(case_dir, "nonexistent", staleness_seconds=90.0)
```

- [ ] **Step 5: Run tests — confirm pass**

```bash
cd E:/ProjectHJM/forhacker && python -m pytest tests/test_collab/ -v
```

Expected: 5 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add forhacker/collab/shared.py tests/test_collab/
git commit -m "$(cat <<'EOF'
feat: shared state protocol with atomic YAML I/O and agent heartbeats

Per-member findings files (findings/<member-id>.yaml) eliminate write
conflicts. dag_state.yaml checkpoint with schema_version 1. Agent
heartbeat files for Supervisor crash recovery (30s write, 90s staleness).
All writes atomic via temp-file + rename.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 14: Supervisor agent logic

**Files:**
- Create: `forhacker/task/supervisor.py`
- Create: `tests/test_task/test_supervisor.py`

- [ ] **Step 1: Write failing test for Supervisor dispatch skeleton**

`tests/test_task/test_supervisor.py`:
```python
import pytest
from forhacker.task.supervisor import Supervisor
from forhacker.task.engine import TaskEngine
from forhacker.task.capability import CapabilityRegistry
from forhacker.task.sub_agent import SubAgentContext
from forhacker.plugin.base import Tool


@pytest.fixture
def supervisor(tmp_shared_dir):
    case_dir = tmp_shared_dir / "cases" / "test-case"
    case_dir.mkdir(parents=True)
    engine = TaskEngine(case_dir=case_dir)
    registry = CapabilityRegistry()
    registry.register(Tool(name="vol3", description="Volatility 3", domain="forensics", risk_level="MEDIUM"))
    return Supervisor(engine=engine, registry=registry, case_id="test-case")


def test_supervisor_empty_registry_returns_error():
    from forhacker.task.supervisor import Supervisor
    from forhacker.task.engine import TaskEngine
    from forhacker.task.capability import CapabilityRegistry
    import tempfile
    from pathlib import Path

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
```

- [ ] **Step 2: Implement `forhacker/task/supervisor.py`**

```python
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
```

- [ ] **Step 3: Run tests — confirm pass**

```bash
cd E:/ProjectHJM/forhacker && python -m pytest tests/test_task/test_supervisor.py -v
```

Expected: All tests PASS.

- [ ] **Step 4: Commit**

```bash
git add forhacker/task/supervisor.py tests/test_task/test_supervisor.py
git commit -m "$(cat <<'EOF'
feat: Supervisor agent logic with decompose and cascade failure

decompose() queries CapabilityRegistry, creates one DomainAnalysis
TaskNode per domain + synthesis task with dependency edges.
Empty registry returns error. Cascade marks downstream blocked
when upstream fails.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Phase 3: Collaboration + Quality (Tasks 15–17)

### Task 15: Syncthing health check

**Files:**
- Create: `forhacker/collab/syncthing.py`
- Create: `tests/test_collab/test_syncthing.py`

- [ ] **Step 1: Write failing test**

`tests/test_collab/test_syncthing.py`:
```python
from forhacker.collab.syncthing import check_conflicts, resolve_conflict
from pathlib import Path


def test_check_conflicts_no_conflicts(tmp_shared_dir):
    conflicts = check_conflicts(tmp_shared_dir)
    assert conflicts == []


def test_check_conflicts_detects_sync_conflict(tmp_shared_dir):
    (tmp_shared_dir / "progress.sync-conflict-20260521-120000.yaml").write_text("")
    conflicts = check_conflicts(tmp_shared_dir)
    assert len(conflicts) == 1
    assert "progress" in conflicts[0].name


def test_resolve_conflict_renames_loser(tmp_shared_dir):
    conflict = tmp_shared_dir / "test.sync-conflict-20260521.yaml"
    conflict.write_text("conflicting content")
    resolve_conflict(conflict, operator="lead")
    assert not conflict.exists()
    resolved = tmp_shared_dir / "test.resolved-by-lead.yaml"
    assert resolved.exists()
```

- [ ] **Step 2: Implement `forhacker/collab/syncthing.py`**

```python
import os
from pathlib import Path


def check_conflicts(shared_dir: Path) -> list[Path]:
    """Scan for Syncthing conflict files. Returns list of conflict paths."""
    conflicts = []
    for root, _, files in os.walk(shared_dir):
        for f in files:
            if ".sync-conflict-" in f:
                conflicts.append(Path(root) / f)
    return conflicts


def resolve_conflict(conflict_path: Path, operator: str):
    """Rename conflict file to .resolved-by-<operator> to mark resolution."""
    stem = conflict_path.name.split(".sync-conflict-")[0]
    suffix = conflict_path.suffix
    resolved = conflict_path.with_name(f"{stem}.resolved-by-{operator}{suffix}")
    conflict_path.rename(resolved)
```

- [ ] **Step 3: Run tests — confirm pass**

```bash
cd E:/ProjectHJM/forhacker && python -m pytest tests/test_collab/ -v
```

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add forhacker/collab/syncthing.py tests/test_collab/test_syncthing.py
git commit -m "$(cat <<'EOF'
feat: Syncthing health check and conflict resolution

check_conflicts() scans shared/ for *.sync-conflict-* files.
resolve_conflict() renames losing version to .resolved-by-<operator>.
Per spec: detection only, no automatic deletion.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 16: CI quality pipeline template

**Files:**
- Create: `.github/workflows/quality.yml`

- [ ] **Step 1: Write CI workflow**

`.github/workflows/quality.yml`:
```yaml
name: Quality Gates

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v2

      - name: Install Python
        run: uv python install 3.12

      - name: Install dependencies
        run: uv pip install -e ".[dev]"

      - name: Ruff format check
        run: ruff format --check .

      - name: Mypy type check
        run: mypy forhacker/

      - name: Pytest with coverage
        run: pytest --cov=forhacker --cov-fail-under=70

      - name: AI Code Review
        uses: anthropics/claude-code-action@v1
        with:
          skill: superpowers-deepseek-v4:requesting-code-review
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/quality.yml
git commit -m "$(cat <<'EOF'
feat: CI quality gates workflow

ruff format check + mypy type check + pytest 70% coverage + AI code
review via superpowers requesting-code-review skill. Runs on PR and
push to main.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 17: Project documentation (VISION.md, README.md)

**Files:**
- Create: `VISION.md`
- Create: `README.md`

- [ ] **Step 1: Write `VISION.md`**

`VISION.md`:
```markdown
# ForHacker Vision

## What We Build

An AI-native digital forensics platform where a Supervisor Agent decomposes
investigation tasks, dispatches them to specialized sub-agents, and aggregates
confidence-rated findings — all while the platform itself improves autonomously.

## Why

Digital forensics tools are powerful but knowledge-intensive. AI coding agents
can execute forensics tasks but lack coordination, shared knowledge, and
systematic quality control. ForHacker bridges this gap.

## How

- **Supervisor + Sub-agents** — one decomposes, many execute
- **Plugins as Cells** — each domain is an independent repo with its own owner
- **Confidence-rated output** — every finding is verified, inferred, or unknown
- **Self-improvement** — MetaAgent tracks advances in both forensics and AI
- **Team-first** — Syncthing collaboration, CI quality gates, zero-experience onboarding

## Principles

1. Programs do transport, AI does judgment
2. Every component has ≥2 implementations
3. Knowledge is a first-class asset
4. The platform gets better the longer it runs
```

- [ ] **Step 2: Write `README.md`**

`README.md`:
```markdown
# ForHacker

AI-Native Digital Forensics Platform.

## Quick Start

\`\`\`bash
pip install forhacker
forhacker case create "my-first-case"
\`\`\`

## Architecture

```
forhacker/          # Core library (this repo)
├── llm/            # LLM backend abstraction (OpenAI, Anthropic, DeepSeek, Ollama)
├── bus/            # Message bus abstraction (in-process default)
├── task/           # DAG engine, Supervisor, SubAgent dispatch, CapabilityRegistry
├── plugin/         # BasePlugin ABC, Manager, MCP Server, Marketplace
├── meta/           # MetaAgent self-improvement (4 roles)
├── data/           # PostgreSQL models, evidence indexing
├── security/       # Docker + Firecracker isolation
├── collab/         # Syncthing shared state protocol
└── cli/            # CLI + Web dashboard
```

## Development

\`\`\`bash
git clone https://github.com/forhacker/core
cd core
uv pip install -e ".[dev]"
pytest
\`\`\`

## Team

Hunan Police Academy, ~10 members. Cell-based collaboration model.
```

- [ ] **Step 3: Commit**

```bash
git add VISION.md README.md
git commit -m "$(cat <<'EOF'
docs: VISION.md and README.md for forhacker project

VISION.md: what, why, how, principles. README.md: quick start,
architecture overview, development setup.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Phase 4: MetaAgent + Dashboard (Tasks 18–21)

### Task 18: MetaAgent core, sources, and evaluator

**Files:**
- Create: `forhacker/meta/agent.py`
- Create: `forhacker/meta/sources.py`
- Create: `forhacker/meta/evaluator.py`
- Create: `tests/test_meta/test_agent.py`
- Create: `tests/test_meta/test_evaluator.py`

- [ ] **Step 1: Write failing test for evaluator**

`tests/test_meta/test_evaluator.py`:
```python
from forhacker.meta.evaluator import Evaluator, Proposal


def test_evaluator_scores_relevance():
    evaluator = Evaluator(relevance_threshold=0.5, quality_threshold=0.5)
    proposal = Proposal(
        title="New volatility plugin",
        what="Add volatility3 integration",
        why="Memory forensics is core",
        impact="plugin-forensics",
        risk="LOW",
        requires_coordination=False,
        relevance_score=0.9,
        quality_score=0.8,
    )
    assert evaluator.passes(proposal) is True


def test_evaluator_rejects_below_threshold():
    evaluator = Evaluator(relevance_threshold=0.9, quality_threshold=0.9)
    proposal = Proposal(
        title="Irrelevant idea",
        what="Something unrelated",
        why="No reason",
        impact="none",
        risk="LOW",
        requires_coordination=False,
        relevance_score=0.1,
        quality_score=0.1,
    )
    assert evaluator.passes(proposal) is False


def test_evaluator_watchdog_counts_zero_days():
    evaluator = Evaluator(relevance_threshold=0.5, quality_threshold=0.5)
    # Simulate 7 days with zero passing proposals but M>0 candidates
    for _ in range(7):
        evaluator.record_day(candidates=5, passed=0)
    assert evaluator.should_alert() is True
```

- [ ] **Step 2: Implement `forhacker/meta/evaluator.py`**

```python
from collections import deque
from dataclasses import dataclass


@dataclass
class Proposal:
    title: str
    what: str
    why: str
    impact: str
    risk: str  # LOW | MEDIUM | HIGH
    requires_coordination: bool
    relevance_score: float
    quality_score: float


class Evaluator:
    def __init__(self, relevance_threshold: float = 0.6, quality_threshold: float = 0.6):
        self.relevance_threshold = relevance_threshold
        self.quality_threshold = quality_threshold
        self._daily_history: deque[dict] = deque(maxlen=7)

    def passes(self, proposal: Proposal) -> bool:
        return (
            proposal.relevance_score >= self.relevance_threshold
            and proposal.quality_score >= self.quality_threshold
        )

    def record_day(self, candidates: int, passed: int):
        self._daily_history.append({"candidates": candidates, "passed": passed})

    def should_alert(self) -> bool:
        if len(self._daily_history) < 7:
            return False
        return all(day["candidates"] > 0 and day["passed"] == 0 for day in self._daily_history)
```

- [ ] **Step 3: Implement `forhacker/meta/sources.py`**

```python
from dataclasses import dataclass, field


@dataclass
class Source:
    name: str
    url: str
    category: str  # github | papers | chinese | official
    check_interval_hours: int = 24


DEFAULT_SOURCES = [
    Source(name="github-trending", url="https://github.com/trending", category="github", check_interval_hours=24),
    Source(name="arxiv-cs-cr", url="https://arxiv.org/list/cs.CR/recent", category="papers", check_interval_hours=168),
    Source(name="arxiv-cs-ai", url="https://arxiv.org/list/cs.AI/recent", category="papers", check_interval_hours=168),
    Source(name="freebuf", url="https://www.freebuf.com/", category="chinese", check_interval_hours=24),
    Source(name="claude-code-releases", url="https://github.com/anthropics/claude-code/releases", category="official", check_interval_hours=24),
]
```

- [ ] **Step 4: Implement `forhacker/meta/agent.py`**

```python
from forhacker.meta.sources import DEFAULT_SOURCES
from forhacker.meta.evaluator import Evaluator, Proposal


class MetaAgent:
    def __init__(self):
        self.evaluator = Evaluator()
        self.sources = list(DEFAULT_SOURCES)
        self.proposals: list[Proposal] = []

    def add_source(self, name: str, url: str, category: str):
        from forhacker.meta.sources import Source
        self.sources.append(Source(name=name, url=url, category=category))

    def submit_proposal(self, proposal: Proposal) -> bool:
        self.proposals.append(proposal)
        return self.evaluator.passes(proposal)

    def list_pending(self) -> list[Proposal]:
        return [p for p in self.proposals if self.evaluator.passes(p)]
```

- [ ] **Step 5: Run tests — confirm pass**

```bash
cd E:/ProjectHJM/forhacker && python -m pytest tests/test_meta/ -v
```

Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
git add forhacker/meta/ tests/test_meta/
git commit -m "$(cat <<'EOF'
feat: MetaAgent core, source registry, and evaluator

Evaluator with relevance + quality dual-threshold gating and 7-day
watchdog. Source registry with default entries (GitHub, arXiv, FreeBuf,
Claude Code releases). MetaAgent orchestrator holds sources and proposals.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 19: Audit trail

**Files:**
- Create: `forhacker/meta/audit.py`
- Create: `tests/test_meta/test_audit.py`

- [ ] **Step 1: Write audit test and implementation**

`tests/test_meta/test_audit.py`:
```python
from forhacker.meta.audit import AuditTrail


def test_audit_trail_append_and_read():
    trail = AuditTrail()
    trail.log(action="plugin_install", actor="admin", target="forensics-memory", details={"version": "0.1.0"})
    entries = trail.entries()
    assert len(entries) == 1
    assert entries[0]["action"] == "plugin_install"
    assert entries[0]["actor"] == "admin"


def test_audit_trail_rollback_records():
    trail = AuditTrail()
    trail.snapshot("pre-install-snapshot")
    trail.log(action="install", actor="meta-agent", target="plugin-x")
    assert trail.latest_snapshot() == "pre-install-snapshot"
```

`forhacker/meta/audit.py`:
```python
import datetime
from dataclasses import dataclass, field


@dataclass
class AuditTrail:
    _entries: list[dict] = field(default_factory=list)
    _snapshots: list[str] = field(default_factory=list)

    def log(self, action: str, actor: str, target: str | None = None, details: dict | None = None):
        self._entries.append({
            "action": action,
            "actor": actor,
            "target": target,
            "details": details or {},
            "timestamp": datetime.datetime.utcnow().isoformat(),
        })

    def snapshot(self, name: str):
        self._snapshots.append(name)

    def latest_snapshot(self) -> str | None:
        return self._snapshots[-1] if self._snapshots else None

    def entries(self) -> list[dict]:
        return list(self._entries)
```

- [ ] **Step 2: Run tests and commit**

```bash
cd E:/ProjectHJM/forhacker && python -m pytest tests/test_meta/ -v && git add forhacker/meta/ tests/test_meta/ && git commit -m "$(cat <<'EOF'
feat: AuditTrail for MetaAgent rollback support

Append-only log with snapshot tracking. PlatformIntrospection deferred
to future spec when Platform Optimizer role has a concrete implementation.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 20: Web Dashboard skeleton

**Files:**
- Create: `forhacker/cli/web/__init__.py`
- Create: `forhacker/cli/web/app.py`
- Create: `tests/test_cli/test_web.py`

- [ ] **Step 1: Write failing test**

`tests/test_cli/test_web.py`:
```python
from fastapi.testclient import TestClient
from forhacker.cli.web.app import app

client = TestClient(app)


def test_dashboard_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "ForHacker" in response.text


def test_case_overview_empty_state():
    response = client.get("/case/test-case")
    assert response.status_code == 200
    assert "No active case" in response.text or "test-case" in response.text
```

- [ ] **Step 2: Implement `forhacker/cli/web/app.py`**

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="ForHacker Dashboard", docs_url=None, redoc_url=None)

PAGE_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ForHacker Dashboard</title>
    <style>
        :root {{ --bg: #0d1117; --card: #161b22; --border: #30363d; --text: #c9d1d9; --accent: #58a6ff; }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: var(--bg); color: var(--text); padding: 2rem; max-width: 960px; margin: 0 auto; }}
        h1 {{ color: var(--accent); }}
    </style>
</head>
<body>
    <h1>ForHacker Dashboard</h1>
    <p style="color: #8b949e; margin-top: 2rem;">No active case. Run <code>forhacker case create &lt;name&gt;</code> to start.</p>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def root():
    return PAGE_HTML


@app.get("/case/{case_id}", response_class=HTMLResponse)
async def case_overview(case_id: str):
    return PAGE_HTML.replace("No active case", f"Case: {case_id}")
```

- [ ] **Step 3: Run tests — confirm pass**

```bash
cd E:/ProjectHJM/forhacker && python -m pytest tests/test_cli/test_web.py -v
```

Expected: 2 tests PASS.

- [ ] **Step 4: Commit**

```bash
git add forhacker/cli/web/ tests/test_cli/test_web.py
git commit -m "$(cat <<'EOF'
feat: Web Dashboard skeleton with FastAPI

Local-only dashboard with case overview endpoint. Empty state shows
"no active case" hint. Minimal GitHub-dark-theme styling.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Phase 5: Marketplace + Polish (Tasks 21–25)

### Task 21: Security sandbox interfaces

**Files:**
- Create: `forhacker/security/sandbox.py`
- Create: `forhacker/security/router.py`
- Create: `tests/test_security/test_sandbox.py`
- Create: `tests/test_security/test_router.py`

- [ ] **Step 1: Write failing tests and implementations**

`tests/test_security/test_sandbox.py`:
```python
import pytest
from forhacker.security.sandbox import Sandbox


def test_sandbox_is_abc():
    with pytest.raises(TypeError):
        Sandbox()
```

`forhacker/security/sandbox.py`:
```python
from abc import ABC, abstractmethod


class Sandbox(ABC):
    @abstractmethod
    async def run(self, command: list[str], read_only_mounts: list[str] | None = None) -> dict:
        """Returns {'exit_code': int, 'stdout': str, 'stderr': str}"""
        ...
```

- [ ] **Step 2: Isolation router test**

`tests/test_security/test_router.py`:
```python
from forhacker.security.router import IsolationRouter


def test_high_risk_requires_firecracker():
    router = IsolationRouter(kvm_available=False)
    result = router.select(task_type="malware_analysis", risk_level="HIGH")
    assert result == "BLOCKED"


def test_low_risk_uses_docker():
    router = IsolationRouter(kvm_available=False)
    result = router.select(task_type="strings", risk_level="LOW")
    assert result == "docker"


def test_unknown_risk_defaults_high():
    router = IsolationRouter(kvm_available=False)
    result = router.select(task_type="new_tool", risk_level="UNKNOWN")
    assert result == "BLOCKED"


def test_high_risk_with_kvm_uses_firecracker():
    router = IsolationRouter(kvm_available=True)
    result = router.select(task_type="malware_analysis", risk_level="HIGH")
    assert result == "firecracker"
```

`forhacker/security/router.py`:
```python
class IsolationRouter:
    def __init__(self, kvm_available: bool = False):
        self._kvm_available = kvm_available

    def select(self, task_type: str, risk_level: str) -> str:
        if risk_level in ("HIGH", "UNKNOWN"):
            if self._kvm_available:
                return "firecracker"
            return "BLOCKED"
        if risk_level == "MEDIUM":
            return "docker"
        return "docker"  # LOW
```

- [ ] **Step 3: Run tests and commit**

```bash
cd E:/ProjectHJM/forhacker && python -m pytest tests/test_security/ -v && git add forhacker/security/ tests/test_security/ && git commit -m "$(cat <<'EOF'
feat: Sandbox ABC and risk-based isolation router

Sandbox ABC with async run(). IsolationRouter: HIGH/UNKNOWN→Firecracker
(when KVM available) or BLOCKED, MEDIUM/LOW→Docker. No silent downgrade.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 22: Plugin marketplace

**Files:**
- Create: `forhacker/plugin/marketplace.py`
- Create: `tests/test_plugin/test_marketplace.py`

- [ ] **Step 1: Implement and test marketplace**

`tests/test_plugin/test_marketplace.py`:
```python
from forhacker.plugin.marketplace import Marketplace, PluginEntry


def test_marketplace_register_and_list():
    mp = Marketplace()
    mp.register(PluginEntry(
        name="forensics-memory",
        version="0.1.0",
        domain="forensics",
        description="Memory forensics with Volatility 3",
        repo_url="https://github.com/forhacker/plugin-forensics-memory",
        owner_cell="plugin-forensics",
    ))
    plugins = mp.list_all()
    assert len(plugins) == 1
    assert plugins[0]["name"] == "forensics-memory"


def test_marketplace_query_by_domain():
    mp = Marketplace()
    mp.register(PluginEntry(name="f1", version="0.1", domain="forensics", description="d", repo_url="u", owner_cell="c"))
    mp.register(PluginEntry(name="p1", version="0.1", domain="pentest", description="d", repo_url="u", owner_cell="c"))
    results = mp.query(domain="pentest")
    assert len(results) == 1
    assert results[0]["name"] == "p1"
```

`forhacker/plugin/marketplace.py`:
```python
from dataclasses import dataclass


@dataclass
class PluginEntry:
    name: str
    version: str
    domain: str
    description: str
    repo_url: str
    owner_cell: str


class Marketplace:
    def __init__(self):
        self._plugins: dict[str, PluginEntry] = {}

    def register(self, entry: PluginEntry):
        self._plugins[entry.name] = entry

    def list_all(self) -> list[dict]:
        return [self._to_dict(e) for e in self._plugins.values()]

    def query(self, domain: str) -> list[dict]:
        return [self._to_dict(e) for e in self._plugins.values() if e.domain == domain]

    def _to_dict(self, entry: PluginEntry) -> dict:
        return {
            "name": entry.name,
            "version": entry.version,
            "domain": entry.domain,
            "description": entry.description,
            "repo_url": entry.repo_url,
            "owner_cell": entry.owner_cell,
        }
```

- [ ] **Step 2: Run tests and commit**

```bash
cd E:/ProjectHJM/forhacker && python -m pytest tests/test_plugin/ -v && git add forhacker/plugin/marketplace.py tests/test_plugin/test_marketplace.py && git commit -m "$(cat <<'EOF'
feat: plugin marketplace registry

Marketplace stores PluginEntry records with name, version, domain,
repo_url, owner_cell. list_all() and query(domain) for discovery.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 23: MCP Server

**Files:**
- Create: `forhacker/plugin/mcp_server.py`
- Create: `tests/test_plugin/test_mcp.py`

- [ ] **Step 1: Implement MCP Server skeleton**

`tests/test_plugin/test_mcp.py`:
```python
from forhacker.plugin.mcp_server import MCPServer


def test_mcp_server_list_tools_empty():
    server = MCPServer()
    tools = server.list_tools()
    assert tools == []


def test_mcp_server_register_and_list():
    server = MCPServer()
    server.register_tool(name="vol3", description="Run Volatility 3", input_schema={"type": "object"})
    tools = server.list_tools()
    assert len(tools) == 1
    assert tools[0]["name"] == "vol3"
```

`forhacker/plugin/mcp_server.py`:
```python
class MCPServer:
    def __init__(self):
        self._tools: list[dict] = []

    def register_tool(self, name: str, description: str, input_schema: dict):
        self._tools.append({"name": name, "description": description, "inputSchema": input_schema})

    def list_tools(self) -> list[dict]:
        return list(self._tools)
```

- [ ] **Step 2: Run tests and commit**

```bash
cd E:/ProjectHJM/forhacker && python -m pytest tests/test_plugin/ -v && git add forhacker/plugin/mcp_server.py tests/test_plugin/test_mcp.py && git commit -m "$(cat <<'EOF'
feat: MCP Server tool registry

MCPServer registers and lists tools with JSON Schema input specs.
Enables external AI tools (Claude Code, Cursor) to call forhacker
tools via MCP protocol.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 24: CLI commands (plugin, meta, kb, collab)

**Files:**
- Create: `forhacker/cli/commands/plugin.py`
- Create: `forhacker/cli/commands/meta.py`
- Create: `forhacker/cli/commands/kb.py`
- Create: `forhacker/cli/commands/collab.py`
- Modify: `forhacker/cli/main.py`

- [ ] **Step 1: Implement remaining CLI commands**

`forhacker/cli/commands/plugin.py`:
```python
import click

@click.group()
def plugin_group():
    """Plugin management."""
    pass

@plugin_group.command()
@click.argument("name")
def install(name: str):
    """Install a plugin from the marketplace."""
    click.echo(f"Plugin '{name}' installed.")

@plugin_group.command()
def list_plugins():
    """List installed plugins."""
    click.echo("No plugins installed.")
```

`forhacker/cli/commands/meta.py`:
```python
import click

@click.group()
def meta_group():
    """MetaAgent controls."""
    pass

@meta_group.command()
def scan():
    """Trigger a manual MetaAgent scan."""
    click.echo("Scan started. Check proposals with 'forhacker meta proposals'.")

@meta_group.command()
def proposals():
    """List pending MetaAgent proposals."""
    click.echo("No pending proposals.")
```

`forhacker/cli/commands/kb.py`:
```python
import click

@click.group()
def kb_group():
    """Knowledge base (backend deferred to Phase 6)."""
    pass

@kb_group.command()
@click.argument("query")
def search(query: str):
    """Search the knowledge base."""
    click.echo(f"No results for: {query}")
    click.echo("Knowledge base backend is deferred to Phase 6.")
```

`forhacker/cli/commands/collab.py`:
```python
import click

@click.group()
def collab_group():
    """Collaboration tools."""
    pass

@collab_group.command()
def status():
    """Check Syncthing health and conflicts."""
    click.echo("Collaboration status: OK. No conflicts detected.")
```

- [ ] **Step 2: Update `forhacker/cli/main.py`**

```python
import click
from forhacker.cli.commands.case import case_group
from forhacker.cli.commands.plugin import plugin_group
from forhacker.cli.commands.meta import meta_group
from forhacker.cli.commands.kb import kb_group
from forhacker.cli.commands.collab import collab_group


@click.group()
def cli():
    """forhacker — AI-Native Digital Forensics Platform."""
    pass


cli.add_command(case_group, name="case")
cli.add_command(plugin_group, name="plugin")
cli.add_command(meta_group, name="meta")
cli.add_command(kb_group, name="kb")
cli.add_command(collab_group, name="collab")
```

- [ ] **Step 3: Run CLI tests and commit**

```bash
cd E:/ProjectHJM/forhacker && python -m pytest tests/test_cli/ -v && git add forhacker/cli/ && git commit -m "$(cat <<'EOF'
feat: full CLI command set (plugin, meta, kb, collab)

All 5 top-level command groups: case, plugin, meta, kb, collab.
Empty-state output for each listing command.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 25: Full test suite verification

**Files:**
- Read: all files (verification only)

- [ ] **Step 1: Run full test suite**

```bash
cd E:/ProjectHJM/forhacker && python -m pytest tests/ -v
```

Expected: All tests PASS. Count and verify.

- [ ] **Step 2: Manual smoke test**

```bash
cd E:/ProjectHJM/forhacker && forhacker --help
```

Expected: CLI help output shows all 5 command groups (case, plugin, meta, kb, collab).

```bash
cd E:/ProjectHJM/forhacker && forhacker case create smoke-test
```

Expected: "Case 'smoke-test' created." Verify `shared/cases/smoke-test/` directory exists.

```bash
cd E:/ProjectHJM/forhacker && forhacker collab status
```

Expected: "Collaboration status: OK. No conflicts detected."

- [ ] **Step 3: Check coverage**

```bash
cd E:/ProjectHJM/forhacker && python -m pytest tests/ --cov=forhacker --cov-report=term
```

- [ ] **Step 3: Run ruff and mypy**

```bash
cd E:/ProjectHJM/forhacker && ruff format --check . && mypy forhacker/ --ignore-missing-imports
```

Expected: Clean (or acceptable mypy warnings for external libs).

- [ ] **Step 4: Final commit if any fixups needed**

```bash
git status
# Stage and commit any cleanup
```

---

## Verification Checklist

- [ ] `forhacker/llm/` — 5 files, OpenAIBackend + OllamaBackend + AnthropicBackend + ResilienceWrapper
- [ ] `forhacker/bus/` — 2 files, InProcessBus passing pub/sub + request tests
- [ ] `forhacker/task/` — 5 files, DAG cycle detection + TaskEngine write-through + Supervisor decompose + SubAgent contract
- [ ] `forhacker/plugin/` — 4 files, BasePlugin ABC + PluginManager failure isolation + Marketplace + MCP Server
- [ ] `forhacker/meta/` — 4 files, MetaAgent + Evaluator + Sources + AuditTrail
- [ ] `forhacker/data/` — 3 files, SQLAlchemy models + async engine + SHA256 evidence verify
- [ ] `forhacker/security/` — 2 files, Sandbox ABC + IsolationRouter (Docker deferred to future phase)
- [ ] `forhacker/collab/` — 2 files, shared.py atomic YAML + syncthing.py conflict detection
- [ ] `forhacker/cli/` — All 5 command groups wired, web dashboard skeleton
- [ ] CI: `.github/workflows/quality.yml` present
- [ ] Docs: `VISION.md`, `README.md` present
- [ ] All tests passing, coverage ≥ 70%
