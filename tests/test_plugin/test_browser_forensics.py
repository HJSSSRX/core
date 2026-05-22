"""Tests for Browser Forensics Cell plugin tools."""

import datetime
import json
import sqlite3
import tempfile
from pathlib import Path

import pytest

from cells.browser_forensics.plugin import (
    BrowserForensicsPlugin,
    _chrome_time,
    run_browser_downloads,
    run_chrome_cookies,
    run_chrome_history,
    run_extract_bookmarks,
    run_firefox_history,
)


def _make_chrome_history_db() -> str:
    """Create a temporary Chrome History SQLite DB with sample data."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    conn = sqlite3.connect(tmp.name)
    conn.execute(
        "CREATE TABLE urls (id INTEGER PRIMARY KEY, url TEXT, title TEXT, "
        "visit_count INTEGER, last_visit_time INTEGER)"
    )
    # last_visit_time: 13300000000000000 ~= 2022-06-15
    conn.execute(
        "INSERT INTO urls (url, title, visit_count, last_visit_time) VALUES (?, ?, ?, ?)",
        ("https://example.com", "Example Site", 5, 13300000000000000),
    )
    conn.execute(
        "INSERT INTO urls (url, title, visit_count, last_visit_time) VALUES (?, ?, ?, ?)",
        ("https://test.org", "Test Org", 2, 13300000000000001),
    )
    conn.commit()
    conn.close()
    return tmp.name


def _make_firefox_history_db() -> str:
    """Create a temporary Firefox places.sqlite with sample data."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    conn = sqlite3.connect(tmp.name)
    conn.execute(
        "CREATE TABLE moz_places (id INTEGER PRIMARY KEY, url TEXT, title TEXT, "
        "visit_count INTEGER, last_visit_date INTEGER)"
    )
    # last_visit_date: microseconds since epoch
    ts = int(datetime.datetime(2024, 1, 15).timestamp() * 1_000_000)
    conn.execute(
        "INSERT INTO moz_places (url, title, visit_count, last_visit_date) VALUES (?, ?, ?, ?)",
        ("https://mozilla.org", "Mozilla", 10, ts),
    )
    conn.commit()
    conn.close()
    return tmp.name


def _make_cookies_db() -> str:
    """Create a temporary Chrome Cookies SQLite DB."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    conn = sqlite3.connect(tmp.name)
    conn.execute(
        "CREATE TABLE cookies (creation_utc INTEGER, host_key TEXT, name TEXT, "
        "encrypted_value BLOB, expires_utc INTEGER, is_secure INTEGER, is_httponly INTEGER)"
    )
    conn.execute(
        "INSERT INTO cookies VALUES (?, ?, ?, ?, ?, ?, ?)",
        (13300000000000000, ".example.com", "session", b"encrypted_blob", 13310000000000000, 1, 1),
    )
    conn.commit()
    conn.close()
    return tmp.name


def _make_downloads_db() -> str:
    """Create a temporary Chrome Downloads SQLite DB."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    conn = sqlite3.connect(tmp.name)
    conn.execute(
        "CREATE TABLE downloads (id INTEGER PRIMARY KEY, target_path TEXT, tab_url TEXT, "
        "total_bytes INTEGER, received_bytes INTEGER, start_time INTEGER, end_time INTEGER, "
        "state INTEGER, danger_type INTEGER)"
    )
    conn.execute(
        "INSERT INTO downloads VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (1, "C:\\Downloads\\setup.exe", "https://example.com/dl", 1024000, 1024000,
         13300000000000000, 13300000000000001, 1, 0),
    )
    conn.commit()
    conn.close()
    return tmp.name


def _make_bookmarks_json():
    """Create a temporary Chrome Bookmarks JSON file."""
    data = {
        "roots": {
            "bookmark_bar": {
                "type": "folder",
                "name": "Bookmark Bar",
                "children": [
                    {"type": "url", "name": "Google", "url": "https://google.com", "date_added": "13300000000000000"},
                    {"type": "url", "name": "GitHub", "url": "https://github.com", "date_added": "0"},
                ],
            },
            "other": {
                "type": "folder",
                "name": "Other Bookmarks",
                "children": [
                    {"type": "folder", "name": "Work",
                     "children": [
                         {"type": "url", "name": "Jira", "url": "https://jira.example.com", "date_added": "13300000000000001"},
                     ]},
                ],
            },
        }
    }
    return data


