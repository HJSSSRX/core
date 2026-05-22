"""Tests for Timeline Analyzer Cell plugin tools."""

import json
import tempfile
from pathlib import Path

from cells.timeline_analyzer.plugin import (
    TimelineAnalyzerPlugin,
    _parse_timestamp,
    _text_similarity,
    run_build_timeline,
    run_correlate_events,
    run_deduplicate_events,
    run_detect_timeline_gaps,
    run_export_timeline_csv,
)

SAMPLE_EVENTS = [
    {"timestamp": "2024-01-15T10:00:00Z", "source": "browser", "type": "visit",
     "description": "Visited https://example.com", "artifact": "Chrome history"},
    {"timestamp": "2024-01-15T10:30:00Z", "source": "registry", "type": "run_key",
     "description": "Malware.exe added to Run key", "artifact": "HKLM\\...\\Run"},
    {"timestamp": "2024-01-15T12:00:00Z", "source": "filesystem", "type": "create",
     "description": "Created C:\\Temp\\payload.exe", "artifact": "payload.exe"},
    {"timestamp": "2024-01-15T10:00:01Z", "source": "browser", "type": "visit",
     "description": "Visited https://example.com", "artifact": "Chrome history"},
    {"timestamp": "2024-01-16T08:00:00Z", "source": "email", "type": "received",
     "description": "Phishing email received", "artifact": "phish.eml"},
]

GAPPED_EVENTS = [
    {"timestamp": "2024-01-15T10:00:00Z", "source": "log", "description": "Login"},
    {"timestamp": "2024-01-15T14:00:00Z", "source": "log", "description": "Logout"},
    {"timestamp": "2024-01-16T10:00:00Z", "source": "log", "description": "Login again"},
]


def _write_events(events, suffix=".json") -> str:
    with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False, encoding="utf-8") as f:
        json.dump(events, f)
        f.flush()
        return f.name


# === Plugin Registration ===

def test_plugin_registration():
    plugin = TimelineAnalyzerPlugin()
    tools = plugin.register_tools()
    assert len(tools) == 5
    names = {t.name for t in tools}
    assert "build_timeline" in names
    assert "detect_timeline_gaps" in names
    assert "correlate_events" in names


# === Timestamp Parsing ===

def test_parse_timestamp_iso():
    result = _parse_timestamp("2024-01-15T10:30:00Z")
    assert result is not None
    assert result.year == 2024
    assert result.month == 1
    assert result.day == 15


def test_parse_timestamp_date_only():
    result = _parse_timestamp("2024-06-15")
    assert result is not None
    assert result.month == 6


def test_parse_timestamp_invalid():
    result = _parse_timestamp("not a date")
    assert result is None


# === Text Similarity ===

def test_text_similarity_equal():
    assert _text_similarity("hello world", "hello world") == 1.0


def test_text_similarity_different():
    sim = _text_similarity("abcdef", "ghijkl")
    assert sim < 0.5


def test_text_similarity_empty():
    assert _text_similarity("", "hello") == 0.0
    assert _text_similarity("hello", "") == 0.0


# === Build Timeline ===

def test_build_timeline():
    path = _write_events(SAMPLE_EVENTS)
    result = run_build_timeline(path)
    Path(path).unlink(missing_ok=True)
    assert result["event_count"] == 5
    assert result["time_range"]["start"] is not None
    assert result["events"][0]["timestamp"] <= result["events"][-1]["timestamp"]


def test_build_timeline_with_wrapper():
    data = {"events": SAMPLE_EVENTS}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(data, f)
        f.flush()
        path = f.name
    result = run_build_timeline(path)
    Path(path).unlink(missing_ok=True)
    assert result["event_count"] == 5


def test_build_timeline_not_found():
    result = run_build_timeline("/nonexistent/timeline.json")
    assert "error" in result


def test_build_timeline_invalid_json(tmp_path):
    f = tmp_path / "bad.json"
    f.write_text("{not json}")
    result = run_build_timeline(str(f))
    assert "error" in result


# === Detect Gaps ===

def test_detect_timeline_gaps():
    path = _write_events(GAPPED_EVENTS)
    result = run_detect_timeline_gaps(path, threshold_hours=1)
    Path(path).unlink(missing_ok=True)
    assert result["gap_count"] >= 1


def test_detect_timeline_gaps_not_found():
    result = run_detect_timeline_gaps("/nonexistent/timeline.json")
    assert "error" in result


# === Correlate Events ===

def test_correlate_events():
    path = _write_events(SAMPLE_EVENTS)
    result = run_correlate_events(path, window_minutes=5)
    Path(path).unlink(missing_ok=True)
    assert result["cluster_count"] >= 1


def test_correlate_events_empty():
    path = _write_events([])
    result = run_correlate_events(path)
    Path(path).unlink(missing_ok=True)
    assert result["cluster_count"] == 0


def test_correlate_events_not_found():
    result = run_correlate_events("/nonexistent/timeline.json")
    assert "error" in result


# === Deduplicate ===

def test_deduplicate_events():
    path = _write_events(SAMPLE_EVENTS)
    result = run_deduplicate_events(path, time_tolerance_seconds=5)
    Path(path).unlink(missing_ok=True)
    assert result["original_count"] == 5
    assert result["deduplicated_count"] < 5
    assert result["duplicates_removed"] >= 1


def test_deduplicate_events_not_found():
    result = run_deduplicate_events("/nonexistent/timeline.json")
    assert "error" in result


# === Export CSV ===

def test_export_timeline_csv():
    path = _write_events(SAMPLE_EVENTS)
    result = run_export_timeline_csv(path)
    Path(path).unlink(missing_ok=True)
    assert result["event_count"] == 5
    assert "timestamp,source,type,description,artifact" in result["csv"]
    assert "https://example.com" in result["csv"]


def test_export_timeline_not_found():
    result = run_export_timeline_csv("/nonexistent/timeline.json")
    assert "error" in result
