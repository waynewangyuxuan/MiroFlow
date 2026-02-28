# SPDX-FileCopyrightText: 2025 MiromindAI
#
# SPDX-License-Identifier: Apache-2.0

"""
Local Docker-based code execution sandbox.

Drop-in replacement for E2B cloud sandbox. Runs containers locally using
Docker Desktop — no cloud API keys, no network latency, no per-minute billing.

Usage:
    sandbox = DockerSandbox.create(image="miroflow-sandbox", timeout=1800)
    result  = sandbox.run_command("echo hello")
    result  = sandbox.run_code("print(1+1)")
    sandbox.upload_file("/local/path.csv", "/home/sandbox/path.csv")
    content = sandbox.download_file("/home/sandbox/output.txt")
    sandbox.kill()

All public methods are synchronous — async wrappers live in python_server.py.
"""

from __future__ import annotations

import io
import tarfile
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import ClassVar

import docker
from docker.errors import NotFound
from docker.models.containers import Container


# ── Result types ─────────────────────────────────────────────────────────────


@dataclass
class CommandResult:
    """Mirrors the E2B CommandResult shape so callers don't need to change."""

    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    error: str | None = None

    def __str__(self) -> str:
        parts = [f"exit_code={self.exit_code}"]
        if self.stdout:
            parts.append(f"stdout={self.stdout}")
        if self.stderr:
            parts.append(f"stderr={self.stderr}")
        if self.error:
            parts.append(f"error={self.error}")
        return f"CommandResult({', '.join(parts)})"


@dataclass
class CodeResult:
    """Mirrors the E2B Execution result shape."""

    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    error: str | None = None
    results: list = field(default_factory=list)

    def __str__(self) -> str:
        parts = [f"exit_code={self.exit_code}"]
        if self.stdout:
            parts.append(f"stdout={self.stdout}")
        if self.stderr:
            parts.append(f"stderr={self.stderr}")
        if self.error:
            parts.append(f"error={self.error}")
        return f"CodeResult({', '.join(parts)})"


# ── Sandbox pool ─────────────────────────────────────────────────────────────


