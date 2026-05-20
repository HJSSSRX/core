# ForHacker: AI-Native Digital Forensics Platform

**Date:** 2026-05-21
**Status:** Reviewed (2-round multi-reviewer, converged)
**Based On:** Phase A Alignment (2026-05-20-forhacker-brainstorm.md, 22 decisions)

## Problem

Existing digital forensics tools are powerful but knowledge-intensive — their capabilities live in the operator's head, not the software. AI coding agents (Claude Code, Cursor, Codex) can execute forensics tasks but lack structure: no coordination between agents, no shared knowledge accumulation, no systematic quality control.

The team (Hunan Police Academy students, ~10 members, varying skill levels) previously built a prompt-driven forensics system that became bloated, untestable, and impossible to collaborate on. Three root causes were identified:

1. **Prompt-driven, not code-driven** — AI prompts are hard to version, test, or compose. The system was a collection of Markdown files with no executable core.
2. **No quality gates** — AI output went directly into the knowledge base without verification. Errors accumulated silently.
3. **File-system chaos** — prompts, tools, knowledge, and shared state were interleaved in one directory with no separation of concerns.

The team needs a platform where: (a) a Supervisor Agent decomposes investigation tasks and dispatches them to specialized sub-agents, (b) every result is verified and confidence-rated, (c) knowledge accumulates automatically across cases, (d) the platform itself improves by tracking advances in both forensics techniques and AI/agent methodology, and (e) team members of all skill levels can contribute meaningfully through AI pair-programming within well-defined plugin boundaries.

## Empirical Foundations

This spec is based on concrete evidence from the old project and team environment:

| Finding | Source | Implication |
|---------|--------|-------------|
| Old project (~8 months) became bloated, unmergeable, zero tests | `E:\项目\自动化取证\` post-mortem | Module boundaries + CI gates are non-negotiable |
| Markdown-based prompts unversionable, untestable | Old project DESIGN.md | All logic goes through executable Python code; prompts are YAML-configurable strings |
| 10-person team, 3 zero-base, weekly 2×2h sync | Team survey (Phase A Q14) | Cell model, scaffolding CLI, TUTORIAL.md per Cell |
| Server 2C8G20G can't store evidence (hundreds of GB) | Infrastructure audit (Phase A Q21) | PostgreSQL metadata only; evidence local per machine |
| DeepSeek latency ~2-5s/request vs OpenAI ~0.5s | Spot testing 2026-05 | Sensitivity router critical; local model fallback for offline competitions |
| Syncthing LAN sync <1s, WAN relay ~3-10s | Spot testing 2026-05 | Acceptable for YAML/MD sync; conflict detection still required |
| Claude Code + Superpowers workflow validated on this spec | This document's own creation process | The multi-reviewer subsystem, brainstorming, and plan workflows work on DeepSeek-V4-Pro |

## Goals

1. **Core Agent Framework** — Supervisor + sub-agent dispatch with LLM-agnostic backend, abstract MessageBus, and DAG-based task engine
2. **Plugin System** — Python ABC + MCP Server dual-mode, with scaffolding CLI and internal marketplace
3. **MetaAgent** — four-role self-improvement agent (research scout, continuous observer, web operator, platform optimizer) with scheduled scan + human-approval gate + audit trail + rollback
4. **Team Collaboration** — Cell-based repo structure, Syncthing-powered shared state, CI-enforced quality gates, AI Code Review on every PR
5. **Knowledge Accumulation** — shared knowledge-base repo with CI auto-ingestion from Cell repos, tag-based search with no external dependencies
6. **Competition-Ready** — Supervisor-driven task dispatch for CTF/forensics matches, works both online (cloud LLM) and offline (local model)
7. **Security Isolation** — Docker for routine tasks, WSL2 Firecracker microVM for high-risk analysis, read-only evidence mounts

## Non-Goals

- Mobile forensics hardware acquisition (cellebrite-style) — out of scope
- Real-time network intrusion detection — out of scope
- Production-grade evidence management for court-admissible chains of custody — Phase 2+
- GUI desktop application — CLI-first, Web dashboard is read-only visualization
- Mobile client for agent interaction — separate project at `E:\ProjectHJM\手机操控agent`
- Offline competition collaboration plugin — reserved slot, not implemented until team qualifies for offline finals
- MinIO/S3 object storage — server disk too small (20GB), evidence stored locally per machine

## Design Principles

### 1. Abstractions with fallbacks, not abstractions with lock-in

Every infrastructure component (LLM backend, MessageBus, isolation runtime) exposes an abstract interface with at least two implementations: a zero-dependency default for single-machine/offline use and an optional scaled implementation for team/online use. Agent code never imports a specific backend directly.

### 2. Programs do transport, AI does judgment

The boundary is absolute: file synchronization, hash verification, format validation, tool execution, and CI checks are deterministic programs. AI agents handle interpretation, correlation, strategy, and generation. AI never calls HTTP for collaboration — it reads and writes local files; Syncthing handles the network.

### 3. Confidence-rated, not binary

Every agent output carries a confidence level: ✅ Verified (tool output directly supports), ⚠️ Inferred (AI reasoning, plausible but unconfirmed), ❌ Unknown (insufficient data). The platform flags ⚠️ findings for human review. This is the three-state output principle inherited from the old project.

### 4. Cell autonomy, core coherence

Each plugin repo (Cell) operates independently with its own owner, CI, and pace. The core repository enforces interface contracts (plugin API, MCP schema, finding format) that all Cells must satisfy. Cells can experiment freely within their boundaries; the core changes only through reviewed PRs.

### 5. Knowledge is a first-class asset

Every case, every task, every finding feeds into a shared knowledge base. The knowledge base is plain Markdown + YAML frontmatter — human-readable, git-diffable, zero-dependency searchable. It is not a database; it is a garden that grows with use.

### 6. Self-improvement is infrastructure, not an afterthought

The MetaAgent is not a plugin — it is a core subsystem that runs on schedule, scans external sources, evaluates relevance, and files structured improvement proposals. The platform gets better the longer it runs.

## Design

### 1. Core Framework Architecture

> **Design Rationale (Q2, Q4, Q6):** The core is a library, not a service. Every subsystem exposes an ABC with ≥2 implementations — this is not future-proofing, it's a hard constraint from the offline-competition requirement. The Supervisor pattern was chosen over peer-to-peer because forensics tasks have a natural decomposition hierarchy (triage → deep-dive → correlate) that maps to a DAG better than to a mesh.

```
forhacker-core/
├── forhacker/
│   ├── llm/
│   │   ├── backend.py          # LLMBackend ABC
│   │   ├── openai.py           # OpenAI-compatible backend
│   │   ├── anthropic.py        # Anthropic backend
│   │   ├── deepseek.py         # DeepSeek backend
│   │   ├── ollama.py           # Ollama (local) backend
│   │   └── router.py           # Sensitivity-based router (local vs cloud)
│   │
│   ├── bus/
│   │   ├── message_bus.py      # MessageBus ABC
│   │   └── in_process.py       # Default: in-process, zero-dependency
│   │
│   ├── task/
│   │   ├── engine.py           # DAG engine with dynamic node addition
│   │   ├── supervisor.py       # Supervisor Agent logic
│   │   ├── sub_agent.py        # Sub-agent dispatch and lifecycle
│   │   ├── dag.py              # DAG data structure and operations
│   │   └── capability.py       # CapabilityRegistry (tool/agent lookup, owned by task/)
│   │
│   ├── plugin/
│   │   ├── base.py             # BasePlugin ABC
│   │   ├── manager.py          # Plugin discovery, loading, lifecycle
│   │   ├── mcp_server.py       # MCP Server for external tool exposure
│   │   └── marketplace.py      # Internal plugin registry
│   │
│   ├── meta/
│   │   ├── agent.py            # MetaAgent core (four-role orchestrator)
│   │   ├── sources.py          # Source registry (GitHub, arXiv, B站, blogs...)
│   │   ├── evaluator.py        # Content relevance and quality evaluator
│   │   ├── introspection.py    # PlatformIntrospection (read-only system surface)
│   │   ├── browser.py          # Playwright browser engine
│   │   └── audit.py            # Audit trail and rollback manager
│   │
│   ├── data/
│   │   ├── db.py               # PostgreSQL connection and migration manager
│   │   ├── models.py           # SQLAlchemy models (Case, Task, Finding, AuditLog)
│   │   └── evidence.py         # Evidence index (path + hash + case relation)
│   │
│   ├── security/
│   │   ├── sandbox.py          # Sandbox ABC
│   │   ├── docker.py           # Docker container isolation
│   │   ├── firecracker.py      # WSL2 Firecracker microVM isolation
│   │   └── router.py           # Risk-based isolation level selector
│   │
│   ├── collab/
│   │   ├── shared.py           # Shared state reader/writer (YAML/MD files)
│   │   └── syncthing.py        # Syncthing health check
│   │
│   └── cli/
│       ├── main.py             # CLI entry point (click/typer)
│       ├── commands/           # Subcommands (case, task, plugin, meta, kb)
│       └── web/                # Local Web dashboard (FastAPI + Jinja2)
│
├── tests/                      # Core test suite
├── docs/                       # Core documentation
└── pyproject.toml
```

#### 1.1 LLMBackend Abstraction

```python
class Message:
    role: Literal["system", "user", "assistant", "tool"]
    content: str

