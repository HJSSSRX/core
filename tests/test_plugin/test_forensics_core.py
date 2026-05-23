import struct
import tempfile
from pathlib import Path

from cells.forensics_core.plugin import (
    ForensicsCorePlugin,
    run_extract_strings,
    run_file_hash,
    run_pe_info,
    run_yara_scan,
)
from forhacker.plugin.manager import PluginManager
from forhacker.task.capability import CapabilityRegistry


def test_plugin_registers_five_tools():
    plugin = ForensicsCorePlugin()
    tools = plugin.register_tools()
    assert len(tools) == 5
    names = {t.name for t in tools}
    assert "file_hash" in names
    assert "extract_strings" in names
    assert "pe_info" in names


def test_file_hash(tmp_path):
    f = tmp_path / "test.bin"
    f.write_bytes(b"Hello World" * 100)
    result = run_file_hash(str(f))
    assert len(result["sha256"]) == 64
    assert len(result["md5"]) == 32
    assert result["size"] == 1100
    assert result["file"]


def test_file_hash_not_found():
    result = run_file_hash("/nonexistent/file.bin")
    assert "error" in result


def test_extract_strings(tmp_path):
    f = tmp_path / "strings.bin"
    f.write_bytes(b"\x00ABC\x00\x00DEFG\x00Hello World!")
    result = run_extract_strings(str(f), min_length=3)
    assert result["ascii_count"] >= 1


def test_extract_strings_not_found():
    result = run_extract_strings("/nonexistent/file")
    assert "error" in result


def test_pe_info_valid():
    with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as tf:
        # MZ header
        tf.write(b"MZ\x00\x00" + b"\x00" * 0x38 + struct.pack("<I", 0x40))
        # PE signature + COFF header (Machine + NumSections + 16 bytes rest)
        # Optional header: 16 bytes before AddressOfEntryPoint
        tf.write(
            b"PE\x00\x00"
            + struct.pack("<H", 0x8664)  # Machine: AMD64
            + struct.pack("<H", 3)  # NumberOfSections
            + b"\x00" * 16  # Rest of COFF header
            + b"\x00" * 16  # Optional header before AddressOfEntryPoint
            + struct.pack("<I", 0x1000)  # AddressOfEntryPoint
        )
        tf.flush()
        result = run_pe_info(tf.name)
    # Clean up
    Path(tf.name).unlink(missing_ok=True)
    assert result["is_64bit"] is True
    assert result["num_sections"] == 3
    assert result["entry_point_rva"] == "0x1000"


def test_pe_info_not_pe(tmp_path):
    f = tmp_path / "notpe.txt"
    f.write_text("just text")
    result = run_pe_info(str(f))
    assert "error" in result


def test_yara_scan_file_not_found():
    result = run_yara_scan("/nonexistent/file.bin")
    assert "error" in result


def test_yara_scan_works(tmp_path):
    import yara  # type: ignore[import-untyped]
    f = tmp_path / "test.bin"
    f.write_text("This contains a suspicious PowerShell IEX command and a keylogger string")
    result = run_yara_scan(str(f))
    assert "error" not in result
    assert "match_count" in result
    assert result["file"] == str(f.absolute())


def test_pe_info_not_found():
    result = run_pe_info("/nonexistent/file.exe")
    assert "error" in result


def test_pe_info_mz_but_no_pe_sig(tmp_path):
    f = tmp_path / "fake.exe"
    # MZ header with PE offset pointing to non-PE data
    data = bytearray(b"MZ" + b"\x00" * 0x3E)
    struct.pack_into("<I", data, 0x3C, 0x40)
    data += b"\x00" * 0x40 + b"XXXX"
    f.write_bytes(data)
    result = run_pe_info(str(f))
    assert "error" in result


def test_pe_info_corrupt_header(tmp_path):
    f = tmp_path / "corrupt.exe"
    # Truncated file: PE offset at 0x3C but not enough data to unpack
    f.write_bytes(b"MZ" + b"\x00" * 0x3A)  # 60 bytes < 64 needed
    result = run_pe_info(str(f))
    assert "error" in result


def test_volatility3_pslist_file_not_found():
    from cells.forensics_core.plugin import run_volatility3_pslist

    result = run_volatility3_pslist("/nonexistent/memory.dmp")
    assert "error" in result


def test_volatility3_pslist_not_a_dump(tmp_path):
    from cells.forensics_core.plugin import run_volatility3_pslist

    f = tmp_path / "not_memory.dmp"
    f.write_text("not a memory dump")
    result = run_volatility3_pslist(str(f))
    assert "error" in result


def test_plugin_loads_in_manager():
    registry = CapabilityRegistry()
    manager = PluginManager(registry=registry)
    plugin = ForensicsCorePlugin()
    manager.load_plugin(plugin)
    assert "forensics-core" in manager.loaded_plugins
    assert len(registry.query(domain="forensics")) == 5
