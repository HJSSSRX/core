import hashlib
from pathlib import Path


def compute_sha256(path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha.update(chunk)
    return sha.hexdigest()


def verify_evidence(path: Path, expected_sha256: str) -> bool:
    """Verify file integrity against expected hash. Returns True if match."""
    actual = compute_sha256(path)
    return actual == expected_sha256
