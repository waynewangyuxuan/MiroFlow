# SPDX-FileCopyrightText: 2025 MiromindAI
#
# SPDX-License-Identifier: Apache-2.0

"""
Code execution MCP server.

Supports two backends (set via SANDBOX_BACKEND env var):
  - "docker"  : Local Docker containers (default, no cloud dependency)
  - "e2b"     : E2B cloud sandbox (requires E2B_API_KEY)

All 6 MCP tools have identical signatures regardless of backend.
"""

import asyncio
import os

from fastmcp import FastMCP

from src.logging.logger import setup_mcp_logging

setup_mcp_logging(tool_name=os.path.basename(__file__))
mcp = FastMCP("code-interpreter")

# ── Configuration ────────────────────────────────────────────────────────────

SANDBOX_BACKEND = os.environ.get("SANDBOX_BACKEND", "docker")
LOGS_DIR = os.environ.get("LOGS_DIR", "./logs")
DEFAULT_TIMEOUT = int(os.environ.get("DEFAULT_TIMEOUT", "1800"))

# Docker backend config
SANDBOX_IMAGE = os.environ.get("SANDBOX_IMAGE", "miroflow-sandbox")
SANDBOX_NETWORK = os.environ.get("SANDBOX_NETWORK", "true").lower() == "true"

# E2B backend config (only needed when SANDBOX_BACKEND=e2b)
E2B_API_KEY = os.environ.get("E2B_API_KEY")
DEFAULT_TEMPLATE_ID = os.environ.get("DEFAULT_TEMPLATE_ID", "all_pip_apt_pkg")


# ── Backend abstraction ──────────────────────────────────────────────────────


def _create_sandbox() -> str:
    """Create a new sandbox using the configured backend. Returns sandbox_id."""
    if SANDBOX_BACKEND == "docker":
        from sandbox.docker_sandbox import DockerSandbox

        sandbox = DockerSandbox.create(
            image=SANDBOX_IMAGE,
            timeout=DEFAULT_TIMEOUT,
            network_enabled=SANDBOX_NETWORK,
        )
        return sandbox.sandbox_id
    else:
        from e2b_code_interpreter import Sandbox

        sandbox = Sandbox(
            template=DEFAULT_TEMPLATE_ID,
            timeout=DEFAULT_TIMEOUT,
            api_key=E2B_API_KEY,
        )
        sandbox.set_timeout(DEFAULT_TIMEOUT)
        return sandbox.get_info().sandbox_id


def _connect(sandbox_id: str):
    """Connect to an existing sandbox. Returns a backend-specific handle."""
    if SANDBOX_BACKEND == "docker":
        from sandbox.docker_sandbox import DockerSandbox

        return DockerSandbox.connect(sandbox_id)
    else:
        from e2b_code_interpreter import Sandbox

        return Sandbox.connect(sandbox_id, api_key=E2B_API_KEY)


def _run_command(handle, command: str) -> str:
    """Run a shell command. Returns stringified result."""
    if SANDBOX_BACKEND == "docker":
        return str(handle.run_command(command))
    else:
        handle.set_timeout(DEFAULT_TIMEOUT)
        return str(handle.commands.run(command))


def _run_code(handle, code: str) -> str:
    """Run Python code. Returns stringified result."""
    if SANDBOX_BACKEND == "docker":
        return str(handle.run_code(code))
    else:
        handle.set_timeout(DEFAULT_TIMEOUT)
        return str(handle.run_code(code))


def _upload_file(handle, local_path: str, sandbox_dir: str) -> str:
    """Upload a local file into the sandbox. Returns the sandbox path."""
    dest = os.path.join(sandbox_dir, os.path.basename(local_path))
    if SANDBOX_BACKEND == "docker":
        handle.upload_file(local_path, dest)
    else:
        handle.set_timeout(DEFAULT_TIMEOUT)
        with open(local_path, "rb") as f:
            handle.files.write(dest, f)
    return dest


def _download_file(handle, sandbox_path: str) -> bytes:
    """Download a file from the sandbox. Returns raw bytes."""
    if SANDBOX_BACKEND == "docker":
        return handle.download_file(sandbox_path)
    else:
        handle.set_timeout(DEFAULT_TIMEOUT)
        return handle.files.read(sandbox_path, format="bytes")


