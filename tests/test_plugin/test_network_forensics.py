"""Tests for the Network Forensics Cell plugin tools."""

import tempfile
from pathlib import Path

from cells.network_forensics.plugin import (
    NetworkForensicsPlugin,
    run_connection_graph,
    run_dns_lookup,
    run_http_header_parse,
    run_ip_geo_lookup,
    run_pcap_summary,
)


def test_plugin_registration():
    plugin = NetworkForensicsPlugin()
    tools = plugin.register_tools()
    assert len(tools) == 5
    tool_names = {t.name for t in tools}
    assert "pcap_summary" in tool_names
    assert "dns_lookup" in tool_names


def test_pcap_summary_too_small():
    with tempfile.NamedTemporaryFile(suffix=".pcap", delete=False) as f:
        f.write(b"\x00" * 10)
        f.flush()
        result = run_pcap_summary(f.name)
    Path(f.name).unlink(missing_ok=True)
    assert "error" in result


def test_pcap_summary_basic():
    # Build a minimal valid PCAP (little-endian)
    header = bytes.fromhex("D4C3B2A1" "0200" "0400" "00000000" "00000000" "00000400" "01000000")
    # Packet header: ts_sec=0, ts_usec=0, incl_len=0, orig_len=0
    pkt_header = bytes(16)
    data = header + pkt_header
    with tempfile.NamedTemporaryFile(suffix=".pcap", delete=False) as f:
        f.write(data)
        f.flush()
        path = f.name
    result = run_pcap_summary(path)
    Path(path).unlink(missing_ok=True)
    assert result["format"].startswith("pcap")
    assert "packet_count" in result


def test_dns_lookup_localhost():
    result = run_dns_lookup("localhost")
    assert result["resolved_count"] >= 1 or "error" in result


def test_dns_lookup_empty():
    result = run_dns_lookup("")
    assert "error" in result


def test_http_header_parse_request():
    text = (
        "GET /index.html HTTP/1.1\r\n"
        "Host: example.com\r\n"
        "User-Agent: Mozilla/5.0\r\n"
        "Accept: text/html\r\n"
        "\r\n"
        "<html>body</html>"
    )
    result = run_http_header_parse(text)
    assert result["header_count"] == 3
    assert result["headers"]["host"] == "example.com"
    assert result["request_line"] == "GET /index.html HTTP/1.1"
    assert result["body_size"] == 17


def test_http_header_parse_response():
    text = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: 5\r\n\r\nhello"
    result = run_http_header_parse(text)
    assert result["status_line"] == "HTTP/1.1 200 OK"
    assert result["headers"]["content-type"] == "text/html"
    assert result["body_size"] == 5


def test_http_header_parse_empty():
    result = run_http_header_parse("")
    assert "error" in result


def test_ip_geo_lookup_stub():
    result = run_ip_geo_lookup("8.8.8.8")
    assert result["status"] == "stub"


def test_connection_graph_netstat():
    text = (
        "tcp  0  0  192.168.1.100:443   10.0.0.50:52341   ESTABLISHED\n"
        "tcp  0  0  192.168.1.100:80    10.0.0.51:61234   ESTABLISHED\n"
        "udp  0  0  0.0.0.0:53          0.0.0.0:0         LISTEN\n"
    )
    result = run_connection_graph(text)
    assert result["connection_count"] == 3
    assert len(result["connections"]) == 3
    assert result["connections"][0]["proto"] == "tcp"
    assert result["connections"][0]["local"] == "192.168.1.100:443"
    assert len(result["top_local_ips"]) > 0


def test_connection_graph_empty():
    result = run_connection_graph("")
    assert "error" in result


def test_pcap_summary_not_found():
    result = run_pcap_summary("/nonexistent/file.pcap")
    assert "error" in result


def test_pcap_summary_big_endian():
    # Build a minimal valid PCAP (big-endian)
    header = bytes.fromhex("A1B2C3D4" "0002" "0004" "00000000" "00000000" "00040000" "00000001")
    pkt_header = bytes(16)
    data = header + pkt_header
    with tempfile.NamedTemporaryFile(suffix=".pcap", delete=False) as f:
        f.write(data)
        f.flush()
        path = f.name
    result = run_pcap_summary(path)
    Path(path).unlink(missing_ok=True)
    assert result["format"].startswith("pcap (big")


def test_pcap_summary_nanosecond():
    # Build a minimal valid nanosecond PCAP (little-endian)
    header = bytes.fromhex("4D3CB2A1" "0200" "0400" "00000000" "00000000" "00000400" "01000000")
    pkt_header = bytes(16)
    data = header + pkt_header
    with tempfile.NamedTemporaryFile(suffix=".pcap", delete=False) as f:
        f.write(data)
        f.flush()
        path = f.name
    result = run_pcap_summary(path)
    Path(path).unlink(missing_ok=True)
    assert result["format"].startswith("pcap-nanosecond")


def test_pcap_summary_unknown_format():
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        f.write(b"\x00" * 40)
        f.flush()
        path = f.name
    result = run_pcap_summary(path)
    Path(path).unlink(missing_ok=True)
    assert result["format"] == "unknown"


def test_dns_lookup_invalid_hostname():
    result = run_dns_lookup("this-hostname-definitely-does-not-exist-12345.invalid")
    assert "error" in result or result["resolved_count"] == 0


def test_http_header_parse_unix_newlines():
    text = "GET /api HTTP/1.1\nHost: example.com\nAccept: */*\n\nbody"
    result = run_http_header_parse(text)
    assert result["request_line"] == "GET /api HTTP/1.1"
    assert result["headers"]["host"] == "example.com"
    assert result["body_size"] == 4


def test_connection_graph_no_match():
    text = "Active Internet connections\nProto Recv-Q Send-Q Local Address Foreign Address State\nsome random text"
    result = run_connection_graph(text)
    assert result["connection_count"] == 0
