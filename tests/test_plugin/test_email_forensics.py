from __future__ import annotations

"""Tests for Email Forensics Cell plugin tools."""

import tempfile
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from cells.email_forensics.plugin import (
    EmailForensicsPlugin,
    run_analyze_attachments,
    run_detect_phishing_indicators,
    run_extract_email_headers,
    run_parse_eml,
    run_parse_mbox,
)


def _make_eml(
    subject="Test Email", from_addr="sender@example.com", to_addr="recipient@example.com", body="Hello world."
) -> str:
    """Create a temporary .eml file and return its path."""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Date"] = "Mon, 15 Jan 2024 10:00:00 +0000"
    msg["Message-ID"] = "<test123@example.com>"
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".eml", delete=False) as f:
        f.write(msg.as_bytes())
        f.flush()
        return f.name


def _make_multipart_eml() -> str:
    """Create a multipart .eml with text, HTML, and attachment."""
    msg = MIMEMultipart()
    msg["Subject"] = "Report"
    msg["From"] = "boss@corp.com"
    msg["To"] = "employee@corp.com"
    msg["Date"] = "Tue, 16 Jan 2024 14:00:00 +0000"
    msg.attach(MIMEText("Plain text body", "plain"))
    msg.attach(MIMEText("<html><body>HTML body</body></html>", "html"))
    att = MIMEBase("application", "octet-stream")
    att.set_payload(b"\x00\x01\x02\x03")
    att.add_header("Content-Disposition", "attachment", filename="data.bin")
    msg.attach(att)
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".eml", delete=False) as f:
        f.write(msg.as_bytes())
        f.flush()
        return f.name


def _make_phishing_eml() -> str:
    """Create a .eml with phishing indicators."""
    msg = MIMEText(
        "Dear valued customer,\n\n"
        "Your account has been suspended. Click here to verify:\n"
        "https://192.168.1.1/verify\n\n"
        "Act now or lose access!\n"
    )
    msg["Subject"] = "URGENT: Verify your account immediately"
    msg["From"] = "support@paypa1.com"
    msg["To"] = "victim@example.com"
    msg["Return-Path"] = "<scammer@evil.org>"
    msg["Date"] = "Wed, 17 Jan 2024 08:00:00 +0000"
    msg["Authentication-Results"] = "spf=fail smtp.mailfrom=paypa1.com; dkim=fail"
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".eml", delete=False) as f:
        f.write(msg.as_bytes())
        f.flush()
        return f.name


def _make_mbox() -> str:
    """Create a temporary mbox file with two messages."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".mbox", delete=False, encoding="utf-8") as f:
        f.write("From sender@example.com Mon Jan 15 10:00:00 2024\n")
        f.write("From: alice@example.com\n")
        f.write("To: bob@example.com\n")
        f.write("Subject: First message\n")
        f.write("Date: Mon, 15 Jan 2024 10:00:00 +0000\n")
        f.write("\n")
        f.write("Body of first message.\n")
        f.write("\n")
        f.write("From sender2@example.com Tue Jan 16 11:00:00 2024\n")
        f.write("From: carol@example.com\n")
        f.write("To: dave@example.com\n")
        f.write("Subject: Second message\n")
        f.write("Date: Tue, 16 Jan 2024 11:00:00 +0000\n")
        f.write("\n")
        f.write("Body of second message.\n")
        f.write("\n")
        f.flush()
        return f.name


# === Plugin Registration ===


def test_plugin_registration():
    plugin = EmailForensicsPlugin()
    tools = plugin.register_tools()
    assert len(tools) == 5
    names = {t.name for t in tools}
    assert "parse_eml" in names
    assert "extract_email_headers" in names
    assert "detect_phishing_indicators" in names


# === Parse EML ===


def test_parse_eml_basic():
    path = _make_eml()
    result = run_parse_eml(path)
    Path(path).unlink(missing_ok=True)
    assert result["subject"] == "Test Email"
    assert result["from"] == "sender@example.com"
    assert "Hello world" in result["body_text_preview"]


def test_parse_eml_multipart():
    path = _make_multipart_eml()
    result = run_parse_eml(path)
    Path(path).unlink(missing_ok=True)
    assert result["attachment_count"] == 1
    assert result["has_html_body"] is True
    assert result["attachments"][0]["filename"] == "data.bin"


def test_parse_eml_not_found():
    result = run_parse_eml("/nonexistent/mail.eml")
    assert "error" in result


# === Extract Headers ===


def test_extract_email_headers():
    path = _make_eml()
    result = run_extract_email_headers(path)
    Path(path).unlink(missing_ok=True)
    assert result["from"] == "sender@example.com"
    assert result["subject"] == "Test Email"
    assert "message_id" in result
    assert "received_count" in result


def test_extract_email_headers_not_found():
    result = run_extract_email_headers("/nonexistent/mail.eml")
    assert "error" in result


# === Analyze Attachments ===


def test_analyze_attachments():
    path = _make_multipart_eml()
    result = run_analyze_attachments(path)
    Path(path).unlink(missing_ok=True)
    assert result["attachment_count"] == 1
    assert len(result["attachments"][0]["sha256"]) == 64
    assert result["attachments"][0]["size"] == 4


def test_analyze_attachments_not_found():
    result = run_analyze_attachments("/nonexistent/mail.eml")
    assert "error" in result


# === Phishing Detection ===


def test_detect_phishing_indicators():
    path = _make_phishing_eml()
    result = run_detect_phishing_indicators(path)
    Path(path).unlink(missing_ok=True)
    assert result["indicator_count"] >= 3
    indicators = result["indicators_found"]
    assert "mismatched_from" in indicators
    assert "urgent_language" in indicators or "spf_fail" in indicators


def test_detect_phishing_clean():
    path = _make_eml()
    result = run_detect_phishing_indicators(path)
    Path(path).unlink(missing_ok=True)
    assert result["risk_level"] == "LOW"


def test_detect_phishing_not_found():
    result = run_detect_phishing_indicators("/nonexistent/mail.eml")
    assert "error" in result


# === Parse Mbox ===


def test_parse_mbox_basic():
    path = _make_mbox()
    result = run_parse_mbox(path)
    Path(path).unlink(missing_ok=True)
    assert result["total_messages"] == 2
    assert result["parsed_count"] == 2
    assert result["messages"][0]["subject"] == "First message"


def test_parse_mbox_not_found():
    result = run_parse_mbox("/nonexistent/mbox")
    assert "error" in result
