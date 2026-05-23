"""Windows Registry Analyzer Cell — forensic analysis of .reg exports and registry hives.

Tools for parsing Windows registry exports (.reg files), extracting forensic artifacts:
startup entries, USB device history, recent files, shellbags, and installed software.
"""

import re
from collections import Counter
from pathlib import Path
from typing import Any

from forhacker.plugin.base import BasePlugin, Tool


class RegistryAnalyzerPlugin(BasePlugin):
    name = "registry-analyzer"
    version = "0.1.0"
    domain = "forensics"
    risk_levels = {
        "parse_reg": "LOW",
        "detect_startup_entries": "LOW",
        "detect_usb_history": "LOW",
        "detect_recent_files": "LOW",
        "detect_installed_software": "LOW",
    }

    def register_tools(self) -> list[Tool]:
        return [
            Tool(
                name="parse_reg",
                description="Parse a .reg export file into structured key/value pairs",
                domain="forensics",
                risk_level="LOW",
            ),
            Tool(
                name="detect_startup_entries",
                description="Extract persistence/autorun entries from registry exports",
                domain="forensics",
                risk_level="LOW",
            ),
            Tool(
                name="detect_usb_history",
                description="Extract USB device connection history from registry exports",
                domain="forensics",
                risk_level="LOW",
            ),
            Tool(
                name="detect_recent_files",
                description="Extract recently accessed files from registry exports",
                domain="forensics",
                risk_level="LOW",
            ),
            Tool(
                name="detect_installed_software",
                description="List installed software from Uninstall registry keys",
                domain="forensics",
                risk_level="LOW",
            ),
        ]


# === Registry Parser ===

_REG_HEADER = re.compile(r"^Windows Registry Editor Version \d\.\d\d$", re.IGNORECASE)
_KEY_LINE = re.compile(r"^\[(.+)\]$")
_VALUE_LINE = re.compile(r'^"([^"]*)"\s*=\s*(.*)$')
_DELETE_LINE = re.compile(r"^\[-(.+)\]$")
_HEX_VALUE = re.compile(r"^hex(?:\([0-9a-f]+\))?:(.*)", re.IGNORECASE)
_DWORD_VALUE = re.compile(r"^dword:([0-9a-f]+)$", re.IGNORECASE)


def run_parse_reg(target: str) -> dict[str, Any]:
    """Parse a Windows .reg export file into structured key-value pairs."""
    path = Path(target)
    if not path.exists():
        return {"error": f"File not found: {target}"}

    content = (
        path.read_text(encoding="utf-16-le", errors="replace")
        if _is_unicode_reg(path)
        else path.read_text(encoding="utf-8", errors="replace")
    )

    line_number = 0
    current_key = ""
    keys: dict[str, dict[str, str]] = {}
    deleted_keys: list[str] = []
    value_count = 0

    for raw in content.splitlines():
        line_number += 1
        line = raw.strip()
        if not line or _REG_HEADER.match(line):
            continue

        del_match = _DELETE_LINE.match(line)
        if del_match:
            deleted_keys.append(del_match.group(1))
            continue

        key_match = _KEY_LINE.match(line)
        if key_match:
            current_key = key_match.group(1)
            if current_key not in keys:
                keys[current_key] = {}
            continue

        val_match = _VALUE_LINE.match(line)
        if val_match and current_key:
            name, raw_value = val_match.groups()
            value = _decode_value(raw_value)
            keys[current_key][name] = value
            value_count += 1

    return {
        "file": str(path.absolute()),
        "key_count": len(keys),
        "value_count": value_count,
        "deleted_key_count": len(deleted_keys),
        "keys": {k: v for k, v in list(keys.items())[:50]},
    }


def _is_unicode_reg(path: Path) -> bool:
    """Check if .reg file is UTF-16 LE (Windows default)."""
    head = path.read_bytes()[:2]
    return head == b"\xff\xfe"