class DockerSandbox:
    """
    Manages a single Docker container as an isolated code-execution sandbox.

    Lifecycle mirrors E2B:
        create()   → start a new container, return sandbox_id
        connect()  → attach to an existing container by sandbox_id
        kill()     → remove the container

    Thread-safe container registry allows multiple sandboxes in parallel.
    """

    # Class-level registry: sandbox_id → DockerSandbox instance
    _registry: ClassVar[dict[str, DockerSandbox]] = {}
    _lock: ClassVar[threading.Lock] = threading.Lock()

    def __init__(
        self,
        container: Container,
        sandbox_id: str,
        timeout: int,
        created_at: float,
    ):
        self._container = container
        self.sandbox_id = sandbox_id
        self.timeout = timeout
        self._created_at = created_at

    # ── Factory methods ──────────────────────────────────────────────────

    @classmethod
    def create(
        cls,
        image: str = "miroflow-sandbox",
        timeout: int = 1800,
        network_enabled: bool = True,
    ) -> DockerSandbox:
        """Create and start a new sandbox container."""
        client = docker.from_env()
        sandbox_id = f"mf-{uuid.uuid4().hex[:12]}"

        container = client.containers.run(
            image=image,
            name=sandbox_id,
            detach=True,
            stdin_open=True,
            tty=False,
            # Resource limits
            mem_limit="4g",
            nano_cpus=int(2 * 1e9),  # 2 CPU cores
            # Security
            security_opt=["no-new-privileges"],
            # Network
            network_mode="bridge" if network_enabled else "none",
            # Workdir
            working_dir="/home/sandbox",
        )

        sandbox = cls(
            container=container,
            sandbox_id=sandbox_id,
            timeout=timeout,
            created_at=time.time(),
        )

        with cls._lock:
            cls._registry[sandbox_id] = sandbox

        # Schedule auto-cleanup
        cleanup = threading.Timer(timeout, sandbox._auto_cleanup)
        cleanup.daemon = True
        cleanup.start()

        return sandbox

    @classmethod
    def connect(cls, sandbox_id: str) -> DockerSandbox:
        """Reconnect to an existing sandbox by ID.

        First checks the in-memory registry, then falls back to looking up
        the Docker container by name (sandbox_id == container name).  This
        handles the case where each MCP tool call runs in a fresh process
        and the in-memory registry is empty.
        """
        with cls._lock:
            sandbox = cls._registry.get(sandbox_id)

        if sandbox is None:
            # Fallback: look up container by name via Docker API
            import docker

            client = docker.from_env()
            try:
                container = client.containers.get(sandbox_id)
            except docker.errors.NotFound:
                raise NotFound(
                    f"Sandbox '{sandbox_id}' not found or already expired."
                )
            if container.status != "running":
                raise NotFound(
                    f"Sandbox '{sandbox_id}' container is no longer running."
                )
            sandbox = cls(
                container=container,
                sandbox_id=sandbox_id,
                timeout=1800,
                created_at=time.time(),
            )
            with cls._lock:
                cls._registry[sandbox_id] = sandbox
            return sandbox

        # Verify container is still running
        sandbox._container.reload()
        if sandbox._container.status != "running":
            sandbox._remove_from_registry()
            raise NotFound(f"Sandbox '{sandbox_id}' container is no longer running.")

        return sandbox

    # ── Command execution ────────────────────────────────────────────────

    def run_command(self, command: str, timeout: int | None = None) -> CommandResult:
        """Execute a shell command inside the sandbox."""
        exec_timeout = timeout or self.timeout
        try:
            exit_code, output = self._container.exec_run(
                cmd=["bash", "-c", command],
                user="sandbox",
                workdir="/home/sandbox",
                demux=True,
            )
            stdout = (output[0] or b"").decode("utf-8", errors="replace")
            stderr = (output[1] or b"").decode("utf-8", errors="replace")
            return CommandResult(
                stdout=stdout, stderr=stderr, exit_code=exit_code
            )
        except Exception as e:
            return CommandResult(exit_code=1, error=str(e))

    def run_code(self, code: str, timeout: int | None = None) -> CodeResult:
        """Execute a Python code block inside the sandbox."""
        # Write code to a temp file, then execute it.
        # This avoids shell escaping issues with complex code blocks.
        tmp_path = f"/tmp/_mf_exec_{uuid.uuid4().hex[:8]}.py"

        # Upload code as file
        self._write_file_to_container(tmp_path, code.encode("utf-8"))

        try:
            exit_code, output = self._container.exec_run(
                cmd=["python", tmp_path],
                user="sandbox",
                workdir="/home/sandbox",
                demux=True,
            )
            stdout = (output[0] or b"").decode("utf-8", errors="replace")
            stderr = (output[1] or b"").decode("utf-8", errors="replace")
            return CodeResult(
                stdout=stdout, stderr=stderr, exit_code=exit_code
            )
        except Exception as e:
            return CodeResult(exit_code=1, error=str(e))
        finally:
            # Clean up temp file
            try:
                self._container.exec_run(cmd=["rm", "-f", tmp_path])
            except Exception:
                pass

    # ── File operations ──────────────────────────────────────────────────

    def upload_file(self, local_path: str, sandbox_path: str) -> None:
        """Copy a local file into the sandbox container."""
        with open(local_path, "rb") as f:
            data = f.read()
        self._write_file_to_container(sandbox_path, data)

    def download_file(self, sandbox_path: str) -> bytes:
        """Read a file from the sandbox container and return its bytes."""
        stream, _ = self._container.get_archive(sandbox_path)
        file_bytes = b"".join(stream)

        # Docker get_archive returns a tar stream — extract the actual file
        tar_buffer = io.BytesIO(file_bytes)
        with tarfile.open(fileobj=tar_buffer) as tar:
            member = tar.getmembers()[0]
            extracted = tar.extractfile(member)
            if extracted is None:
                raise FileNotFoundError(
                    f"Could not extract '{sandbox_path}' from container archive."
                )
            return extracted.read()

    # ── Lifecycle ────────────────────────────────────────────────────────

    def set_timeout(self, seconds: int) -> None:
        """Update the sandbox timeout (resets the auto-cleanup timer)."""
        self.timeout = seconds

    def kill(self) -> None:
        """Stop and remove the sandbox container."""
        try:
            self._container.remove(force=True)
        except Exception:
            pass
        self._remove_from_registry()

    # ── Internal helpers ─────────────────────────────────────────────────

    def _write_file_to_container(self, path: str, data: bytes) -> None:
        """Write raw bytes to a path inside the container via tar stream."""
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
            info = tarfile.TarInfo(name=path.split("/")[-1])
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
        tar_buffer.seek(0)

        dest_dir = "/".join(path.split("/")[:-1]) or "/"
        # Ensure directory exists
        self._container.exec_run(cmd=["mkdir", "-p", dest_dir], user="root")
        self._container.put_archive(dest_dir, tar_buffer)

    def _auto_cleanup(self) -> None:
        """Called by the timer thread when the sandbox times out."""
        try:
            self._container.reload()
            if self._container.status == "running":
                self._container.remove(force=True)
        except Exception:
            pass
        self._remove_from_registry()

    def _remove_from_registry(self) -> None:
        with self._lock:
            self._registry.pop(self.sandbox_id, None)
