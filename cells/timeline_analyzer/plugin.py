"""Timeline Analyzer Cell — correlate, deduplicate, and analyze timestamped forensic events.

Pure Python stdlib — zero external dependencies.
"""

import csv
import json
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Any

from forhacker.plugin.base import BasePlugin, Tool


class TimelineAnalyzerPlugin(BasePlugin):
    name = "timeline-analyzer"
    version = "0.1.0"
    domain = "forensics"
    risk_levels = {
        "build_timeline": "LOW",
        "detect_timeline_gaps": "LOW",
        "correlate_events": "LOW",
        "deduplicate_events": "LOW",
        "export_timeline_csv": "LOW",
    }

    def register_tools(self) -> list[Tool]:
        return [
            Tool(name="build_timeline", description="Build a unified chronological timeline from JSON event data",
                 domain="forensics", risk_level="LOW"),
            Tool(name="detect_timeline_gaps", description="Detect time gaps in a timeline that may indicate tampering",
                 domain="forensics", risk_level="LOW"),
            Tool(name="correlate_events", description="Correlate events by time window proximity",
                 domain="forensics", risk_level="LOW"),
            Tool(name="deduplicate_events", description="Deduplicate timeline events by time and content similarity",
                 domain="forensics", risk_level="LOW"),
            Tool(name="export_timeline_csv", description="Export a timeline to CSV format",
                 domain="forensics", risk_level="LOW"),
        ]


