"""Log Parser Cell — parse CSV, JSON-lines, IIS, and Windows Event logs."""

import csv
import json
from io import StringIO
from pathlib import Path
from typing import Any

from forhacker.plugin.base import BasePlugin, Tool


class LogParserPlugin(BasePlugin):
    name = "log-parser"
    version = "0.1.0"
    domain = "forensics"
    risk_levels = {
        "parse_csv": "LOW",
        "parse_jsonl": "LOW",
        "parse_iis_log": "LOW",
        "parse_evtx": "MEDIUM",
    }

    def register_tools(self) -> list[Tool]:
        return [
            Tool(
                name="parse_csv",
                description="Parse CSV/TSV log files with header detection",
                domain="forensics",
                risk_level="LOW",
                applicable_extensions=(".csv", ".tsv", ".txt", ".log"),
            ),
            Tool(
                name="parse_jsonl",
                description="Parse JSON-lines (NDJSON) log files",
                domain="forensics",
                risk_level="LOW",
                applicable_extensions=(".jsonl", ".json", ".ndjson"),
            ),
            Tool(
                name="parse_iis_log",
                description="Parse Microsoft IIS W3C log format",
                domain="forensics",
                risk_level="LOW",
                applicable_extensions=(".log", ".txt"),
            ),
            Tool(
                name="parse_evtx",
                description="Parse Windows Event Log (.evtx) files",
                domain="forensics",
                risk_level="MEDIUM",
                applicable_extensions=(".evtx",),
            ),
        ]


def run_parse_csv(target: str, delimiter: str = "", max_rows: int = 200) -> dict[str, Any]:
    """Parse CSV/TSV log files. Auto-detects delimiter if not specified."""
    path = Path(target)
    if not path.exists():
        return {"error": f"File not found: {target}"}

    text = path.read_text(encoding="utf-8", errors="replace")
    if not delimiter:
        delimiter = "\t" if "\t" in text[:200] else ","

    reader = csv.DictReader(StringIO(text), delimiter=delimiter)
    if not reader.fieldnames:
        return {"error": "No headers detected", "file": str(path.absolute())}

    rows = []
    for row in reader:
        rows.append(dict(row))
        if len(rows) >= max_rows:
            break

    return {
        "file": str(path.absolute()),
        "headers": list(reader.fieldnames),
        "row_count": len(rows),
        "delimiter": "tab" if delimiter == "\t" else delimiter,
        "rows": rows,
    }


def run_parse_jsonl(target: str, max_rows: int = 200) -> dict[str, Any]:
    """Parse JSON-lines (NDJSON) format — one JSON object per line."""
    path = Path(target)
    if not path.exists():
        return {"error": f"File not found: {target}"}

    rows = []
    errors = 0
    with path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                errors += 1
            if len(rows) >= max_rows:
                break

    return {
        "file": str(path.absolute()),
        "row_count": len(rows),
        "parse_errors": errors,
        "keys": list(rows[0].keys()) if rows else [],
        "rows": rows,
    }


def run_parse_iis_log(target: str, max_rows: int = 200) -> dict[str, Any]:
    """Parse Microsoft IIS W3C extended log format.

    IIS logs have #Fields: line defining column order, then space-delimited data rows.
    """
    path = Path(target)
    if not path.exists():
        return {"error": f"File not found: {target}"}

    text = path.read_text(encoding="utf-8", errors="replace")
    fields: list[str] = []
    rows = []

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("#Fields:"):
            fields = line.replace("#Fields:", "").strip().split()
        elif line.startswith("#"):
            continue
        elif fields:
            values = line.split()
            row = dict(zip(fields, values))
            rows.append(row)
            if len(rows) >= max_rows:
                break

    return {
        "file": str(path.absolute()),
        "fields": fields,
        "row_count": len(rows),
        "rows": rows,
    }


def run_parse_evtx(target: str, max_rows: int = 200) -> dict[str, Any]:
    """Parse Windows Event Log (.evtx) files. Requires `pip install python-evtx`."""
    try:
        from Evtx.Evtx import Evtx  # type: ignore[import-untyped]
    except ImportError:
        return {"error": "python-evtx not installed. Run: pip install python-evtx"}

    events = []
    try:
        with Evtx(target) as evtx:
            for record in evtx.records():
                try:
                    events.append(
                        {"event_id": record.event_id(), "timestamp": str(record.timestamp()), "xml": record.xml()}
                    )
                except Exception:
                    events.append({"error": "failed to parse record"})
                if len(events) >= max_rows:
                    break
    except Exception as e:
        return {"error": f"Failed to parse EVTX file: {e}"}

    return {
        "file": str(Path(target).absolute()),
        "event_count": len(events),
        "events": events,
    }