# === Plugin Registration ===

def test_plugin_registration():
    plugin = BrowserForensicsPlugin()
    tools = plugin.register_tools()
    assert len(tools) == 5
    names = {t.name for t in tools}
    assert "chrome_history" in names
    assert "firefox_history" in names
    assert "chrome_cookies" in names
    assert "browser_downloads" in names
    assert "extract_bookmarks" in names


# === Chrome Time Conversion ===

def test_chrome_time_valid():
    # 13300000000000000 microseconds from 1601-01-01
    result = _chrome_time(13300000000000000)
    assert "202" in result  # some year in the 2020s


def test_chrome_time_zero():
    result = _chrome_time(0)
    assert result == ""


def test_chrome_time_negative():
    result = _chrome_time(-1)
    assert result == ""


def test_chrome_time_overflow():
    result = _chrome_time(10 ** 30)
    assert isinstance(result, str)


# === Chrome History ===

def test_chrome_history_basic():
    db_path = _make_chrome_history_db()
    result = run_chrome_history(db_path)
    Path(db_path).unlink(missing_ok=True)
    assert result["entry_count"] == 2
    urls = {e["url"] for e in result["entries"]}
    assert "https://example.com" in urls
    assert "https://test.org" in urls


def test_chrome_history_not_found():
    result = run_chrome_history("/nonexistent/history.db")
    assert "error" in result


def test_chrome_history_invalid_db(tmp_path):
    f = tmp_path / "bad.db"
    f.write_text("not a sqlite db")
    result = run_chrome_history(str(f))
    assert "error" in result


# === Firefox History ===

def test_firefox_history_basic():
    db_path = _make_firefox_history_db()
    result = run_firefox_history(db_path)
    Path(db_path).unlink(missing_ok=True)
    assert result["entry_count"] == 1
    assert result["entries"][0]["url"] == "https://mozilla.org"


def test_firefox_history_not_found():
    result = run_firefox_history("/nonexistent/places.sqlite")
    assert "error" in result


# === Chrome Cookies ===

def test_chrome_cookies_basic():
    db_path = _make_cookies_db()
    result = run_chrome_cookies(db_path)
    Path(db_path).unlink(missing_ok=True)
    assert result["cookie_count"] == 1
    assert result["cookies"][0]["host"] == ".example.com"
    assert result["cookies"][0]["secure"] is True


def test_chrome_cookies_not_found():
    result = run_chrome_cookies("/nonexistent/cookies.db")
    assert "error" in result


# === Browser Downloads ===

def test_browser_downloads_basic():
    db_path = _make_downloads_db()
    result = run_browser_downloads(db_path)
    Path(db_path).unlink(missing_ok=True)
    assert result["download_count"] == 1
    assert result["downloads"][0]["state"] == "complete"


def test_browser_downloads_not_found():
    result = run_browser_downloads("/nonexistent/history.db")
    assert "error" in result


# === Extract Bookmarks ===

def test_extract_bookmarks_basic():
    data = _make_bookmarks_json()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(data, f)
        f.flush()
        path = f.name
    result = run_extract_bookmarks(path)
    Path(path).unlink(missing_ok=True)
    assert result["bookmark_count"] == 3
    names = {b["name"] for b in result["bookmarks"]}
    assert "Google" in names
    assert "GitHub" in names
    assert "Jira" in names


def test_extract_bookmarks_not_found():
    result = run_extract_bookmarks("/nonexistent/bookmarks.json")
    assert "error" in result


def test_extract_bookmarks_invalid_json(tmp_path):
    f = tmp_path / "bad.json"
    f.write_text("{not valid json")
    result = run_extract_bookmarks(str(f))
    assert "error" in result


def test_extract_bookmarks_max_rows():
    data = _make_bookmarks_json()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(data, f)
        f.flush()
        path = f.name
    result = run_extract_bookmarks(path, max_rows=1)
    Path(path).unlink(missing_ok=True)
    assert result["bookmark_count"] == 1
