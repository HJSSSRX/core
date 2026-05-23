"""Network Forensics Cell — packet capture analysis and network intelligence tools.

Built for ForHacker. All tools use pure Python with zero external dependencies
for core functionality. Advanced analysis (pcap parsing) requires optional libs.
"""

import re
import socket
from collections import Counter
from pathlib import Path
from typing import Any, Literal

from forhacker.plugin.base import BasePlugin, Tool


class NetworkForensicsPlugin(BasePlugin):
    name = "network-forensics"
    version = "0.1.0"
    domain = "network"
    risk_levels = {
        "pcap_summary": "LOW",
        "dns_lookup": "LOW",
        "http_header_parse": "LOW",
        "ip_geo_lookup": "MEDIUM",
        "connection_graph": "MEDIUM",
    }

    def register_tools(self) -> list[Tool]:
        return [
            Tool(
                name="pcap_summary",
                description="Summarize a PCAP file — protocol breakdown, top talkers",
                domain="network",
                risk_level="LOW",
            ),
            Tool(
                name="dns_lookup",
                description="Resolve hostname to IP addresses (A/AAAA records)",
                domain="network",
                risk_level="LOW",
            ),
            Tool(
                name="http_header_parse",
                description="Parse HTTP request/response headers from raw text",
                domain="network",
                risk_level="LOW",
            ),
            Tool(
                name="ip_geo_lookup",
                description="Stub: GeoIP lookup (requires MaxMind database)",
                domain="network",
                risk_level="MEDIUM",
            ),
            Tool(
                name="connection_graph",
                description="Extract TCP/UDP connection pairs from netstat output",
                domain="network",
                risk_level="MEDIUM",
            ),
        ]


# === Tool Implementations ===


def run_pcap_summary(target: str) -> dict[str, Any]:
    """Parse basic PCAP structure — protocol counts, top source/dest IPs."""
    path = Path(target)
    if not path.exists():
        return {"error": f"File not found: {target}"}

    data = path.read_bytes()
    result: dict[str, Any] = {"file": str(path.absolute()), "size": len(data)}

    # PCAP magic number check
    if len(data) < 24:
        result["error"] = "File too small to be PCAP"
        return result

    magic = int.from_bytes(data[:4], "little")
    magic2 = int.from_bytes(data[:4], "big")
    if magic == 0xA1B2C3D4:
        result["format"] = "pcap (little-endian)"
        endian: Literal["little", "big"] = "little"
    elif magic2 == 0xA1B2C3D4:
        result["format"] = "pcap (big-endian)"
        endian = "big"
    elif magic == 0xA1B23C4D:
        result["format"] = "pcap-nanosecond (little-endian)"
        endian = "little"
    elif magic2 == 0xA1B23C4D:
        result["format"] = "pcap-nanosecond (big-endian)"
        endian = "big"
    else:
        result["format"] = "unknown"
        result["note"] = "Raw packet analysis requires scapy. Install: pip install scapy"
        return result

    # Count packets
    packet_count = 0
    offset = 24
    while offset + 16 <= len(data):
        incl_len = int.from_bytes(data[offset + 8 : offset + 12], endian)
        packet_count += 1
        offset += 16 + incl_len
        if offset > len(data):
            break

    result["packet_count"] = packet_count
    result["note"] = "Full protocol breakdown requires scapy. Install: pip install scapy"
    return result


def run_dns_lookup(hostname: str) -> dict[str, Any]:
    """Resolve a hostname to IP addresses using system DNS."""
    if not hostname or not hostname.strip():
        return {"error": "No hostname provided"}
    hostname = hostname.strip()
    result: dict[str, Any] = {"hostname": hostname, "addresses": []}
    try:
        info = socket.getaddrinfo(hostname, None)
        seen = set()
        for _, _, _, _, sockaddr in info:
            addr = sockaddr[0]
            if addr not in seen:
                seen.add(addr)
                result["addresses"].append(addr)
    except socket.gaierror as e:
        result["error"] = f"DNS resolution failed: {e}"
    except Exception as e:
        result["error"] = str(e)
    result["resolved_count"] = len(result["addresses"])
    return result


def run_http_header_parse(text: str) -> dict[str, Any]:
    """Parse HTTP request or response headers from raw text."""
    if not text or not text.strip():
        return {"error": "No input text provided"}

    text = text.strip()
    result: dict[str, Any] = {
        "headers": {},
        "request_line": None,
        "status_line": None,
    }

    # Split headers from body
    parts = text.split("\r\n\r\n", 1)
    if len(parts) == 1:
        parts = text.split("\n\n", 1)
    header_block = parts[0]
    body = parts[1] if len(parts) > 1 else ""

    lines = header_block.split("\r\n") if "\r\n" in header_block else header_block.split("\n")

    # First line
    if lines:
        first = lines[0]
        if first.startswith("HTTP/"):
            result["status_line"] = first
        elif "HTTP/" in first:
            result["request_line"] = first

    # Parse header fields
    for line in lines[1:]:
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip().lower()
            value = value.strip()
            result["headers"][key] = value

    result["header_count"] = len(result["headers"])
    result["body_size"] = len(body)
    return result


def run_ip_geo_lookup(ip_address: str) -> dict[str, Any]:
    """GeoIP lookup stub — requires MaxMind GeoLite2 database."""
    return {
        "ip": ip_address,
        "status": "stub",
        "note": "GeoIP lookup requires MaxMind GeoLite2 database. "
        "Download from https://dev.maxmind.com/geoip/geolite2-free-geolocation-data",
    }


def run_connection_graph(text: str) -> dict[str, Any]:
    """Extract TCP/UDP connection pairs from netstat or ss output."""
    if not text or not text.strip():
        return {"error": "No netstat/ss output provided"}

    lines = text.strip().split("\n")
    connections: list[dict] = []
    local_counter: Counter = Counter()
    remote_counter: Counter = Counter()

    # Common patterns: "tcp  0  0  192.168.1.1:443  10.0.0.1:52341  ESTABLISHED"
    conn_pattern = re.compile(
        r"(tcp|udp)\S*\s+\d+\s+\d+\s+"
        r"([0-9a-f.:\[\]]+)[:\.](\d+)\s+"
        r"([0-9a-f.:\[\]]+)[:\.](\d+)\s*"
        r"(\S*)",
        re.IGNORECASE,
    )

    for line in lines:
        m = conn_pattern.search(line)
        if m:
            proto, local_ip, local_port, remote_ip, remote_port, state = m.groups()
            conn = {
                "proto": proto.lower(),
                "local": f"{local_ip}:{local_port}",
                "remote": f"{remote_ip}:{remote_port}",
                "state": state or "unknown",
            }
            connections.append(conn)
            local_counter[f"{local_ip}"] += 1
            remote_counter[f"{remote_ip}"] += 1

    return {
        "connection_count": len(connections),
        "connections": connections,
        "top_local_ips": local_counter.most_common(10),
        "top_remote_ips": remote_counter.most_common(10),
    }