def _parse_timestamp(ts: str) -> datetime | None:
    """Try multiple timestamp formats and return UTC datetime."""
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%Y/%m/%d %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
    ]
    ts = ts.strip().replace("+00:00", "Z").replace("+0000", "Z")
    for fmt in formats:
        try:
            dt = datetime.strptime(ts, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def _load_events(target: str) -> tuple[list[dict], dict | None]:
    """Load events from a JSON file or array string. Returns (events, error)."""
    path = Path(target)
    if not path.exists():
        return [], {"error": f"File not found: {target}"}
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError as e:
        return [], {"error": f"Invalid JSON: {e}"}
    if isinstance(data, dict):
        data = data.get("events", [])
    if not isinstance(data, list):
        return [], {"error": "Expected a JSON array or object with 'events' key"}
    return data, None


def run_build_timeline(target: str) -> dict[str, Any]:
    """Build a unified chronological timeline from JSON event data.

    Expected format: [{"timestamp": "2024-01-15T10:30:00Z", "source": "...", "description": "..."}, ...]
    """
    events, error = _load_events(target)
    if error:
        return error

    parsed = []
    unparseable = 0
    for evt in events:
        ts = evt.get("timestamp", "")
        dt = _parse_timestamp(str(ts))
        if dt:
            parsed.append({
                "timestamp": dt.isoformat(),
                "source": evt.get("source", "unknown"),
                "type": evt.get("type", ""),
                "description": evt.get("description", ""),
                "artifact": evt.get("artifact", ""),
            })
        else:
            unparseable += 1

    parsed.sort(key=lambda e: e["timestamp"])

    return {
        "file": str(Path(target).absolute()),
        "event_count": len(parsed),
        "unparseable": unparseable,
        "time_range": {
            "start": parsed[0]["timestamp"] if parsed else None,
            "end": parsed[-1]["timestamp"] if parsed else None,
        },
        "events": parsed[:500],
    }


def run_detect_timeline_gaps(target: str, threshold_hours: int = 1) -> dict[str, Any]:
    """Detect time gaps in a timeline that may indicate data deletion or tampering."""
    events, error = _load_events(target)
    if error:
        return error

    parsed = []
    for evt in events:
        dt = _parse_timestamp(str(evt.get("timestamp", "")))
        if dt:
            parsed.append((dt, evt))

    parsed.sort(key=lambda x: x[0])

    gaps = []
    for i in range(1, len(parsed)):
        delta = (parsed[i][0] - parsed[i - 1][0]).total_seconds() / 3600
        if delta > threshold_hours:
            gaps.append({
                "gap_start": parsed[i - 1][0].isoformat(),
                "gap_end": parsed[i][0].isoformat(),
                "duration_hours": round(delta, 2),
                "event_before": parsed[i - 1][1].get("description", "")[:100],
                "event_after": parsed[i][1].get("description", "")[:100],
            })

    return {
        "file": str(Path(target).absolute()),
        "event_count": len(parsed),
        "gap_count": len(gaps),
        "threshold_hours": threshold_hours,
        "gaps": gaps[:100],
    }


def run_correlate_events(target: str, window_minutes: int = 5) -> dict[str, Any]:
    """Correlate events that occur within a specified time window of each other."""
    events, error = _load_events(target)
    if error:
        return error

    parsed = []
    for evt in events:
        dt = _parse_timestamp(str(evt.get("timestamp", "")))
        if dt:
            parsed.append((dt, evt))

    parsed.sort(key=lambda x: x[0])

    clusters = []
    current_cluster = [parsed[0]] if parsed else []
    window_seconds = window_minutes * 60

    for i in range(1, len(parsed)):
        delta = (parsed[i][0] - parsed[i - 1][0]).total_seconds()
        if delta <= window_seconds:
            current_cluster.append(parsed[i])
        else:
            if len(current_cluster) >= 2:
                clusters.append({
                    "time_start": current_cluster[0][0].isoformat(),
                    "time_end": current_cluster[-1][0].isoformat(),
                    "count": len(current_cluster),
                    "sources": list({evt.get("source", "") for _, evt in current_cluster}),
                    "events": [{
                        "timestamp": dt.isoformat(),
                        "source": evt.get("source", ""),
                        "description": evt.get("description", "")[:120],
                    } for dt, evt in current_cluster],
                })
            current_cluster = [parsed[i]]

    if len(current_cluster) >= 2:
        clusters.append({
            "time_start": current_cluster[0][0].isoformat(),
            "time_end": current_cluster[-1][0].isoformat(),
            "count": len(current_cluster),
            "sources": list({evt.get("source", "") for _, evt in current_cluster}),
            "events": [{"timestamp": dt.isoformat(), "source": evt.get("source", ""),
                        "description": evt.get("description", "")[:120]} for dt, evt in current_cluster],
        })

    return {
        "file": str(Path(target).absolute()),
        "event_count": len(parsed),
        "window_minutes": window_minutes,
        "cluster_count": len(clusters),
        "clusters": clusters[:100],
    }


def run_deduplicate_events(target: str, time_tolerance_seconds: float = 1.0) -> dict[str, Any]:
    """Deduplicate timeline events based on near-identical timestamps and content."""
    events, error = _load_events(target)
    if error:
        return error

    parsed = []
    for evt in events:
        dt = _parse_timestamp(str(evt.get("timestamp", "")))
        if dt:
            parsed.append((dt, evt))

    parsed.sort(key=lambda x: x[0])

    unique = [parsed[0]] if parsed else []
    duplicates = []

    for i in range(1, len(parsed)):
        prev_dt, prev_evt = unique[-1]
        curr_dt, curr_evt = parsed[i]
        time_diff = abs((curr_dt - prev_dt).total_seconds())

        prev_desc = prev_evt.get("description", "")
        curr_desc = curr_evt.get("description", "")
        sim = _text_similarity(prev_desc, curr_desc)

        if time_diff <= time_tolerance_seconds and sim > 0.7:
            duplicates.append({
                "timestamp": curr_dt.isoformat(),
                "description": curr_desc[:120],
                "similar_to": prev_desc[:120],
                "similarity": round(sim, 3),
            })
        else:
            unique.append(parsed[i])

    return {
        "file": str(Path(target).absolute()),
        "original_count": len(parsed),
        "deduplicated_count": len(unique),
        "duplicates_removed": len(duplicates),
        "duplicates": duplicates[:100],
        "events": [{
            "timestamp": dt.isoformat(),
            "source": evt.get("source", ""),
            "description": evt.get("description", "")[:200],
        } for dt, evt in unique[:500]],
    }


def _text_similarity(a: str, b: str) -> float:
    """Simple bigram Jaccard similarity for dedup."""
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    a_bigrams = {a[i:i + 2] for i in range(len(a) - 1)}
    b_bigrams = {b[i:i + 2] for i in range(len(b) - 1)}
    if not a_bigrams or not b_bigrams:
        return 0.0
    intersection = a_bigrams & b_bigrams
    union = a_bigrams | b_bigrams
    return len(intersection) / len(union) if union else 0.0


def run_export_timeline_csv(target: str) -> dict[str, Any]:
    """Export a timeline JSON file to CSV format, returning CSV as text."""
    events, error = _load_events(target)
    if error:
        return error

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["timestamp", "source", "type", "description", "artifact"])

    parsed = []
    for evt in events:
        dt = _parse_timestamp(str(evt.get("timestamp", "")))
        if dt:
            parsed.append((dt, evt))
    parsed.sort(key=lambda x: x[0])

    for dt, evt in parsed:
        writer.writerow([
            dt.isoformat(),
            evt.get("source", ""),
            evt.get("type", ""),
            evt.get("description", ""),
            evt.get("artifact", ""),
        ])

    return {
        "file": str(Path(target).absolute()),
        "event_count": len(parsed),
        "csv": output.getvalue(),
    }
