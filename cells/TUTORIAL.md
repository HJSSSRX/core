# Cell Plugin Tutorial

## Overview

A **Cell** is an independent plugin that provides forensic analysis tools to ForHacker. Each Cell is a directory under `cells/` with a `plugin.py` file that implements `BasePlugin`.

## 5-Minute Quick Start

### 1. Create the directory

```bash
mkdir -p cells/my_analyzer
```

### 2. Write plugin.py

```python
"""My Analyzer Cell — describe what it does."""

from forhacker.plugin.base import BasePlugin, Tool


class MyAnalyzerPlugin(BasePlugin):
    name = "my-analyzer"
    version = "0.1.0"
    domain = "forensics"       # forensics | network | mobile | malware
    risk_levels = {
        "my_tool": "LOW",      # LOW | MEDIUM | HIGH
    }

    def register_tools(self) -> list[Tool]:
        return [
            Tool(
                name="my_tool",
                description="What this tool does",
                domain="forensics",
                risk_level="LOW",
            ),
        ]


# Tool implementation — a plain function
def run_my_tool(target: str) -> dict:
    from pathlib import Path
    path = Path(target)
    if not path.exists():
        return {"error": f"File not found: {target}"}
    # Your forensic logic here
    return {"file": str(path), "result": "analysis output"}
```

### 3. Test it

```bash
forhacker case plugins
```

Your plugin appears automatically. Run it in a case:

```bash
forhacker case run test-case "analyze my target"
```

## Tool Contract

Every tool function:
- Accepts a `target: str` as first argument
- Returns a `dict` with at minimum `{"error": "message"}` on failure
- Returns structured data on success — keys should be snake_case

## Risk Levels

| Level | Meaning | Sandbox |
|-------|---------|---------|
| LOW | Read-only, safe operations | No isolation needed |
| MEDIUM | Reads untrusted files | Docker container |
| HIGH | Executes untrusted code | Firecracker VM (Linux only) |

## Domain Names

Use existing domains or propose new ones:
- `forensics` — File/memory/disk analysis
- `network` — Packet capture, DNS, connections
- `mobile` — Android/iOS artifacts
- `malware` — Reverse engineering, sandboxing

## Testing Your Plugin

```python
# tests/test_plugin/test_my_analyzer.py
from cells.my_analyzer.plugin import MyAnalyzerPlugin, run_my_tool

def test_plugin_registers_tools():
    plugin = MyAnalyzerPlugin()
    tools = plugin.register_tools()
    assert len(tools) >= 1

def test_my_tool_works(tmp_path):
    f = tmp_path / "test.bin"
    f.write_bytes(b"test data")
    result = run_my_tool(str(f))
    assert "error" not in result
```

## Publishing

1. Push your Cell to its own git repo
2. Add repo URL to `forhacker/plugin/marketplace.py`
3. Other team members: `git clone <cell-repo> cells/<name>`
