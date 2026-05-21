import tempfile
from pathlib import Path

from forhacker.data.evidence import compute_sha256, verify_evidence


def test_compute_sha256():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        f.write(b"hello world")
        path = Path(f.name)
    try:
        h = compute_sha256(path)
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)
    finally:
        path.unlink()


def test_verify_evidence_match():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
        f.write(b"test data")
        path = Path(f.name)
    try:
        h = compute_sha256(path)
        assert verify_evidence(path, h) is True
    finally:
        path.unlink()


def test_verify_evidence_mismatch():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
        f.write(b"original")
        path = Path(f.name)
    try:
        assert verify_evidence(path, "a" * 64) is False
    finally:
        path.unlink()
