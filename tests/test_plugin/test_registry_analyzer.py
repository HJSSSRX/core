from __future__ import annotations

"""Tests for Registry Analyzer Cell plugin tools."""

import tempfile
from pathlib import Path

from cells.registry_analyzer.plugin import (
    RegistryAnalyzerPlugin,
    _decode_value,
    _is_unicode_reg,
    run_detect_installed_software,
    run_detect_recent_files,
    run_detect_startup_entries,
    run_detect_usb_history,
    run_parse_reg,
)

SAMPLE_REG = """Windows Registry Editor Version 5.00

[HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run]
"SecurityHealth"="%windir%\\\\system32\\\\SecurityHealthSystray.exe"

[HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Firefox]
"DisplayName"="Mozilla Firefox"
"DisplayVersion"="120.0"
"Publisher"="Mozilla"
"InstallDate"="20240101"
"""


def test_plugin_registration():
    plugin = RegistryAnalyzerPlugin()
    tools = plugin.register_tools()
    assert len(tools) == 5
    names = {t.name for t in tools}
    assert "parse_reg" in names
    assert "detect_startup_entries" in names


def test_is_unicode_reg():
    with tempfile.NamedTemporaryFile(suffix=".reg", delete=False) as f:
        f.write(b"\xff\xfe" + "test".encode("utf-16-le"))
        f.flush()
        result = _is_unicode_reg(Path(f.name))
    Path(f.name).unlink(missing_ok=True)
    assert result is True


def test_is_not_unicode_reg():
    with tempfile.NamedTemporaryFile(suffix=".reg", delete=False) as f:
        f.write(b"Windows Registry Editor Version 5.00\n")
        f.flush()
        result = _is_unicode_reg(Path(f.name))
    Path(f.name).unlink(missing_ok=True)
    assert result is False


def test_decode_dword():
    result = _decode_value("dword:00000001")
    assert result == "1"


def test_decode_string():
    result = _decode_value('"C:\\Program Files\\App\\app.exe"')
    assert "Program Files" in result


def test_parse_reg_basic():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".reg", delete=False, encoding="utf-8") as f:
        f.write(SAMPLE_REG)
        f.flush()
        path = f.name
    result = run_parse_reg(path)
    Path(path).unlink(missing_ok=True)
    assert result["key_count"] == 2
    assert result["value_count"] >= 1


def test_parse_reg_not_found():
    result = run_parse_reg("/nonexistent/file.reg")
    assert "error" in result


def test_detect_startup_entries():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".reg", delete=False, encoding="utf-8") as f:
        f.write(SAMPLE_REG)
        f.flush()
        path = f.name
    result = run_detect_startup_entries(path)
    Path(path).unlink(missing_ok=True)
    assert result["startup_entry_count"] >= 1
    assert any("SecurityHealth" in e.get("entry_name", "") for e in result["entries"])


def test_detect_usb_history_empty():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".reg", delete=False, encoding="utf-8") as f:
        f.write(
            "Windows Registry Editor Version 5.00\n\n"
            "[HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Enum\\USB\\VID_0781&PID_5591\\123456]\n"
            '"DeviceDesc"="@usbstor.inf,%usb\\\\class_08.devicedesc%;USB Mass Storage Device"\n'
            "\n"
            "[HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run]\n"
            '"TestApp"="C:\\\\Test\\\\app.exe"\n'
        )
        f.flush()
        path = f.name
    result = run_detect_usb_history(path)
    Path(path).unlink(missing_ok=True)
    assert result["usb_device_count"] >= 1


def test_detect_recent_files_empty():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".reg", delete=False, encoding="utf-8") as f:
        f.write(
            "Windows Registry Editor Version 5.00\n\n"
            "[HKEY_CURRENT_USER\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\RecentDocs\\.txt]\n"
            '"0"="report.txt"\n'
        )
        f.flush()
        path = f.name
    result = run_detect_recent_files(path)
    Path(path).unlink(missing_ok=True)
    assert result["recent_file_count"] >= 1


def test_detect_installed_software():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".reg", delete=False, encoding="utf-8") as f:
        f.write(SAMPLE_REG)
        f.flush()
        path = f.name
    result = run_detect_installed_software(path)
    Path(path).unlink(missing_ok=True)
    assert result["installed_count"] >= 1
    assert any("Firefox" in s.get("name", "") for s in result["software"])
    assert len(result["top_publishers"]) >= 1


def test_parse_reg_with_delete_key():
    content = "Windows Registry Editor Version 5.00\n\n"
    content += "[-HKEY_LOCAL_MACHINE\\SOFTWARE\\DeletedApp]\n"
    content += "[HKEY_LOCAL_MACHINE\\SOFTWARE\\KeptApp]\n"
    content += '"Value"="test"\n'
    with tempfile.NamedTemporaryFile(mode="w", suffix=".reg", delete=False, encoding="utf-8") as f:
        f.write(content)
        f.flush()
        path = f.name
    result = run_parse_reg(path)
    Path(path).unlink(missing_ok=True)
    assert result["deleted_key_count"] == 1
    assert result["key_count"] == 1


def test_decode_hex_value():
    # "Test" in UTF-16LE hex: 54 00 65 00 73 00 74 00
    result = _decode_value("hex:54,00,65,00,73,00,74,00")
    assert "Test" in result


def test_decode_hex_invalid():
    result = _decode_value("hex:ZZ,ZZ,ZZ")
    assert len(result) <= 80


def test_decode_dword_invalid():
    result = _decode_value("dword:NOTHEX")
    assert "dword" in result.lower() or len(result) > 0


def test_detect_startup_entries_not_found():
    result = run_detect_startup_entries("/nonexistent/file.reg")
    assert "error" in result


def test_detect_usb_history_not_found():
    result = run_detect_usb_history("/nonexistent/file.reg")
    assert "error" in result


def test_detect_recent_files_not_found():
    result = run_detect_recent_files("/nonexistent/file.reg")
    assert "error" in result


def test_detect_installed_software_not_found():
    result = run_detect_installed_software("/nonexistent/file.reg")
    assert "error" in result
