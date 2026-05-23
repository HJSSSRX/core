from __future__ import annotations

"""Tests for evidence CLI commands — verify, purge-orphans."""

import hashlib
from pathlib import Path

from click.testing import CliRunner

from forhacker.cli.main import cli


def test_evidence_verify_no_dir():
    runner = CliRunner()
    result = runner.invoke(cli, ["evidence", "verify", "nonexistent_case"])
    assert result.exit_code == 0
    assert "No evidence" in result.output


def test_evidence_verify_empty_dir(tmp_path):
    evidence_dir = tmp_path / "shared" / "cases" / "testcase" / "evidence"
    evidence_dir.mkdir(parents=True)

    old_cwd = Path.cwd()
    # We need to patch Path("shared") to point to tmp_path/shared
    import os

    os.chdir(str(tmp_path))
    try:
        runner = CliRunner()
        result = runner.invoke(cli, ["evidence", "verify", "testcase"])
        assert result.exit_code == 0
        assert "No evidence files" in result.output
    finally:
        os.chdir(str(old_cwd))


def test_evidence_verify_with_files(tmp_path):
    evidence_dir = tmp_path / "shared" / "cases" / "testcase2" / "evidence"
    evidence_dir.mkdir(parents=True)
    f = evidence_dir / "sample.txt"
    f.write_bytes(b"hello forensic world")

    import os

    old_cwd = Path.cwd()
    os.chdir(str(tmp_path))
    try:
        runner = CliRunner()
        result = runner.invoke(cli, ["evidence", "verify", "testcase2"])
        assert result.exit_code == 0
        # Should index the file
        assert "INDEXED" in result.output or "OK" in result.output
        # Verify hash file was created
        hash_file = f.with_suffix(f.suffix + ".sha256")
        assert hash_file.exists()
    finally:
        os.chdir(str(old_cwd))


def test_evidence_verify_hash_ok(tmp_path):
    evidence_dir = tmp_path / "shared" / "cases" / "testcase3" / "evidence"
    evidence_dir.mkdir(parents=True)
    f = evidence_dir / "data.bin"
    content = b"secure evidence data"
    f.write_bytes(content)
    hash_val = hashlib.sha256(content).hexdigest()

    # Pre-create valid hash file
    hash_file = f.with_suffix(f.suffix + ".sha256")
    hash_file.write_text(f"{hash_val}  data.bin", encoding="utf-8")

    import os

    old_cwd = Path.cwd()
    os.chdir(str(tmp_path))
    try:
        runner = CliRunner()
        result = runner.invoke(cli, ["evidence", "verify", "testcase3"])
        assert result.exit_code == 0
        assert "OK" in result.output
    finally:
        os.chdir(str(old_cwd))


def test_evidence_verify_hash_mismatch(tmp_path):
    evidence_dir = tmp_path / "shared" / "cases" / "testcase4" / "evidence"
    evidence_dir.mkdir(parents=True)
    f = evidence_dir / "tampered.txt"
    f.write_bytes(b"current content")
    hash_file = f.with_suffix(f.suffix + ".sha256")
    hash_file.write_text("deadbeefdeadbeefdeadbeefdeadbeefdeadbeef  tampered.txt", encoding="utf-8")

    import os

    old_cwd = Path.cwd()
    os.chdir(str(tmp_path))
    try:
        runner = CliRunner()
        result = runner.invoke(cli, ["evidence", "verify", "testcase4"])
        assert result.exit_code == 0
        assert "MISMATCH" in result.output
    finally:
        os.chdir(str(old_cwd))


def test_purge_orphans_no_dir():
    runner = CliRunner()
    result = runner.invoke(cli, ["evidence", "purge-orphans", "nonexistent_case", "--yes"])
    assert result.exit_code == 0
    assert "No evidence" in result.output


def test_purge_orphans_none_found(tmp_path):
    evidence_dir = tmp_path / "shared" / "cases" / "testcase5" / "evidence"
    evidence_dir.mkdir(parents=True)
    # Create file without orphan hash
    (evidence_dir / "file.txt").write_text("data", encoding="utf-8")

    import os

    old_cwd = Path.cwd()
    os.chdir(str(tmp_path))
    try:
        runner = CliRunner()
        result = runner.invoke(cli, ["evidence", "purge-orphans", "testcase5", "--yes"])
        assert result.exit_code == 0
        assert "No orphaned" in result.output
    finally:
        os.chdir(str(old_cwd))


def test_purge_orphans_with_orphans(tmp_path):
    evidence_dir = tmp_path / "shared" / "cases" / "testcase6" / "evidence"
    evidence_dir.mkdir(parents=True)
    # Create orphan hash file (no corresponding content file)
    orphan_hash = evidence_dir / "missing.txt.sha256"
    orphan_hash.write_text("deadbeefdeadbeefdeadbeefdeadbeefdeadbeef  missing.txt", encoding="utf-8")

    import os

    old_cwd = Path.cwd()
    os.chdir(str(tmp_path))
    try:
        runner = CliRunner()
        result = runner.invoke(cli, ["evidence", "purge-orphans", "testcase6", "--yes"])
        assert result.exit_code == 0
        assert "Purged" in result.output
        assert not orphan_hash.exists()
    finally:
        os.chdir(str(old_cwd))