def _download_via_wget(handle, url: str, sandbox_dir: str) -> str:
    """Download a URL inside the sandbox via wget. Returns dest path or empty string."""
    dest = os.path.join(sandbox_dir, os.path.basename(url))
    cmd = f"wget -q '{url}' -O '{dest}'"
    if SANDBOX_BACKEND == "docker":
        result = handle.run_command(cmd)
        return dest if result.exit_code == 0 else ""
    else:
        handle.set_timeout(DEFAULT_TIMEOUT)
        result = handle.commands.run(cmd)
        return dest if result.exit_code == 0 else ""


# ── MCP Tools ────────────────────────────────────────────────────────────────


@mcp.tool()
async def create_sandbox() -> str:
    """Create a linux sandbox and get the `sandbox_id` for safely executing
    commands and running python code.

    The sandbox may timeout and automatically shutdown. If so, you will need
    to create a new sandbox.

    IMPORTANT: Do not execute `create_sandbox` and other sandbox tools in the
    same message. You must wait for `create_sandbox` to return the `sandbox_id`,
    then use that `sandbox_id` in subsequent messages.

    Returns:
        The `sandbox_id` of the newly created sandbox.
    """
    max_retries = 5
    for attempt in range(1, max_retries + 1):
        try:
            sandbox_id = _create_sandbox()
            os.makedirs(os.path.join(LOGS_DIR, "tmpfiles"), exist_ok=True)
            return f"Sandbox created with sandbox_id: {sandbox_id}"
        except Exception as e:
            if attempt == max_retries:
                return (
                    f"Failed to create sandbox after {max_retries} attempts: {e}, "
                    "please retry later."
                )
            await asyncio.sleep(attempt * 2)


@mcp.tool()
async def run_command(sandbox_id: str, command: str) -> str:
    """Execute a shell command in the linux sandbox.
    The sandbox is already installed with common system packages for the task.

    Args:
        sandbox_id: The id of the existing sandbox (from `create_sandbox`).
        command: The shell command to execute.

    Returns:
        Result of the command execution (stderr, stdout, exit_code, error).
    """
    try:
        handle = _connect(sandbox_id)
    except Exception:
        return (
            f"[ERROR]: Failed to connect to sandbox {sandbox_id}, retry later. "
            "Make sure the sandbox is created and the id is correct."
        )

    max_retries = 5
    for attempt in range(1, max_retries + 1):
        try:
            result_str = _run_command(handle, command)

            if "pip install" in command or "apt-get" in command:
                result_str += (
                    "\n\n[PACKAGE INSTALL STATUS]: The system packages and Python "
                    "packages required for the task have been installed. No need to "
                    "install them again unless a missing package error occurs."
                )
            return result_str

        except Exception as e:
            if attempt == max_retries:
                error_msg = (
                    f"[ERROR]: Failed to run command after {max_retries} attempts. "
                    f"Exception type: {type(e).__name__}, Details: {e}.\n\n"
                    "[HINT]: Shell commands can be error-prone. Consider using the "
                    "`run_python_code` tool instead.\n\n"
                    "[PERMISSION HINT]: You are running as user, not root. Use "
                    "`sudo` for commands requiring admin privileges."
                )
                if "pip install" in command or "apt-get" in command:
                    error_msg += (
                        "\n\n[PACKAGE INSTALL STATUS]: Packages may already be "
                        "installed. Only re-install if a missing package error occurs."
                    )
                return error_msg
            await asyncio.sleep(attempt * 2)


@mcp.tool()
async def run_python_code(sandbox_id: str, code_block: str) -> str:
    """Run python code in the sandbox and return the execution result.
    The sandbox is already installed with common python packages for the task.

    Args:
        sandbox_id: The id of the existing sandbox (from `create_sandbox`).
        code_block: The python code to run.

    Returns:
        Result of the code execution (stderr, stdout, exit_code, error).
    """
    try:
        handle = _connect(sandbox_id)
    except Exception:
        return (
            f"[ERROR]: Failed to connect to sandbox {sandbox_id}, retry later. "
            "Make sure the sandbox is created and the id is correct."
        )

    max_retries = 5
    for attempt in range(1, max_retries + 1):
        try:
            return _run_code(handle, code_block)
        except Exception as e:
            if attempt == max_retries:
                return (
                    f"[ERROR]: Failed to run code in sandbox {sandbox_id} after "
                    f"{max_retries} attempts. Exception type: {type(e).__name__}, "
                    f"Details: {e}."
                )
            await asyncio.sleep(attempt * 2)