class LLMBackend(ABC):
    """Unified interface for all LLM providers."""
    
    @abstractmethod
    async def complete(self, messages: list[Message], tools: list[dict] | None = None, **kwargs) -> LLMResponse: ...
    
    @abstractmethod
    async def stream(self, messages: list[Message], tools: list[dict] | None = None, **kwargs) -> AsyncIterator[str]: ...
    
    @property
    @abstractmethod
    def model_name(self) -> str: ...
    
    @property
    @abstractmethod
    def supports_streaming(self) -> bool: ...

class LLMResponse:
    text: str
    model: str
    tokens_used: int
    finish_reason: str
    tool_calls: list[dict] | None  # structured tool invocations from model
```

**Backend selection** is controlled by a global `FORHACKER_OFFLINE` environment variable and a per-agent `sensitivity_level` tag:

| Condition | Backend | Use Case |
|-----------|---------|----------|
| `sensitivity=high` | Local model | Evidence content analysis |
| `sensitivity=low` | Cloud API | Report formatting, code generation |
| `FORHACKER_OFFLINE=1` | Local model | All requests (overrides sensitivity) |

**Resilience**: Every LLM call is wrapped with: (a) configurable timeout (default 120s), (b) exponential backoff with jitter for retryable errors (429, 5xx), max 3 retries, (c) circuit breaker opening after 5 consecutive failures with 60s cooldown. Unrecoverable errors (4xx auth) propagate immediately. `finish_reason=length` triggers retry with increased max_tokens; if persistent, the result is flagged `confidence=unknown` with a truncation warning.

#### 1.2 MessageBus Abstraction

```python
class MessageBus(ABC):
    @abstractmethod
    async def publish(self, topic: str, message: dict) -> None: ...
    
    @abstractmethod
    async def subscribe(self, topic: str, handler: Callable) -> None: ...
    
    @abstractmethod
    async def request(self, target: str, payload: dict) -> dict: ...
```

**Default implementation** (`InProcessBus`): Python `asyncio.Queue` per topic, zero setup. A distributed bus (Redis/NATS) is deferred until a concrete cross-machine message-passing scenario emerges beyond file-based Syncthing collaboration.

#### 1.3 Task Engine (DAG + Dynamic)

The DAG engine models an investigation as a directed acyclic graph of tasks:

```yaml
task_id: T-001
type: evidence_analysis
status: pending | running | done | failed | blocked
assigned_to: agent_id | cell_name
depends_on: [T-000]
artifacts: [path/to/output]
confidence: HIGH | MEDIUM | LOW
```

**Dynamic addition**: Agents can call `engine.add_task(parent_id, new_task) -> AddTaskResult` at runtime when new leads emerge. `add_task()` performs cycle detection on every call — tasks that would create cycles are rejected with `AddTaskResult(status="rejected_cycle")`. On success (`status="added"`), the new task is immediately written-through to `dag_state.yaml` (atomic: write temp file, rename) so dynamic tasks survive Supervisor crashes between checkpoints. `AddTaskResult` statuses: `added` | `rejected_cycle` | `rejected_duplicate`.

**Supervisor logic**:
1. Receive high-level goal (e.g., "analyze this disk image for data exfiltration evidence")
2. Query CapabilityRegistry for matching tools and techniques (see §1.4)
3. Decompose into initial task DAG
4. Persist DAG state to `shared/cases/<id>/dag_state.yaml` (checkpoint before dispatch)
5. Dispatch ready tasks (dependencies satisfied) to sub-agents via SubAgentContext
6. Monitor completion with heartbeat check (30s interval, 90s staleness → reassign), aggregate findings, trigger new tasks as needed
7. On failure of any task: cascade-mark downstream dependents as `failed` with reason "dependency <id> failed"; Supervisor may override with retry/reassign
8. Produce final report with confidence-rated findings

**Supervisor crash recovery**: On startup, read `dag_state.yaml`. Scan all tasks with `status=running` — check agent heartbeats. Orphaned tasks (no heartbeat within 90s) are reassigned or marked `failed` with reason "supervisor_restart". Task state is persisted to shared/ BEFORE dispatch.

**Task cascade failure**: When a task transitions to `failed`, the Supervisor evaluates the failure before propagating. It may choose to retry/reassign the failed task directly, preventing cascade. If the Supervisor decides not to retry, all downstream dependents are marked `failed` with reason "dependency <id> failed". State machine: `pending → running → done|failed`, `blocked → running` (deps satisfied), `blocked → failed` (any dep fails, Supervisor chooses not to retry), `failed → blocked` (failed dependency was retried and succeeded — dependents revert to blocked for re-evaluation).

**SubAgent execution contract**:

```python
class SubAgentContext:
    task_id: str
    case_id: str
    goal: str
    evidence_paths: list[str]
    available_tools: list[Tool]
    dependency_findings: list[Finding]  # findings from completed upstream tasks
    config: dict

