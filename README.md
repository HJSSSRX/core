# ForHacker

AI-Native Digital Forensics Platform — Supervisor Agent + multi-agent dispatch + self-improvement.

## Quick Start

```bash
# Clone and install
git clone https://github.com/forhacker/core
cd core
pip install -e ".[dev]"

# Create a case
forhacker case create "my-first-case"

# Scaffold a Cell plugin
forhacker plugin create memory-analysis

# Run a forensic investigation
forhacker case run "my-first-case" "analyze memory dump for malware"

# Check team status
forhacker collab status

# View dashboard
forhacker web serve  # then open http://localhost:8000
```

## CLI Commands

```
forhacker case create <name>        Create a new case
forhacker case run <case> <goal>    Run a forensics pipeline
forhacker case status               Show case status
forhacker case plugins              List autoloaded Cell plugins

forhacker plugin list               List installed plugins and tools
forhacker plugin create <name>      Scaffold a new Cell plugin
forhacker plugin marketplace        Browse installable plugins
forhacker plugin install <name>     Install from marketplace

forhacker meta scan                 Trigger MetaAgent source scan
forhacker meta proposals            List pending proposals
forhacker meta review <N>           Review a proposal
forhacker meta verify               Verify proposal integrity
forhacker meta watchdog             Check evaluator alert status

forhacker kb search <query>         Search knowledge base
forhacker kb add <title>            Add a KB entry
forhacker kb list                   List all KB entries

forhacker collab status             Check shared state + agent heartbeats
forhacker collab conflicts          List Syncthing conflict files
forhacker collab resolve <path>     Resolve a conflict file
forhacker collab syncthing          Check Syncthing health

forhacker evidence verify <case>    Verify evidence file integrity
forhacker evidence purge-orphans    Clean up orphaned hash files
```

## Architecture

```
forhacker/
├── llm/            # LLMBackend ABC + OpenAI, Anthropic, DeepSeek, Ollama, sensitivity router
├── bus/            # MessageBus ABC + InProcessBus
├── task/           # DAG engine, Supervisor, SubAgent dispatch, Pipeline orchestrator, CapabilityRegistry
├── plugin/         # BasePlugin ABC, PluginManager, MCP Server, Marketplace
├── meta/           # MetaAgent (4 roles), scheduler, browser, evaluator, introspection, audit
├── kb/             # Knowledge base: Markdown+YAML storage, tag/keyword search
├── data/           # PostgreSQL models, evidence indexing, async engine
├── security/       # Sandbox ABC, Docker isolation, Firecracker stub, risk-based router
├── collab/         # Syncthing shared state protocol, health check, conflict resolution
└── cli/            # Click CLI + FastAPI Web Dashboard (Cases, Timeline, Evidence, KB)
```

## Development

```bash
uv pip install -e ".[dev]"

# Quality checks (same as CI)
ruff format --check forhacker/ tests/
ruff check forhacker/ tests/
mypy forhacker/ --ignore-missing-imports
pytest tests/ --cov=forhacker --cov-fail-under=70
```

## Team

Hunan Police Academy, ~10 members. Cell-based collaboration model.
