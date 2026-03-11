#!/usr/bin/env python3
"""
RAM Tool: Shell Commands
Run arbitrary bash commands on the Ubuntu machine.
"""

import subprocess
import shlex
from pathlib import Path
from typing import Optional


DESTRUCTIVE_KEYWORDS = [
    "rm ", "rmdir", "mkfs", "dd ", "shred", "wipefs",
    "chmod 000", "chown root", "> /dev/", "format",
    ":(){:|:&};:", "shutdown", "reboot", "halt", "poweroff"
]


def is_destructive(command: str) -> bool:
    cmd_lower = command.lower()
    return any(kw in cmd_lower for kw in DESTRUCTIVE_KEYWORDS)


def run_command(
    command: str,
    cwd: Optional[str] = None,
    timeout: int = 30,
    force: bool = False
) -> dict:
    """
    Execute a shell command.
    
    Args:
        command: Bash command string
        cwd: Working directory (default: home)
        timeout: Timeout in seconds
        force: Skip destructive check
    
    Returns:
        dict with keys: success, stdout, stderr, returncode, command
    """
    if not force and is_destructive(command):
        return {
            "success": False,
            "stdout": "",
            "stderr": "",
            "returncode": -1,
            "command": command,
            "requires_confirmation": True,
            "message": f"Destructive command detected. Set force=True to confirm: {command}"
        }

    working_dir = cwd or str(Path.home())

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=working_dir,
            env={**__import__("os").environ, "TERM": "xterm-256color"}
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode,
            "command": command,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Command timed out after {timeout}s",
            "returncode": -1,
            "command": command,
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1,
            "command": command,
        }


def run_interactive(command: str):
    """Run a command and stream output line by line"""
    import subprocess
    proc = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    for line in proc.stdout:
        yield line.rstrip()
    proc.wait()


if __name__ == "__main__":
    # Test
    result = run_command("echo 'RAM Shell Tool Online'; uname -a")
    print(result["stdout"])