class SubAgentResult:
    findings: list[Finding]
    confidence: str  # per Design Principle 3
    artifacts: list[str]  # paths to produced files
    status: str  # "done" | "failed"
    error: str | None

class SubAgentLifecycle(Enum):
    INIT = "initialized"
    EXECUTING = "executing"
    REPORTING = "reporting"
    DONE = "done"
    FAILED = "failed"
```

#### 1.4 Plugin System

**Plugin ABC**:
```python
class BasePlugin(ABC):
    name: str
    version: str
    domain: str  # forensics, pentest, osint, ctf
    risk_levels: dict[str, str]  # tool_name → LOW|MEDIUM|HIGH (required for security router)
    
    @abstractmethod
    def register_tools(self) -> list[Tool]: ...
    
    @abstractmethod
    def register_mcp_resources(self) -> list[MCPResource]: ...
```

**CapabilityRegistry** (in `task/capability.py`, owned by `task/`, implemented by `plugin/`):
```python
class CapabilityRegistry:
    def register(self, tool: Tool) -> None: ...
    def query(self, domain: str, tags: list[str]) -> list[Tool]: ...
    def list_domains(self) -> list[str]: ...
```

The PluginManager (`plugin/manager.py`) imports the ABC from `task/capability.py` and populates it at load time. The Supervisor imports this interface (not PluginManager internals) for task decomposition step 2. Dependency direction: `plugin/ → task/capability.py` (plugins depend on core contracts). When the registry is empty (zero plugins loaded), the Supervisor returns an error: "No tools available for domain <domain>. Register plugins first." — a zero-task DAG is not a valid outcome.

**Plugin load failure**: Each plugin loads in an isolated try/except. A failed plugin is skipped with a logged error and added to a `degraded_plugins` list visible in `forhacker plugin list --status`. Plugin dependency resolution uses topological sort with cycle detection — circular dependencies (A→B→A) cause both plugins to be rejected with a cycle report. If a plugin declares `dependencies: [other_plugin]` and a dependency fails to load or is in a rejected cycle, the dependent plugin is also skipped with a "missing dependency: <name>" message. The system remains functional with degraded capabilities.

**MCP dual-mode**: The core runs an MCP Server that exposes plugin tools as MCP endpoints. External AI tools (Claude Code, Cursor) can call forhacker tools via MCP without importing Python code.

**Scaffolding CLI**:
```bash
forhacker plugin create forensics-memory
# Generates:
#   plugin-forensics-memory/
#   ├── pyproject.toml
#   ├── src/plugin.py          # BasePlugin subclass skeleton
#   ├── src/tools/             # Tool implementations
#   ├── tests/
#   ├── knowledge/
#   ├── README.md
#   └── TUTORIAL.md
```

**Marketplace**: A `plugins.yaml` registry in the core repo listing available plugins with version, owner Cell, and compatibility. `forhacker plugin install <name>` fetches from the corresponding GitHub repo.

### 2. MetaAgent Subsystem

#### 2.1 Four Roles

| Role | Trigger | Output |
|------|---------|--------|
| **Design Scout** | Brainstorming session start | Research summary: existing solutions, papers, repos relevant to current design task |
| **Continuous Observer** | Daily cron (configurable) | Improvement proposals as structured Issues with: what, why, impact assessment, risk |
| **Web Operator** | On-demand (OSINT/forensics tasks) | Web search results, scraped content, structured intelligence |
| **Platform Optimizer** | Daily cron (shared with Observer) | Suggestions for better AI/agent patterns, new Claude Code features, skill improvements |

#### 2.2 Sources

```yaml
sources:
  github:
    - trending repos (daily)
    - specific orgs: anthropics, anthropics-skills, langchain-ai
    - keyword watch: "ctf-forensics", "dfir", "volatility", "agent-framework"
  papers:
    - arxiv: cs.CR, cs.AI, cs.CL (weekly)
    - scholar alerts: "digital forensics + AI", "multi-agent + security"
  chinese:
    - blogs: 先知社区, FreeBuf, 安全客, CSDN-取证板块
    - video: B站-电子取证, B站-AI Agent
    - forums: 看雪, 吾爱破解
  official:
    - Claude Code release notes
    - Superpowers release notes
    - DeepSeek API changelog
```

#### 2.3 Approval Flow

```
MetaAgent finds candidate improvement
  → Evaluator scores relevance (>threshold) and quality (>threshold)
  → Generates structured Proposal:
      title: "..."
      what: "..."          # What to add/change
      why: "..."           # Why it matters
      impact: "..."        # What subsystems are affected
      risk: LOW|MEDIUM|HIGH
      requires_coordination: true|false  # Does this need cross-project changes?
  → Files as Issue in appropriate repo
  → Human reviews via GitHub/phone
  → If approved:
      → Backup current state
      → Execute installation/change
      → Log to audit trail
      → Report completion
  → If rejected:
      → Log rejection reason
      → Optionally refine and re-propose later
