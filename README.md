# ForHacker

AI-Native Digital Forensics Platform.

## Quick Start

```bash
pip install forhacker
forhacker case create "my-first-case"
```

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

```bash
git clone https://github.com/forhacker/core
cd core
uv pip install -e ".[dev]"
pytest
```

## Team

Hunan Police Academy, ~10 members. Cell-based collaboration model.
