import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def tmp_shared_dir():
    """Temporary shared/ directory mimicking Syncthing-synced state."""
    with tempfile.TemporaryDirectory() as td:
        shared = Path(td)
        (shared / "cases").mkdir()
        (shared / "agents").mkdir()
        yield shared