```

**Rollback**: Every MetaAgent-triggered change creates a backup snapshot. `forhacker meta rollback <change-id>` restores previous state. Audit log is append-only. Changes are transactional where possible: new files written to staging directory then atomically swapped. Each step is logged to audit trail BEFORE execution. On rollback failure, the system enters a quarantined state with a clear message listing reverted vs. un-reverted steps. `forhacker meta verify` checks integrity of all backup snapshots.

**Scan mutex**: Before starting a scan, MetaAgent acquires a lease (`meta_scan_lock` row in PostgreSQL with `SELECT ... FOR UPDATE SKIP LOCKED`, or file-based lock in `shared/meta_scan.lock`). If the lock is held (previous scan still in progress), the scheduled run is skipped with a log: "previous scan still in progress." A `MAX_SCAN_DURATION` timeout (default 6 hours) force-releases stale locks. The file-based lock is best-effort: in a Syncthing-shared directory, two nodes may concurrently create the lock file before seeing each other's version (TOCTOU race). The post-hoc safeguard is proposal deduplication — before filing a new proposal, MetaAgent checks existing open proposals for semantic similarity (same title prefix or >90% body overlap via minhash). If a near-duplicate proposal already exists, the new one is discarded with a log: "duplicate proposal suppressed (matches existing #<id>)."

**Evaluator watchdog**: Two separate alert conditions: (a) M=0 case — no candidates found at all (source configuration may be broken), alert: "MetaAgent found zero candidates — check source registry." (b) M>0 case — candidates found but none passed threshold for 7 consecutive days, alert: "MetaAgent evaluator may be too strict — 0 of M candidates passed threshold." The highest-scoring-but-rejected candidates are logged for human spot-check. The evaluator's own pass rate is tracked as a metric.

**Platform Introspection Interface** (used by Platform Optimizer role):

```python
class PlatformIntrospection(ABC):
    """Read-only introspection surface for the Platform Optimizer to assess current state."""
    
    @abstractmethod
    def list_registered_plugins(self) -> list[PluginInfo]: ...
    
    @abstractmethod
    def get_skill_configurations(self) -> dict[str, Any]: ...
    
    @abstractmethod
    def get_recent_metrics(self, window_seconds: float) -> dict[str, Any]: ...