@mcp.tool()
async def upload_file_from_local_to_sandbox(
    sandbox_id: str, local_file_path: str, sandbox_file_path: str = "/home/sandbox"
) -> str:
    """Upload a local file to the sandbox.

    Args:
        sandbox_id: The id of the existing sandbox (from `create_sandbox`).
        local_file_path: The local path of the file to upload.
        sandbox_file_path: Destination directory in the sandbox.
            Default is `/home/sandbox/`.

    Returns:
        The path of the uploaded file in the sandbox.
    """
    try:
        handle = _connect(sandbox_id)
    except Exception:
        return (
            f"[ERROR]: Failed to connect to sandbox {sandbox_id}, retry later. "
            "Make sure the sandbox is created and the id is correct."
        )

    try:
        dest = _upload_file(handle, local_file_path, sandbox_file_path)
        return (
            f"File uploaded to {dest}\n\n"
            "[INFO]: For directly reading local files without uploading to sandbox, "
            "consider using the `read_file` tool which can read various file types "
            "directly from local paths or URLs."
        )
    except Exception as e:
        return (
            f"[ERROR]: Failed to upload file {local_file_path} to sandbox "
            f"{sandbox_id}: {e}\n\n"
            "[INFO]: Consider using the `read_file` tool which can directly read "
            "various file types from local paths or URLs without uploading."
        )


@mcp.tool()
async def download_file_from_internet_to_sandbox(
    sandbox_id: str, url: str, sandbox_file_path: str = "/home/sandbox"
) -> str:
    """Download a file from the internet into the sandbox.

    Args:
        sandbox_id: The id of the existing sandbox (from `create_sandbox`).
        url: The URL of the file to download.
        sandbox_file_path: Destination directory in the sandbox.
            Default is `/home/sandbox/`.

    Returns:
        The path of the downloaded file in the sandbox.
    """
    try:
        handle = _connect(sandbox_id)
    except Exception:
        return (
            f"[ERROR]: Failed to connect to sandbox {sandbox_id}, retry later. "
            "Make sure the sandbox is created and the id is correct."
        )

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            dest = _download_via_wget(handle, url, sandbox_file_path)
            if dest:
                return (
                    f"File downloaded to {dest}\n\n"
                    "[INFO]: For directly reading files from URLs without downloading "
                    "to sandbox, consider using the `read_file` tool."
                )
            if attempt < max_retries:
                await asyncio.sleep(4**attempt)
                continue
            return (
                f"[ERROR]: Failed to download file from {url} after "
                f"{max_retries} attempts.\n\n"
                "[INFO]: To upload local files, use `upload_file_from_local_to_sandbox`."
            )
        except Exception as e:
            if attempt == max_retries:
                return f"[ERROR]: Failed to download file from {url}: {e}"
            await asyncio.sleep(4**attempt)


@mcp.tool()
async def download_file_from_sandbox_to_local(
    sandbox_id: str, sandbox_file_path: str, local_filename: str = None
) -> str:
    """Download a file from the sandbox to the local system.

    Files in sandbox cannot be processed by tools from other servers — only
    local files and internet URLs can be processed by them.

    Args:
        sandbox_id: The id of the sandbox (from `create_sandbox`).
        sandbox_file_path: Path of the file inside the sandbox.
        local_filename: Optional filename to save as.

    Returns:
        The local path of the downloaded file.
    """
    try:
        handle = _connect(sandbox_id)
    except Exception:
        return (
            f"[ERROR]: Failed to connect to sandbox {sandbox_id}, retry later. "
            "Make sure the sandbox is created and the id is correct."
        )

    try:
        if not LOGS_DIR:
            return "[ERROR]: LOGS_DIR environment variable is not set."

        tmpfiles_dir = os.path.join(LOGS_DIR, "tmpfiles")
        os.makedirs(tmpfiles_dir, exist_ok=True)

        if not local_filename or not local_filename.strip():
            local_filename = os.path.basename(sandbox_file_path)

        local_path = os.path.join(
            tmpfiles_dir, f"sandbox_{sandbox_id}_{local_filename}"
        )

        content = _download_file(handle, sandbox_file_path)
        with open(local_path, "wb") as f:
            f.write(content)

        return (
            f"File downloaded successfully to: {local_path}\n\n"
            "[INFO]: The file can now be accessed by other tools which only "
            "support local files and internet URLs, not sandbox files."
        )
    except Exception as e:
        return (
            f"[ERROR]: Failed to download file {sandbox_file_path} from "
            f"sandbox {sandbox_id}: {e}\n\n"
            "[INFO]: To upload local files to the sandbox, use "
            "`upload_file_from_local_to_sandbox` instead."
        )


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
