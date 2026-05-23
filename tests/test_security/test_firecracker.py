from __future__ import annotations

import platform

from forhacker.security.firecracker import FirecrackerSandbox


def test_firecracker_raises_on_windows():
    if platform.system() != "Linux":
        try:
            FirecrackerSandbox(kernel_path="/tmp/vmlinux", rootfs_path="/tmp/rootfs.ext4")
            assert False, "Should have raised RuntimeError"
        except RuntimeError as e:
            assert "Linux" in str(e) or "KVM" in str(e)
