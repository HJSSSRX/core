from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from forhacker.cli.commands.plugin import _discover_plugins
from forhacker.kb.store import KBStore

app = FastAPI(title="ForHacker Dashboard", docs_url=None, redoc_url=None)
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

SHARED_DIR = Path("shared")
KB_DIR = SHARED_DIR / "kb"


def _list_cases() -> list[str]:
    cases_dir = SHARED_DIR / "cases"
    if not cases_dir.exists():
        return []
    return sorted(d.name for d in cases_dir.iterdir() if d.is_dir())


def _read_dag(case_id: str) -> dict:
    path = SHARED_DIR / "cases" / case_id / "dag_state.yaml"
    if not path.exists():
        return {"tasks": []}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {"tasks": []}


def _read_findings(case_id: str) -> list[dict]:
    findings_dir = SHARED_DIR / "cases" / case_id / "findings"
    if not findings_dir.exists():
        return []
    results = []
    for f in sorted(findings_dir.glob("*.yaml")):
        data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        for item in data.get("findings", []):
            item["task_id"] = f.stem
            item["_mtime"] = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).isoformat()
            results.append(item)
    return results


def _read_all_findings() -> list[dict]:
    """Read findings from all cases, sorted by modification time (newest first)."""
    all_findings = []
    for case_id in _list_cases():
        findings_dir = SHARED_DIR / "cases" / case_id / "findings"
        if not findings_dir.exists():
            continue
        for f in sorted(findings_dir.glob("*.yaml")):
            mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
            data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
            for item in data.get("findings", []):
                item["_case_id"] = case_id
                item["_task_id"] = f.stem
                item["_mtime"] = mtime.isoformat()
                all_findings.append(item)
    all_findings.sort(key=lambda x: x["_mtime"], reverse=True)
    return all_findings


def _list_evidence(case_id: str) -> list[dict]:
    """List evidence files for a case with size and modification time."""
    evidence_dir = SHARED_DIR / "cases" / case_id / "evidence"
    if not evidence_dir.exists():
        return []
    results = []
    for f in sorted(evidence_dir.rglob("*")):
        if f.is_file():
            stat = f.stat()
            results.append(
                {
                    "name": f.name,
                    "path": str(f.relative_to(evidence_dir)),
                    "size": stat.st_size,
                    "mtime": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                }
            )
    return results


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request, "cases": _list_cases()})


@app.get("/case/{case_id}", response_class=HTMLResponse)
async def case_overview(request: Request, case_id: str):
    dag = _read_dag(case_id)
    tasks = dag.get("tasks", [])
    findings = _read_findings(case_id)
    return templates.TemplateResponse(
        request,
        "case_detail.html",
        {
            "request": request,
            "case_id": case_id,
            "tasks": tasks,
            "tasks_done": sum(1 for t in tasks if t.get("status") == "done"),
            "tasks_running": sum(1 for t in tasks if t.get("status") == "running"),
            "tasks_failed": sum(1 for t in tasks if t.get("status") == "failed"),
            "findings": findings,
            "findings_count": len(findings),
        },
    )


@app.get("/kb", response_class=HTMLResponse)
async def kb_index(request: Request, q: str = Query(default=""), tag: str = Query(default="")):
    store = KBStore(KB_DIR)
    entries = store.search(keyword=q, tags=[tag] if tag else None)
    return templates.TemplateResponse(
        request,
        "kb.html",
        {
            "request": request,
            "entries": entries,
            "query": q,
            "tag_filter": tag,
            "total": len(entries),
        },
    )


@app.get("/kb/{entry_id}", response_class=HTMLResponse)
async def kb_entry(request: Request, entry_id: str):
    store = KBStore(KB_DIR)
    entry = store.get(entry_id)
    if entry is None:
        return HTMLResponse("<h1>Not Found</h1>", status_code=404)
    return templates.TemplateResponse(
        request,
        "kb_detail.html",
        {
            "request": request,
            "entry": entry,
        },
    )


@app.get("/timeline", response_class=HTMLResponse)
async def timeline(request: Request):
    """Chronological view of findings across all cases."""
    findings = _read_all_findings()
    cases = _list_cases()
    return templates.TemplateResponse(
        request,
        "timeline.html",
        {
            "request": request,
            "findings": findings,
            "findings_count": len(findings),
            "cases": cases,
        },
    )


@app.get("/evidence/{case_id}", response_class=HTMLResponse)
async def evidence_map(request: Request, case_id: str):
    """Evidence file listing for a case."""
    evidence = _list_evidence(case_id)
    return templates.TemplateResponse(
        request,
        "evidence.html",
        {
            "request": request,
            "case_id": case_id,
            "evidence": evidence,
            "evidence_count": len(evidence),
        },
    )


def _get_plugin_status() -> dict:
    """Collect plugin and system status for the dashboard."""
    try:
        manager = _discover_plugins()
        plugins_data = {}
        total_tools = 0
        for name in manager.loaded_plugins:
            tools = manager.get_plugin_tools(name)
            total_tools += len(tools)
            plugins_data[name] = {
                "tools": [{"name": t.name, "domain": t.domain, "risk": t.risk_level} for t in tools],
                "count": len(tools),
            }
        return {
            "plugin_count": len(manager.loaded_plugins),
            "tool_count": total_tools,
            "degraded": manager.degraded_plugins,
            "plugins": plugins_data,
        }
    except Exception as e:
        return {"error": str(e)}


def _get_system_status() -> dict[str, Any]:
    """Aggregate full system status."""
    status: dict[str, Any] = {"plugins": _get_plugin_status()}

    kb_dir = SHARED_DIR / "kb"
    status["kb_entries"] = len(list(kb_dir.glob("*.md"))) if kb_dir.exists() else 0

    cases_dir = SHARED_DIR / "cases"
    status["cases"] = (
        len([d for d in cases_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]) if cases_dir.exists() else 0
    )

    proposals_dir = SHARED_DIR / "meta" / "proposals"
    status["proposals"] = len(list(proposals_dir.glob("*.yaml"))) if proposals_dir.exists() else 0

    return status


@app.get("/api/status")
async def api_status():
    """JSON API for system status."""
    return _get_system_status()


@app.get("/status", response_class=HTMLResponse)
async def status_page(request: Request):
    """System status dashboard page."""
    status = _get_system_status()
    return templates.TemplateResponse(
        request,
        "status.html",
        {
            "request": request,
            "status": status,
        },
    )
