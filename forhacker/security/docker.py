import asyncio
import shutil

from forhacker.security.sandbox import Sandbox


class DockerSandbox(Sandbox):
    """Run commands inside a Docker container. Requires docker CLI on PATH."""

    def __init__(self, image: str = "ubuntu:22.04", timeout: float = 300.0):
        if not shutil.which("docker"):
            raise RuntimeError("docker CLI not found on PATH")
        self._image = image
        self._timeout = timeout

    def _build_docker_cmd(self, command: list[str], read_only_mounts: list[str] | None) -> list[str]:
        cmd = ["docker", "run", "--rm", "--network=none"]
        if read_only_mounts:
            for mount in read_only_mounts:
                cmd.extend(["-v", f"{mount}:{mount}:ro"])
        cmd.append(self._image)
        cmd.extend(command)
        return cmd

    async def run(self, command: list[str], read_only_mounts: list[str] | None = None) -> dict[str, object]:
        docker_cmd = self._build_docker_cmd(command, read_only_mounts)
        proc = await asyncio.create_subprocess_exec(
            *docker_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self._timeout)
        except TimeoutError:
            proc.kill()
            return {"exit_code": -1, "stdout": "", "stderr": f"Command timed out after {self._timeout}s"}
        return {
            "exit_code": proc.returncode or 0,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
        }
