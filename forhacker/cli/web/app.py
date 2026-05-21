from pathlib import Path

import yaml
from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

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
            results.append(item)
    return results


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request, "cases": _list_cases()})


@app.get("/case/{case_id}", response_class=HTMLResponse)
async def case_overview(request: Request, case_id: str):
    dag = _read_dag(case_id)
    tasks = dag.get("tasks", [])
    findings = _read_findings(case_id)
    return templates.TemplateResponse(request, "case_detail.html", {
        "request": request,
        "case_id": case_id,
        "tasks": tasks,
        "tasks_done": sum(1 for t in tasks if t.get("status") == "done"),
        "tasks_running": sum(1 for t in tasks if t.get("status") == "running"),
        "tasks_failed": sum(1 for t in tasks if t.get("status") == "failed"),
        "findings": findings,
        "findings_count": len(findings),
    })


@app.get("/kb", response_class=HTMLResponse)
async def kb_index(request: Request, q: str = Query(default=""), tag: str = Query(default="")):
    store = KBStore(KB_DIR)
    entries = store.search(keyword=q, tags=[tag] if tag else None)
    return templates.TemplateResponse(request, "kb.html", {
        "request": request,
        "entries": entries,
        "query": q,
        "tag_filter": tag,
        "total": len(entries),
    })


@app.get("/kb/{entry_id}", response_class=HTMLResponse)
async def kb_entry(request: Request, entry_id: str):
    store = KBStore(KB_DIR)
    entry = store.get(entry_id)
    if entry is None:
        return HTMLResponse("<h1>Not Found</h1>", status_code=404)
    return templates.TemplateResponse(request, "kb_detail.html", {
        "request": request,
        "entry": entry,
    })
