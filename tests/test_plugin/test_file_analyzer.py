from __future__ import annotations

from cells.file_analyzer.plugin import (
    FileAnalyzerPlugin,
    run_calculate_entropy,
    run_detect_file_type,
    run_file_timeline,
)


def test_plugin_registers_tools():
    plugin = FileAnalyzerPlugin()
    tools = plugin.register_tools()
    assert len(tools) == 3
    names = {t.name for t in tools}
    assert "detect_file_type" in names
    assert "calculate_entropy" in names
    assert "file_timeline" in names


def test_detect_pdf(tmp_path):
    f = tmp_path / "doc.pdf"
    f.write_bytes(b"%PDF-1.4 fake pdf content here")
    result = run_detect_file_type(str(f))
    assert "pdf" in result["magic_matches"]


def test_detect_zip(tmp_path):
    f = tmp_path / "archive.zip"
    f.write_bytes(b"PK\x03\x04" + b"\x00" * 100)
    result = run_detect_file_type(str(f))
    assert "zip" in result["magic_matches"] or "docx" in result["magic_matches"]


def test_detect_exe(tmp_path):
    f = tmp_path / "program.exe"
    f.write_bytes(b"MZ" + b"\x00" * 100)
    result = run_detect_file_type(str(f))
    assert "exe" in result["magic_matches"]


def test_detect_unknown(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x00\x01\x02\x03" * 4)
    result = run_detect_file_type(str(f))
    assert result["likely_type"] == "unknown"


def test_detect_not_found():
    result = run_detect_file_type("/nonexistent/file")
    assert "error" in result


def test_entropy_encrypted(tmp_path):
    f = tmp_path / "random.bin"
    f.write_bytes(b"\x00\x01\x02\x03" * 1000)  # uniform distribution = low entropy
    result = run_calculate_entropy(str(f))
    assert result["verdict"] == "low_entropy_text_or_sparse"


def test_entropy_empty(tmp_path):
    f = tmp_path / "empty.bin"
    f.write_bytes(b"")
    result = run_calculate_entropy(str(f))
    assert result["entropy"] == 0.0
    assert result["verdict"] == "empty"


def test_file_timeline(tmp_path):
    (tmp_path / "a.txt").write_text("aaa")
    (tmp_path / "b.txt").write_text("bbb")
    result = run_file_timeline(str(tmp_path))
    assert result["file_count"] == 2
    assert len(result["entries"]) == 2


def test_file_timeline_not_found():
    result = run_file_timeline("/nonexistent/dir")
    assert "error" in result
