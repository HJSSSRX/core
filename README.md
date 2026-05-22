# ForHacker

AI-Native Digital Forensics Platform — Supervisor Agent + multi-agent dispatch + self-improvement.

**59 commits | 8 Cell plugins | 37 forensic tools | 282 tests | 86% coverage**

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

# List all forensic tools
forhacker plugin list

# View dashboard
forhacker web serve  # then open http://localhost:8000
```

## Cell Plugins (8 plugins, 37 tools)

| Plugin | Tools | Description |
|--------|-------|-------------|
| `forensics-core` | 5 | file_hash, extract_strings, pe_info, yara_scan, volatility3_pslist |
| `file-analyzer` | 3 | file_metadata, entropy_scan, hex_dump |
| `log-parser` | 4 | parse_csv, parse_jsonl, parse_iis_log, parse_evtx |
| `network-forensics` | 5 | pcap_summary, dns_lookup, http_header_parse, ip_geo_lookup, connection_graph |
| `registry-analyzer` | 5 | parse_reg, detect_startup_entries, detect_usb_history, detect_recent_files, detect_installed_software |
| `browser-forensics` | 5 | chrome_history, firefox_history, chrome_cookies, browser_downloads, extract_bookmarks |
| `email-forensics` | 5 | parse_eml, extract_email_headers, analyze_attachments, detect_phishing_indicators, parse_mbox |
| `timeline-analyzer` | 5 | build_timeline, detect_timeline_gaps, correlate_events, deduplicate_events, export_timeline_csv |

All plugins use Python stdlib for core functionality — zero external dependencies unless noted.

## CLI Commands

```
forhacker case create <name>        Create a new case
forhacker case run <case> <goal>    Run a forensics pipeline
forhacker case status               Show case status

forhacker plugin list               List installed plugins and tools
forhacker plugin create <name>      Scaffold a new Cell plugin
forhacker plugin marketplace        Browse installable plugins
forhacker plugin install <name>     Install from marketplace

forhacker meta scan                 Trigger MetaAgent source scan
forhacker meta proposals            List pending proposals
forhacker meta review <N>           Review a proposal (--approve/--reject)
forhacker meta verify               Verify proposal integrity
forhacker meta watchdog             Check evaluator alert status
forhacker meta snapshots            List backup snapshots
forhacker meta rollback <id>        Rollback an approved change

forhacker evidence verify <case>    Verify evidence file integrity
forhacker evidence purge-orphans    Clean up orphaned hash files

forhacker kb search <query>         Search knowledge base
forhacker kb add <title>            Add a KB entry
forhacker kb list                   List all KB entries

forhacker collab status             Check shared state + agent heartbeats
forhacker collab conflicts          List Syncthing conflict files
forhacker collab resolve <path>     Resolve a conflict file
forhacker collab sync               Trigger Syncthing folder rescan

forhacker web serve                 Start FastAPI dashboard (port 8000)
```

## Architecture

```
forhacker/
├── llm/            # LLMBackend ABC + OpenAI, Anthropic, DeepSeek, Ollama, Router, Resilience
├── bus/            # MessageBus ABC + InProcessBus
├── task/           # DAG, Supervisor, SubAgent, Pipeline, CapabilityRegistry
├── plugin/         # BasePlugin ABC, PluginManager, MCP Server, Marketplace
├── meta/           # MetaAgent, Scheduler, Browser, Evaluator, Introspection, Audit
├── kb/             # Knowledge base: Markdown+YAML storage, tag/keyword search
├── data/           # PostgreSQL models, evidence indexing
├── security/       # Sandbox ABC, Docker isolation, Firecracker stub, risk-based router
├── collab/         # Syncthing shared state, health check, conflict resolution
└── cli/            # Click CLI (case/plugin/meta/evidence/kb/collab) + FastAPI Dashboard

cells/
├── forensics_core/    # File hashing, PE parsing, YARA, Volatility stubs
├── file_analyzer/     # File metadata, entropy analysis, hex dump
├── log_parser/        # CSV, JSONL, IIS W3C, Windows EVTX parsing
├── network_forensics/ # PCAP summary, DNS lookup, HTTP headers, netstat
├── registry_analyzer/ # .reg parser, startup entries, USB history, software inventory
├── browser_forensics/ # Chrome/Firefox history, cookies, downloads, bookmarks
├── email_forensics/   # EML parsing, header analysis, phishing detection, mbox
└── timeline_analyzer/ # Event correlation, gap detection, dedup, CSV export
```

## Development

```bash
pip install -e ".[dev]"

# Quality checks (same as CI)
ruff format --check .
ruff check .
mypy forhacker/ --ignore-missing-imports
pytest tests/ --cov=. --cov-fail-under=70
```

## CI Pipeline

GitHub Actions with matrix strategy:
1. **format** — ruff format check
2. **lint** — ruff check
3. **typecheck** — mypy with `--ignore-missing-imports`
4. **test** — pytest with `--cov-fail-under=70`

## Team

Hunan Police Academy, ~10 members. Cell-based collaboration model with Syncthing shared state.
