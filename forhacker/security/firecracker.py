from __future__ import annotations

"""Firecracker microVM sandbox — Linux-only, requires KVM.

Firecracker provides stronger isolation than Docker by running each workload
in a lightweight virtual machine with its own kernel. This is appropriate for
HIGH/CRITICAL risk tasks (malware analysis, exploit testing).

Requirements:
    - Linux host with KVM enabled (/dev/kvm)
    - firecracker binary on PATH
    - Root or appropriate permissions for /dev/kvm access

On Windows and macOS, this backend is unavailable — the IsolationRouter will
block HIGH-risk tasks when no Firecracker backend is registered.
"""

from forhacker.security.sandbox import Sandbox


class FirecrackerSandbox(Sandbox):
    """Firecracker microVM sandbox. Requires Linux + KVM + firecracker binary."""

    def __init__(self, kernel_path: str = "", rootfs_path: str = "", timeout: float = 600.0):
        import platform

        if platform.system() != "Linux":
            raise RuntimeError(
                f"FirecrackerSandbox requires Linux with KVM. "
                f"Current platform: {platform.system()}. "
                f"Use DockerSandbox for non-Linux environments."
            )
        import shutil

        if not shutil.which("firecracker"):
            raise RuntimeError("firecracker binary not found on PATH")
        if not kernel_path or not rootfs_path:
            raise RuntimeError("kernel_path and rootfs_path are required for Firecracker VM")
        self._kernel = kernel_path
        self._rootfs = rootfs_path
        self._timeout = timeout

    async def run(self, command: list[str], read_only_mounts: list[str] | None = None) -> dict[str, object]:
        """Run a command inside a Firecracker microVM.

        Note: Full Firecracker VM lifecycle (start VM, configure vsock, exec command,
        capture output, stop VM) requires integration with the Firecracker API socket.
        This stub documents the interface; full implementation deferred.
        """
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": (
                "FirecrackerSandbox full implementation deferred. "
                "Requires: Linux + KVM + firecracker + VM lifecycle management. "
                "Use DockerSandbox for current environments."
            ),
        }
