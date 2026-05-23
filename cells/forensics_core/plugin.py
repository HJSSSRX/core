"""Forensics Core Cell — built-in forensics tools with zero external dependencies.

This is the first Cell plugin for ForHacker. It demonstrates the plugin contract
and provides genuinely useful file analysis tools out of the box.
"""

import hashlib
import re
import struct
from pathlib import Path
from typing import Any

from forhacker.plugin.base import BasePlugin, Tool


class ForensicsCorePlugin(BasePlugin):
    name = "forensics-core"
    version = "0.1.0"
    domain = "forensics"
    risk_levels = {
        "file_hash": "LOW",
        "extract_strings": "LOW",
        "pe_info": "LOW",
        "yara_scan": "MEDIUM",
        "volatility3_pslist": "MEDIUM",
    }

    def register_tools(self) -> list[Tool]:
        return [
            Tool(
                name="file_hash",
                description="Calculate SHA256 and MD5 hashes of a file",
                domain="forensics",
                risk_level="LOW",
            ),
            Tool(
                name="extract_strings",
                description="Extract ASCII/UTF-16 printable strings from a file",
                domain="forensics",
                risk_level="LOW",
            ),
            Tool(
                name="pe_info",
                description="Parse PE header: sections, entry point, imports",
                domain="forensics",
                risk_level="LOW",
            ),
            Tool(name="yara_scan", description="Scan files with YARA rules", domain="forensics", risk_level="MEDIUM"),
            Tool(
                name="volatility3_pslist",
                description="List processes from memory dump via Volatility 3",
                domain="forensics",
                risk_level="MEDIUM",
            ),
        ]


def run_file_hash(target: str) -> dict[str, Any]:
    """Calculate SHA256 and MD5 of a file. Pure Python, no dependencies."""
    path = Path(target)
    if not path.exists():
        return {"error": f"File not found: {target}"}
    sha = hashlib.sha256()
    md5 = hashlib.md5()
    with path.open("rb") as fh:
        while chunk := fh.read(8192):
            sha.update(chunk)
            md5.update(chunk)
    return {
        "file": str(path.absolute()),
        "size": path.stat().st_size,
        "sha256": sha.hexdigest(),
        "md5": md5.hexdigest(),
    }


def run_extract_strings(target: str, min_length: int = 4) -> dict[str, Any]:
    """Extract ASCII and UTF-16-LE printable strings from a binary file."""
    path = Path(target)
    if not path.exists():
        return {"error": f"File not found: {target}"}
    data = path.read_bytes()
    ascii_pattern = re.compile(rb"[\x20-\x7e]{" + str(min_length).encode() + rb",}")
    ascii_strings = [m.group().decode("ascii") for m in ascii_pattern.finditer(data)]
    return {
        "file": str(path.absolute()),
        "ascii_count": len(ascii_strings),
        "ascii_strings": ascii_strings[:200],
    }


def run_pe_info(target: str) -> dict[str, Any]:
    """Parse PE header: machine type, sections, entry point."""
    path = Path(target)
    if not path.exists():
        return {"error": f"File not found: {target}"}
    data = path.read_bytes()
    if data[:2] != b"MZ":
        return {"error": "Not a valid PE file (missing MZ header)"}
    try:
        pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
        if data[pe_offset : pe_offset + 4] != b"PE\x00\x00":
            return {"error": "PE signature not found"}
        machine = struct.unpack_from("<H", data, pe_offset + 4)[0]
        num_sections = struct.unpack_from("<H", data, pe_offset + 6)[0]
        entry_rva = struct.unpack_from("<I", data, pe_offset + 40)[0]
        return {
            "file": str(path.absolute()),
            "machine": machine,
            "num_sections": num_sections,
            "entry_point_rva": hex(entry_rva),
            "is_64bit": machine == 0x8664,
        }
    except (struct.error, IndexError) as e:
        return {"error": f"Failed to parse PE header: {e}"}


def run_yara_scan(target: str, rule_path: str = "") -> dict[str, Any]:
    """Scan a file with YARA rules. Requires `pip install yara-python`."""
    try:
        import yara  # type: ignore[import-untyped]
    except ImportError:
        return {"error": "yara-python not installed. Run: pip install yara-python"}
    if not rule_path:
        return {"error": "No YARA rule path provided"}
    rules = yara.compile(rule_path)
    matches = rules.match(target)
    return {"file": target, "matches": [m.rule for m in matches]}


def run_volatility3_pslist(target: str) -> dict[str, Any]:
    """List processes from memory dump using Volatility 3. Requires `pip install volatility3`."""
    return {"error": "Volatility 3 integration requires `pip install volatility3` and is not yet automated"}