```

Located at `meta/introspection.py`. Implementations query the live PluginManager, skill registry, and metrics store respectively. This is a read-only query interface — the Platform Optimizer cannot mutate system state through it.

### 3. Data Layer

#### 3.1 PostgreSQL Schema (core tables)

```sql
cases (id, name, status, created_at, lead_investigator)
tasks (id, case_id, parent_task_id, type, status, assigned_to, task_confidence, created_at)
findings (id, case_id, task_id, type, summary, task_confidence, evidence_confidence, evidence_ref, created_by, last_ingested_at)
audit_log (id, action, actor, target, details_json, created_at)
evidence_index (id, case_id, path, sha256, file_type, size_bytes, indexed_at, integrity)
agents (id, name, role, cell, status, last_heartbeat)
meta_proposals (id, source, title, status, risk_level, approved_by, executed_at, rollback_snapshot)
meta_scan_lock (id, locked_at, locked_by, expires_at)  -- MetaAgent scan mutex
```

**Agent heartbeat**: Agents heartbeat every 30s by writing `shared/agents/<agent-id>/heartbeat.yaml` (schema_version: 1, fields: agent_id, timestamp, current_task_id). After 3 missed heartbeats (90s), agent is marked `status=dead`. The Supervisor scans for dead agents and reassigns their running tasks or marks them `failed` with reason "agent_unreachable". Heartbeat files serve both the hot path (in-process file stat) and cold path (PostgreSQL `agents.last_heartbeat`). In degraded mode, the Supervisor reads heartbeat timestamps directly from `shared/agents/*/heartbeat.yaml`.

**PostgreSQL degraded mode**: When PostgreSQL is unreachable, the system falls back to the `shared/` YAML files as the operational data store. Core operations (task dispatch, finding write, answer aggregation) work entirely from `shared/`. Two additional structures are replicated to `shared/` for degraded-mode completeness: `shared/evidence_index.yaml` (mirrors the `evidence_index` table — path, sha256, integrity status per file) and `shared/agents/<agent-id>/heartbeat.yaml` (agent liveness). When PostgreSQL connectivity is restored, a reconciliation sync merges `shared/` state into the database. Reconciliation compares per-record timestamps — for each record present in both stores, the version with the later `updated_at` wins; records present only in one store are copied to the other. Conflicts (same timestamp, different content) are logged to `shared/reconciliation_conflicts.yaml` for manual resolution. For single-machine/offline use, SQLite is an available lightweight alternative configured via `FORHACKER_DB=sqlite`.

**Data access — two-path model**:

| Path | Subsystems | Storage | Interface | Purpose |
|------|-----------|---------|-----------|---------|
| Hot (operational) | `task/`, `collab/` | `shared/` YAML via `collab/shared.py` | `shared.py` reader/writer | Task dispatch, findings, answers, DAG checkpoint, real-time Syncthing distribution |
| Cold (durable) | `data/`, `meta/`, `cli/` | PostgreSQL via `data/models.py` (SQLAlchemy) | SQLAlchemy models | Historical queries, KB pipeline, audit trail, metrics, MetaAgent proposals |

The dependency is one-directional: `data/` does not import from `task/`, `meta/`, or `collab/`. `task/` depends on `collab/shared.py` for shared state I/O; `collab/` does not import from `task/`. Repository interfaces are deferred (see Future Considerations).

**Confidence taxonomy — two columns**: Findings carry two separate confidence fields:
- `task_confidence` (HIGH | MEDIUM | LOW) — how confident the Supervisor is in the task decomposition and assignment. Reflects tool match quality and agent capability.
- `evidence_confidence` (verified | inferred | unknown) — how well the finding is supported by tool output. Maps to Design Principle 3: ✅ verified (tool output directly supports), ⚠️ inferred (AI reasoning, plausible but unconfirmed), ❌ unknown (insufficient data).

KB ingestion maps both: `task_confidence` → KB entry `confidence` field; `evidence_confidence` → KB entry quality tier. Entries with `evidence_confidence=unknown` are ingested with a `needs_review: true` flag.

#### 3.2 Evidence Storage

Evidence files live on each team member's local machine under `cases/<case-id>/evidence/`. The `evidence_index` table tracks which files exist where, with SHA256 for integrity verification. Syncthing syncs only the YAML/JSON/MD files in `shared/`, never the evidence binaries.

**Hash verification**: Before any task consumes evidence, SHA256 is verified against the indexed value. On mismatch: (a) a CRITICAL alert is raised, (b) the evidence is marked `integrity=failed` in `evidence_index`, (c) the task is blocked from execution, (d) the mismatch is logged to `audit_log` with expected and actual hash values. Evidence that has been registered but not yet verified (e.g., newly added to a case) carries `integrity=missing` — it is treated as unverified and blocked from consumption until `forhacker evidence verify` confirms the hash. `forhacker evidence verify <case-id>` re-scans all evidence and reports integrity status per file.

**Orphan cleanup**: A scheduled job (daily) scans `evidence_index` for entries whose `path` no longer exists on any team member's filesystem. Orphans are flagged `integrity=orphan` and surfaced in `forhacker evidence verify` output. Manual cleanup via `forhacker evidence purge-orphans <case-id>` removes orphan entries after operator confirmation. This prevents the index from accumulating dead references from deleted or moved evidence files.

### 4. Security Isolation

| Risk Level | Task Examples | Isolation | Network | Fallback if KVM unavailable |
|------------|--------------|-----------|---------|---------------------------|
| LOW | strings, metadata extraction, hash computation | Docker container, read-only evidence | Allowed | Docker (unchanged) |
| MEDIUM | File parsing, archive extraction, log analysis | Docker container, read-only evidence | Restricted | Docker (unchanged) |
| HIGH | Malware analysis, exploit verification, suspicious binary execution | WSL2 Firecracker microVM | Full isolation, ephemeral disk | **BLOCKED** — error: "KVM unavailable, Firecracker required" |
| UNKNOWN | Any task type not in the risk registry | **Defaults to HIGH** (conservative) | Full isolation | **BLOCKED** (same as HIGH) |

**Override**: Human operator can force a lower isolation tier with `--force-docker` flag. Every override is logged to `audit_log` with operator identity, task ID, and rationale.

**Plugin risk declaration**: Each plugin's `risk_levels` dict maps tool names to LOW/MEDIUM/HIGH. The isolation router reads this mapping. Unregistered tool names default to HIGH with a warning: "Task type '<name>' has no defined risk level — defaulting to HIGH." A plugin that declares `risk_levels: {}` (empty dict) means all of its tools default to HIGH — this is valid but should be intentional. The scaffolding template pre-fills `risk_levels` with `# TODO: assign LOW|MEDIUM|HIGH per tool` to make the omission visible.

### 5. Team Collaboration Infrastructure

#### 5.1 Repository Organization

```
github.com/forhacker/
├── core/                    # Core framework (you + 2 design seniors)
├── plugin-forensics/        # Forensics plugin (2 competition veterans)
├── plugin-pentest/          # Pentest plugin (1 veteran + 1 junior)
├── plugin-osint/            # OSINT plugin (1 mid + 1 junior)
├── plugin-ctf/              # CTF plugin (1 junior + AI)
├── knowledge-base/          # Shared knowledge (CI auto-sync from all Cells)
└── docs/                    # Central documentation
```

#### 5.2 Shared State Protocol (Syncthing-backed)

```
shared/
├── cases/
│   └── <case-id>/
│       ├── status.yaml                 # Global case status (schema_version: 1)
│       ├── dag_state.yaml              # DAG checkpoint (schema_version: 1)
│       ├── tasks/                      # Task assignments (DAG state)
│       ├── findings/                   # Per-member findings files (member-A.yaml, member-B.yaml)
│       └── answers.yaml                # Answer aggregation (Supervisor-maintained, schema_version: 1)
├── evidence_index.yaml                 # Degraded-mode evidence index (schema_version: 1)
├── agents/                             # Agent heartbeat files
│   └── <agent-id>/
│       └── heartbeat.yaml              # Liveness (schema_version: 1)
└── reconciliation_conflicts.yaml       # Timestamp-tie conflicts from PostgreSQL reconciliation
```

**Rules**:
1. Each member writes findings to their own per-member file (`findings/<member-id>.yaml`) — eliminates write conflicts
2. Each finding has member-scoped unique ID (`<member-id>-F-001`, `<member-id>-F-002`...), `confidence` field, `evidence_ref`
3. Supervisor reads all findings, extracts answers, maintains `answers.yaml`
4. Syncthing handles all transport — AI never calls HTTP for collaboration
5. All shared YAML artifacts carry a mandatory `schema_version` field. Readers accept version N and N-1; writers always produce the latest. Migration functions in `collab/shared.py` upgrade older formats on read.
6. `forhacker collab status` scans for `*.sync-conflict*` files and alerts if any are found. Per-member findings files eliminate the primary conflict source.
7. **Conflict resolution procedure**: When `forhacker collab status` detects `*.sync-conflict*` files: (1) Both versions are preserved in-place — no automatic deletion. (2) The CLI lists each conflict file with both timestamps and member-IDs (parsed from filename). (3) Operator runs `forhacker collab resolve <path> --keep <member-id>` to select the winning version; the losing version is renamed to `<file>.resolved-by-<operator>`. If the conflict is in a per-member findings file (`findings/<member-id>.yaml`), the owning member's version automatically wins — the other version is discarded with a log entry. Conflicts in `dag_state.yaml` or `answers.yaml` require Supervisor (or human lead) resolution.

#### 5.3 CI Quality Gates (per Cell repo)

```yaml
# .github/workflows/quality.yml (identical across all repos)
checks:
  - ruff format --check
  - mypy src/
  - pytest --cov --cov-fail-under=70
  - ai-code-review (superpowers skill)
```

PR cannot merge unless all checks pass. The AI Code Review step uses the `superpowers-deepseek-v4:requesting-code-review` skill. Note: CI enforces code quality (format, types, tests, AI review). Enforcement of the brainstorming→plan→TDD workflow is handled by team process and Cell owner review, not by automated CI gates.

### 6. CLI and Web Dashboard

#### 6.1 CLI

```bash
# Case management
forhacker case create "2026龙岩杯" --type competition
forhacker case status

# Task execution
forhacker task run "analyze memory image" --evidence path/to/memory.dmp

# Plugin management
forhacker plugin create forensics-disk
forhacker plugin install forensics-disk
forhacker plugin list

# MetaAgent
forhacker meta scan              # Manual trigger
forhacker meta proposals         # List pending proposals
forhacker meta approve <id>      # Approve a proposal
forhacker meta rollback <id>     # Rollback an approved change

# Knowledge base
forhacker kb search "内存取证 可疑进程"
forhacker kb ingest --url "https://example.com/writeup"

# Collaboration
forhacker collab status          # Check Syncthing health
forhacker collab sync            # Manual sync trigger
```

#### 6.2 Web Dashboard

Local-only FastAPI server. Three views:
1. **Case Overview** — task DAG visualization, progress bars, confidence distribution
2. **Timeline** — chronological view of findings across all agents
3. **Evidence Map** — relationship graph between artifacts

No authentication — localhost only. Team members access their own dashboard.

**Empty states**: Case Overview with no active case shows: "No active case. Run `forhacker case create <name>` to start." Timeline with zero findings shows: "No findings yet. Findings will appear here as agents complete tasks." Evidence Map with no evidence shows: "No evidence indexed. Run `forhacker evidence verify <case-id>` to index evidence files."

### 7. Knowledge Base Flow

```
Cell repos (each has knowledge/ directory)
  ↓  CI auto-sync (daily + on push to main)
  ↓  Script: extract YAML frontmatter, validate schema, dedup, merge
  ↓
knowledge-base repo (central, tag-indexed)
  ↓  Search API (local file scan, no server needed)
  ↓
Any Cell queries: forhacker kb search "..."
```

**Dedup strategy**: Two entries are duplicates if they share the same `source` field OR their body text has >95% similarity (via minhash/LSH). When a duplicate is detected, the entry with higher `confidence` and later `date` is kept; the discarded entry's source is logged. Ambiguous cases keep both with a `see_also` cross-reference. Dedup decisions are surfaced in CI job output.

**Operational findings pipeline**: A scheduled job queries the PostgreSQL `findings` table for completed cases, transforms findings into the Markdown + YAML frontmatter format, writes them to the knowledge-base repo's ingestion queue, and the existing dedup/validate script processes them. This closes the loop from Principle 5 ("Every finding feeds into a shared knowledge base"). Manual ingestion via `forhacker kb ingest` remains available for URLs and external sources.

**Re-ingestion on case update**: Each finding carries a `last_ingested_at` timestamp. When a case is re-opened and new findings are added, the ingestion job queries `findings WHERE last_ingested_at IS NULL OR updated_at > last_ingested_at` — only new or updated findings are pushed to the KB queue. If a finding's confidence is upgraded (e.g., `unknown → verified` after human review), `updated_at` changes and the finding is re-ingested; the KB dedup step replaces the old entry (same finding ID, later timestamp wins).

Knowledge entries are Markdown with YAML frontmatter (inherited from old project format):
```markdown
---
tags: [memory_forensics, volatility, windows]
tools: [vol3, strings]
difficulty: medium
confidence: verified
source: competition_2026_fic_q15
---
# Windows Memory Analysis — Suspicious Process
...
```

## What Does NOT Change (Preserved Invariants)

The following assets from the old project and team environment are preserved unchanged by this design:

- **Three-state confidence model** (✅ Verified, ⚠️ Inferred, ❌ Unknown) — inherited from old project, formalized as Design Principle 3
- **Markdown + YAML frontmatter knowledge format** — existing knowledge entries remain valid; the new KB pipeline reads the same schema
- **`cases/<case-id>/evidence/` directory convention** — existing evidence layout preserved
- **Team Cell structure** (5 Cells, 10 members, weekly 2×2h sync) — the design enables Cells, it does not reorganize them
- **`E:\项目\自动化取证\` historical data** — archived as reference, not migrated; the new system starts fresh
- **Syncthing as transport layer** — already validated by the team; the design formalizes the file protocol on top of it
- **Claude Code + Superpowers workflow** — the brainstorming/plan/review process used to create this spec is itself a preserved team practice

## Decision Traceability

Mapping of Phase A decisions to design sections:

| Q# | Decision | Design Section | Status |
|----|----------|---------------|--------|
| Q1 | Comprehensive platform scope | Goals, Non-Goals | Addressed |
| Q2 | Core + Plugin architecture | §1 Core Framework, §1.4 Plugin System | Addressed |
| Q3 | Supervisor multi-agent pattern | §1.3 Task Engine, Supervisor logic | Addressed |
| Q4 | Python + Rust (PyO3) | Design Principles, File Inventory | Addressed |
| Q5 | Python ABC + MCP Server dual-mode | §1.4 Plugin System | Addressed |
| Q6 | LLM abstraction + offline switch | §1.1 LLMBackend | Addressed |
| Q7 | MessageBus abstraction | §1.2 MessageBus | Addressed |
| Q8 | DAG + dynamic expansion | §1.3 Task Engine | Addressed |
| Q9/Q21 | PostgreSQL + local filesystem | §3 Data Layer | Addressed |
| Q10 | Docker + WSL2 Firecracker | §4 Security Isolation | Addressed |
| Q11 | CLI-first + Web dashboard | §6 CLI and Web Dashboard | Addressed |
| Q12 | Case spaces + role permissions | §5 Team Collaboration | Addressed |
| Q13 | Scaffolding CLI + marketplace | §1.4 Plugin System | Addressed |
| Q14 | Core monorepo + plugin repos | §5.1 Repository Organization | Addressed |
| Q15 | Dual-track first iteration | Implementation Phases | Addressed |
| Q16/Q16.1 | MetaAgent 4 roles + approval | §2 MetaAgent | Addressed |
| Q17 | CI gates + AI Code Review | §5.3 CI Quality Gates | Addressed |
| Q18 | Mobile async interaction | Out of Scope (separate project) | Deferred |
| Q19 | Shared knowledge-base + CI | §7 Knowledge Base Flow | Addressed |
| Q20/Q20.1 | Supervisor dispatch + Syncthing | §1.3 Supervisor, §5.2 Shared State | Addressed |

## Scope Summary

| Module | Files | Est. LOC | Status |
|--------|-------|----------|--------|
| `forhacker/llm/` | 6 | ~800 | New |
| `forhacker/bus/` | 2 | ~200 | New |
| `forhacker/task/` | 5 | ~1400 | New |
| `forhacker/plugin/` | 4 | ~800 | New |
| `forhacker/meta/` | 6 | ~1100 | New |
| `forhacker/data/` | 3 | ~600 | New |
| `forhacker/security/` | 4 | ~500 | New |
| `forhacker/collab/` | 2 | ~300 | New |
| `forhacker/cli/` | ~10 | ~1000 | New |
| `tests/` | ~20 | ~1500 | New |
| `docs/` | ~10 | — | New |
| **Total** | **~73 files** | **~8,200 LOC** | All new (greenfield) |

## Future Considerations

- **Distributed MessageBus (Redis/NATS)**: Deferred until a concrete cross-machine message-passing scenario emerges beyond Syncthing file-based collaboration
- **Firecracker microVM hardening**: KVM dependency limits deployment; revisit when team hardware standardizes on KVM-capable machines
- **Offline competition LAN collaboration plugin**: Reserved plugin slot; implement when team qualifies for offline finals
- **Mobile agent interaction client**: Separate project at `E:\ProjectHJM\手机操控agent`
- **Repository pattern extraction**: If >2 modules need the same data-access interface, extract shared repository ABCs from `data/models.py`

## Design Iteration Notes

This spec passed two rounds of multi-reviewer review (6 reviewers + arbiter per round).

**Round 1** (31 actionable findings — 10 BLOCKING, 21 IMPORTANT):
1. **SubAgent execution contract** — Added `SubAgentContext`, `SubAgentResult`, `SubAgentLifecycle` to §1.3
2. **CapabilityRegistry** — Added named interface (was a ghost reference)
3. **Security isolation** — Changed silent Docker fallback to explicit BLOCK for HIGH-risk tasks
4. **Finding ID scheme** — Changed to member-scoped (`<member-id>-F-001`) with per-member files
5. **Shared state protocol** — Added `schema_version`, `dag_state.yaml`, Supervisor recovery, cascade failure, conflict detection

**Round 2** (20 actionable findings — 8 BLOCKING, 12 IMPORTANT, +13 NITs; STOP_DEGENERATE after degradation check):
6. **LLMBackend type system** — Redesigned `complete()` signature to messages-based API with `Message` and `LLMResponse` types
7. **Two-path data model** — Documented hot path (shared/ YAML via `collab/shared.py`) vs cold path (PostgreSQL via `data/models.py`)
8. **Degraded mode completeness** — Replicated `evidence_index` and agent heartbeats to `shared/` for PostgreSQL-offline operation
9. **CapabilityRegistry ownership** — Moved from `plugin/capability.py` to `task/capability.py`; inverted dependency direction
10. **Confidence taxonomy** — Split into `task_confidence` (HIGH|MEDIUM|LOW) and `evidence_confidence` (verified|inferred|unknown)
11. **Cycle detection** — Added to both `add_task()` (per-call) and plugin dependency resolution (topological sort)
12. **DAG write-through** — `add_task()` atomically persists via temp-file + rename; `AddTaskResult` with explicit status enum
13. **PlatformIntrospection** — Added read-only interface for Platform Optimizer role
14. **MetaAgent safeguards** — File lock documented as best-effort with post-hoc proposal dedup; evaluator watchdog split into M=0 and M>0 conditions
15. **Syncthing conflict resolution** — 3-step procedure with per-member auto-resolution
16. **Reconciliation timestamps** — Per-record `updated_at` comparison; tie conflicts logged to `reconciliation_conflicts.yaml`
17. **KB re-ingestion** — `last_ingested_at` field; incremental query on case update
18. **Evidence integrity** — Added `integrity=missing` for unverified files; orphan detection and purge
19. **Scaffolding cleanup** — Removed `src/agents/` from plugin template
20. **Risk R2 expansion** — Multi-paragraph narrative covering model variance, domain knowledge gap, and prompt sensitivity

## Implementation Phases

### Phase 1: Core Skeleton (Weeks 1-3, ~2,000 LOC)
- `LLMBackend` ABC + OpenAI + Ollama implementations
- `MessageBus` ABC + InProcessBus
- `BasePlugin` ABC + PluginManager (discovery only)
- Minimal CLI (`forhacker case create`, `forhacker task run`)
- PostgreSQL schema + migration
- One end-to-end test: "analyze a memory dump" using Volatility 3 via CLI

### Phase 2: Supervisor + First Plugin (Weeks 4-6, ~2,500 LOC)
- `TaskEngine` with DAG + dynamic addition
- `Supervisor` agent logic (decompose → dispatch → aggregate)
- `forensics-memory` plugin (first real plugin, by competition Cell)
- `SubAgent` dispatch (each task = fresh agent instance)
- Shared state protocol (YAML read/write)

### Phase 3: Collaboration + Quality (Weeks 7-9, ~1,200 LOC)
- Syncthing integration + health checks
- CI pipeline template for all Cell repos
- AI Code Review automation
- `knowledge-base` CI auto-ingestion

### Phase 4: MetaAgent + Dashboard (Weeks 10-12, ~1,500 LOC)
- MetaAgent core (scheduler + evaluator + browser engine)
- Source registry with initial sources
- Proposal → Issue workflow
- Web Dashboard (FastAPI + Jinja2, local only)
- Audit trail and rollback

### Phase 5: Marketplace + Polish (Weeks 13+, ~1,000 LOC)
- Plugin marketplace registry
- `forhacker plugin create` scaffolding CLI
- `forhacker plugin install` from marketplace
- TUTORIAL.md template generation
- Sandbox isolation (Docker + Firecracker)

## Testing Strategy

### Unit Tests (per module)
| # | Test | Pass Criteria |
|---|------|---------------|
| T1 | LLM backend routing logic | Correct backend selected for each sensitivity level + OFFLINE flag |
| T2 | DAG operations (add node, detect cycle, topological sort, cascade fail) | Cycles detected, topological order correct, cascade marks all downstream |
| T3 | Plugin discovery, loading, and failure isolation | Failed plugin skipped; healthy plugins load; degraded_plugins list populated |
| T4 | MetaAgent evaluator scoring | Relevance threshold correctly filters proposals; watchdog fires after 7 zero days |
| T5 | CapabilityRegistry query | Correct tools returned for domain+tags; unknown domain returns empty list |
| T6 | Finding ID generation (member-scoped) | No collisions across 1000 concurrent IDs from 10 members |

### Integration Tests
| # | Test | Pass Criteria |
|---|------|---------------|
| T7 | End-to-end: CLI → Supervisor → SubAgent → finding in shared/ [Manual] | Full pipeline completes; finding written to member's YAML with correct schema_version |
| T8 | Plugin lifecycle: create → load → register tools → call via MCP [Manual] | Tool callable via MCP endpoint; result returned correctly |
| T9 | Knowledge base: write entry → CI ingest → search returns match [Manual] | Entry appears in search results within 1 CI cycle |
| T10 | MetaAgent: scan mock source → proposal → approve → execute → rollback [Manual] | Proposal flows through all gates; rollback restores exact prior state |
| T11 | Supervisor crash recovery [Manual] | Kill Supervisor mid-task; restart reads dag_state.yaml; orphaned tasks reassigned |
| T12 | PostgreSQL fallback | Kill PostgreSQL; system continues with shared/ YAML; reconciliation sync on reconnect |
| T13 | Evidence hash verification | Tampered file blocked; integrity flag set; CRITICAL alert raised |

### Competition Simulation
| # | Test | Pass Criteria |
|---|------|---------------|
| T14 | Past CTF forensics question set, full pipeline [Manual] | Time to first correct answer measured; confidence accuracy tracked; KB hit rate logged. **Fail modes:** (a) pipeline stalls — any task stuck in `running` >5min triggers timeout alert; (b) incorrect answer — finding marked `evidence_confidence=inferred` but answer wrong, triggers re-decomposition with adjusted prompt; (c) KB miss — relevant KB entry exists but not surfaced, logged as search-recall gap for index tuning; (d) model degradation — same question produces correct answer on cloud model but wrong on local model, logged with model version for regression tracking. |

### CI Requirements
- All tests must pass before merge
- Coverage ≥ 70% for core modules
- AI Code Review must pass (no blocking findings)

## File Inventory

```
forhacker-core/
├── forhacker/
│   ├── llm/                        # 6 files (backend.py, openai.py, anthropic.py, deepseek.py, ollama.py, router.py)
│   ├── bus/                        # 2 files (message_bus.py, in_process.py)
│   ├── task/                       # 5 files (engine.py, supervisor.py, sub_agent.py, dag.py, capability.py)
│   ├── plugin/                     # 4 files (base.py, manager.py, mcp_server.py, marketplace.py)
│   ├── meta/                       # 6 files (agent.py, sources.py, evaluator.py, introspection.py, browser.py, audit.py)
│   ├── data/                       # 3 files (db.py, models.py, evidence.py)
│   ├── security/                   # 4 files (sandbox.py, docker.py, firecracker.py, router.py)
│   ├── collab/                     # 2 files (shared.py, syncthing.py)
│   └── cli/                        # ~10 files
├── tests/                          # mirrored structure
├── docs/
│   ├── superpowers/
│   │   ├── specs/                  # This spec and future specs
│   │   └── brainstorms/            # Decision logs
│   └── tutorials/                  # Per-component tutorials
├── shared/                         # Runtime collaboration directory
├── VISION.md
├── README.md
├── pyproject.toml
└── .github/workflows/quality.yml
```

## Risks

### Risk Assessment

| # | Risk | Severity | Status | Mitigation | Residual Risk |
|---|------|----------|--------|------------|---------------|
| R1 | LLM abstraction over-engineering | MEDIUM | MONITORED | Phase 1 implements only OpenAI + Ollama; others added when needed | Interface may drift from real usage patterns before stabilization |
| R2 | Supervisor quality depends on underlying model | HIGH | MONITORED | DAG structure allows human review before dispatch; Supervisor outputs proposed DAG, human can modify; sensitivity-based routing sends decomposition prompts to strongest available model | **Detailed assessment:** The Supervisor is the single point of intelligence in the task flow — if it produces poor decomposition, every downstream sub-agent inherits the error. This risk has three dimensions: **(a) Model capability variance** — DeepSeek-V4-Pro (primary, strongest) vs Ollama local models (offline, significantly weaker). In offline/competition scenarios where only a local 7B–14B model is available, decomposition quality may degrade sharply. **(b) Domain knowledge gap** — the Supervisor must understand forensics task semantics (e.g., distinguishing volatility2 vs volatility3 plugins, knowing which artifacts to prioritize). Without domain-specific fine-tuning, it may produce syntactically valid but semantically wrong DAGs. **(c) Prompt sensitivity** — small changes to the Supervisor system prompt can produce large changes in output structure; versioning the prompt is easy but measuring its quality regression requires human evaluation on real cases. **Mitigation layers:** (i) DAG is human-reviewable and editable before dispatch; (ii) sensitivity-based routing sends decomposition prompts to the strongest model; (iii) Phase 1 includes a benchmark suite of 10 known forensics decomposition tasks with expected DAG shapes; (iv) the CapabilityRegistry constrains valid tool assignments to registered tools, reducing hallucinated steps. **Residual risk:** a weak local model may still produce decomposition that passes structural validation but is forensically unsound — only domain-expert human review can catch this. | Weak local model may produce consistently poor decomposition requiring heavy human correction; prompt regression may go undetected between benchmark runs |
| R3 | MetaAgent noise (low-quality proposals) | MEDIUM | MONITORED | Configurable evaluator threshold; start high, lower as proven; evaluator watchdog with M=0 and M>0 alert conditions | Evaluator miscalibration could produce zero or too many proposals |
| R4 | Team adoption (skipping workflow) | MEDIUM | MONITORED | Scaffolding CLI generates structure automatically; CI gates check code quality | Process steps (brainstorming, planning) require Cell owner discipline, not CI-enforcement |
| R5 | Syncthing reliability behind GFW | LOW | MONITORED | Relay protocol works over HTTPS; public server in China as relay node; LAN mode for offline | WAN relay latency may slow sync for remote team members |
| R6 | Windows + WSL2 dependency (Firecracker) | LOW | VALIDATED | Isolation router blocks HIGH-risk tasks when KVM unavailable (not silent downgrade); Docker suffices for LOW/MEDIUM | Some team laptops may be unable to run HIGH-risk malware analysis locally |

### Cross-Component Integration Status

| Subsystem Pair | Integration Point | Status | Validated |
|---------------|-------------------|--------|-----------|
| Supervisor ↔ Plugin | CapabilityRegistry.query() | Defined | Not yet implemented |
| DAG Engine ↔ Shared State | dag_state.yaml read/write | Defined | Not yet implemented |
| SubAgent ↔ Supervisor | SubAgentContext / SubAgentResult | Defined | Not yet implemented |
| MetaAgent ↔ Core | Audit trail + rollback | Defined | Not yet implemented |
| Cell Repos ↔ Knowledge Base | CI auto-sync pipeline | Defined | Not yet implemented |
| Syncthing ↔ Shared State | Per-member YAML files | Defined | Spot-tested (LAN <1s sync) |

## Out of Scope

- Court-admissible forensic imaging and chain-of-custody logging
- Mobile device acquisition (UFED, Cellebrite style)
- Real-time monitoring / IDS integration
- Multi-tenancy with organization-level access control
- Plugin billing or commercial marketplace
- Local model training pipeline (use existing tools like llama.cpp)
- Offline competition LAN collaboration plugin (reserved, not implemented)
- Mobile agent interaction client (separate project)