def _decode_value(raw: str) -> str:
    """Decode a registry value from its raw string representation."""
    raw = raw.strip().strip('"')
    hex_match = _HEX_VALUE.match(raw)
    if hex_match:
        try:
            hex_str = hex_match.group(1).replace(",", "").replace(" ", "").replace("\\\n", "")
            return bytes.fromhex(hex_str).decode("utf-16-le", errors="replace").rstrip("\x00")
        except (ValueError, UnicodeDecodeError):
            return raw[:80] + ("..." if len(raw) > 80 else "")
    dword_match = _DWORD_VALUE.match(raw)
    if dword_match:
        try:
            return str(int(dword_match.group(1), 16))
        except ValueError:
            pass
    return raw


# === Forensic Artifact Extractors ===

STARTUP_PATHS = [
    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
    r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce",
    r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run",
    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer\Run",
]


def run_detect_startup_entries(target: str) -> dict[str, Any]:
    """Extract persistence/autorun entries from registry exports."""
    parsed = run_parse_reg(target)
    if "error" in parsed:
        return parsed

    entries: list[dict[str, str]] = []
    keys = parsed.get("keys", {})

    for full_key, values in keys.items():
        for path in STARTUP_PATHS:
            if full_key.lower().endswith(path.lower()):
                for name, value in values.items():
                    entries.append(
                        {
                            "key_path": full_key,
                            "entry_name": name,
                            "command": value,
                        }
                    )

    return {
        "startup_entry_count": len(entries),
        "entries": entries,
        "risk_note": "Review any suspicious or obfuscated command lines",
    }


USB_PATH = r"SYSTEM\CurrentControlSet\Enum\USB"


def run_detect_usb_history(target: str) -> dict[str, Any]:
    """Extract USB device connection history."""
    parsed = run_parse_reg(target)
    if "error" in parsed:
        return parsed

    devices: list[dict[str, str]] = []
    keys = parsed.get("keys", {})

    for full_key, values in keys.items():
        if USB_PATH.lower() not in full_key.lower():
            continue
        parts = full_key.split("\\")
        if len(parts) >= 5:
            device_info = {
                "key_path": full_key,
                "vid_pid": parts[3] if len(parts) > 3 else "",
                "serial": parts[4] if len(parts) > 4 else "",
            }
            for name, value in values.items():
                device_info[name.lower()] = value
            devices.append(device_info)

    return {
        "usb_device_count": len(devices),
        "devices": devices[:50],
    }


RECENT_PATHS = [
    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs",
    r"NTUSER.DAT\Software\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32\OpenSavePidlMRU",
]


def run_detect_recent_files(target: str) -> dict[str, Any]:
    """Extract recently accessed files and MRU (Most Recently Used) list entries."""
    parsed = run_parse_reg(target)
    if "error" in parsed:
        return parsed

    recent: list[dict[str, str]] = []
    keys = parsed.get("keys", {})

    for full_key, values in keys.items():
        for path in RECENT_PATHS:
            if path.lower() in full_key.lower():
                for name, value in values.items():
                    recent.append(
                        {
                            "key_path": full_key,
                            "entry": name,
                            "value": value[:200],
                        }
                    )

    return {
        "recent_file_count": len(recent),
        "recent_entries": recent[:100],
    }


UNINSTALL_PATHS = [
    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
    r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
]


def run_detect_installed_software(target: str) -> dict[str, Any]:
    """List installed software from Uninstall registry keys."""
    parsed = run_parse_reg(target)
    if "error" in parsed:
        return parsed

    software: list[dict[str, str]] = []
    keys = parsed.get("keys", {})

    for full_key, values in keys.items():
        for path in UNINSTALL_PATHS:
            if path.lower() in full_key.lower():
                display_name = values.get("DisplayName", "")
                if display_name:
                    software.append(
                        {
                            "name": display_name,
                            "version": values.get("DisplayVersion", ""),
                            "publisher": values.get("Publisher", ""),
                            "install_date": values.get("InstallDate", ""),
                            "key_path": full_key,
                        }
                    )

    pub_counter = Counter(s["publisher"] for s in software if s["publisher"])

    return {
        "installed_count": len(software),
        "software": software[:100],
        "top_publishers": pub_counter.most_common(10),
    }
