#!/usr/bin/env python3
"""
RAM Agent Core - Ollama Cloud API
"""

import os
import re
import json
import shutil
import asyncio
import subprocess
import psutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable

from ollama import Client

OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY", "sk_4e2f36c12e409003ccf8da7c678de36ca802ed81d0cd26f3")
MODEL = os.environ.get("OLLAMA_MODEL", "gpt-oss:120b")

# ── Destructive keyword detection ─────────────────────────────────────────────
DESTRUCTIVE_PATTERNS = [
    r'\brm\s+-rf?\b', r'\brmdir\b', r'\bmkfs\b', r'\bdd\s+', r'\bshred\b',
    r'\bwipefs\b', r'\bshutdown\b', r'\breboot\b', r'\bhalt\b', r'\bpoweroff\b',
    r'\bformat\b', r'>\s*/dev/', r':.*\{.*\|.*:.*&.*\}',
]

def is_destructive(cmd: str) -> bool:
    cmd_lower = cmd.lower()
    return any(re.search(p, cmd_lower) for p in DESTRUCTIVE_PATTERNS)


# ── Terminal launcher — avoids snap/GLIBC issues ──────────────────────────────
def get_terminal_cmd(inner_cmd: str) -> str:
    """Return a command that opens inner_cmd in an available terminal"""
    # Prefer non-snap terminals
    for term in ["xterm", "lxterminal", "xfce4-terminal", "konsole", "tilix", "alacritty", "kitty"]:
        if shutil.which(term):
            if term == "xterm":
                return f'xterm -e "bash -c \\"{inner_cmd}; exec bash\\""'
            else:
                return f'{term} -- bash -c "{inner_cmd}; exec bash"'
    # gnome-terminal last (may be snap)
    if shutil.which("gnome-terminal"):
        return f'gnome-terminal -- bash -c "{inner_cmd}; exec bash"'
    # Fallback: just run in background
    return f"{inner_cmd} &"


# ── Screenshot helper ──────────────────────────────────────────────────────────
def take_screenshot() -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = str(Path.home() / f"screenshot_{ts}.png")
    for tool, cmd in [
        ("scrot",          f"scrot '{out}'"),
        ("import",         f"import -window root '{out}'"),   # imagemagick
        ("gnome-screenshot", f"gnome-screenshot -f '{out}'"),
        ("flameshot",      f"flameshot full -p '{out}'"),
        ("spectacle",      f"spectacle -b -f -o '{out}'"),
    ]:
        if shutil.which(tool):
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            if r.returncode == 0 and Path(out).exists():
                return f"Screenshot saved: {out}"
            # try next tool
    return (
        "No screenshot tool found, Boss. Install one:\n"
        "  sudo apt install scrot          # lightweight\n"
        "  sudo apt install imagemagick    # import command\n"
        "  sudo apt install flameshot      # modern GUI tool"
    )


# ── Webcam helper ──────────────────────────────────────────────────────────────
def take_photo() -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = str(Path.home() / f"photo_{ts}.jpg")
    for tool, cmd in [
        ("fswebcam", f"fswebcam -r 1280x720 --no-banner '{out}'"),
        ("ffmpeg",   f"ffmpeg -y -f v4l2 -i /dev/video0 -vframes 1 '{out}'"),
    ]:
        if shutil.which(tool):
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
            if r.returncode == 0 and Path(out).exists():
                return f"Photo saved: {out}"
    return (
        "No webcam tool found, Boss. Install one:\n"
        "  sudo apt install fswebcam\n"
        "  sudo apt install ffmpeg"
    )


SYSTEM_PROMPT = """You are RAM, an intelligent Ubuntu OS agent running on the user's machine.

Personality:
- Address the user as "Boss"
- Sharp, efficient, concise — hacker/tech aesthetic
- Always confirm before destructive operations (shutdown, reboot, delete, format, etc.)

When you need to run a shell command, output ONLY this JSON (no markdown, no backticks):
{"action": "shell", "command": "bash command here", "destructive": false}

For destructive commands (shutdown, reboot, rm -rf, etc.) set "destructive": true.

For system info:
{"action": "sysinfo", "type": "cpu|ram|disk|network|processes|uptime|battery|all"}

For screenshots: {"action": "screenshot"}
For webcam photo: {"action": "photo"}

For opening a terminal with a command:
{"action": "terminal", "command": "the command to run in new terminal"}

For regular text replies, just respond normally. No markdown code fences around JSON.
Mix plain text with action JSON as needed. One JSON block per response max."""


class RAMAgent:
    def __init__(self, output_callback: Optional[Callable] = None):
        self.output_callback = output_callback
        self.conversation_history = []
        self.client = Client(
            host="https://ollama.com",
            headers={"Authorization": "Bearer " + OLLAMA_API_KEY}
        )

    async def chat(self, user_message: str) -> str:
        self.conversation_history.append({"role": "user", "content": user_message})
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + self.conversation_history

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat(MODEL, messages=messages, stream=False)
            )
            assistant_message = response['message']['content']
        except Exception as e:
            assistant_message = f"[Connection error: {e}]\n\nBoss, I can't reach Ollama. Check API key / internet."

        self.conversation_history.append({"role": "assistant", "content": assistant_message})
        return await self.process_response(assistant_message)

    async def process_response(self, text: str) -> str:
        # Strip any markdown fences the model might wrap around JSON
        text = re.sub(r'```(?:json|bash|shell)?\s*', '', text)
        text = re.sub(r'```', '', text)

        # Find JSON action blocks
        json_pattern = r'\{[^{}]*"action"[^{}]*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)

        result_text = text
        for match in matches:
            try:
                action = json.loads(match)
                atype = action.get("action")
                replacement = ""

                if atype == "shell":
                    cmd = action.get("command", "")
                    destructive = action.get("destructive", False) or is_destructive(cmd)
                    if destructive:
                        replacement = (
                            f"[CONFIRMATION REQUIRED] Destructive command: {cmd}\n"
                            f"Type 'confirm' to execute."
                        )
                    else:
                        out = await self._run_shell(cmd)
                        replacement = f"[CMD: {cmd}]\n{out}"

                elif atype == "terminal":
                    cmd = action.get("command", "")
                    term_cmd = get_terminal_cmd(cmd)
                    out = await self._run_shell(term_cmd)
                    replacement = f"[TERMINAL: {cmd}]\n{out}"

                elif atype == "sysinfo":
                    replacement = await self.get_sysinfo(action.get("type", "all"))

                elif atype == "screenshot":
                    loop = asyncio.get_event_loop()
                    replacement = await loop.run_in_executor(None, take_screenshot)

                elif atype == "photo":
                    loop = asyncio.get_event_loop()
                    replacement = await loop.run_in_executor(None, take_photo)

                elif atype == "file":
                    replacement = await self.handle_file(action)

                result_text = result_text.replace(match, replacement)

            except json.JSONDecodeError:
                pass

        return result_text.strip()

    async def _run_shell(self, command: str) -> str:
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True,
                text=True, timeout=30, cwd=str(Path.home()),
                env={**os.environ, "DISPLAY": os.environ.get("DISPLAY", ":0")}
            )
            out = (result.stdout + result.stderr).strip()
            return out if out else "(done, no output)"
        except subprocess.TimeoutExpired:
            return "[Timeout after 30s]"
        except Exception as e:
            return f"[Error: {e}]"

    async def get_sysinfo(self, info_type: str = "all") -> str:
        lines = []
        if info_type in ("cpu", "all"):
            lines.append(f"CPU: {psutil.cpu_percent(interval=0.5)}% ({psutil.cpu_count()} cores)")
        if info_type in ("ram", "all"):
            ram = psutil.virtual_memory()
            lines.append(f"RAM: {ram.percent}% used  ({ram.used//1024**2}MB / {ram.total//1024**2}MB)")
        if info_type in ("disk", "all"):
            d = psutil.disk_usage('/')
            lines.append(f"Disk: {d.percent}% used  ({d.used//1024**3}GB / {d.total//1024**3}GB)")
        if info_type in ("network", "all"):
            try:
                r = subprocess.run(["ping","-c","1","-W","2","8.8.8.8"],
                                   capture_output=True, text=True, timeout=5)
                lines.append(f"Network: {'Online ✓' if r.returncode==0 else 'OFFLINE ✗'}")
            except Exception:
                lines.append("Network: unknown")
        if info_type in ("processes", "all"):
            lines.append(f"Processes: {len(list(psutil.process_iter()))} running")
        if info_type in ("uptime", "all"):
            s = int(datetime.now().timestamp() - psutil.boot_time())
            h, m = divmod(s // 60, 60)
            lines.append(f"Uptime: {h}h {m}m")
        if info_type in ("battery", "all"):
            b = psutil.sensors_battery()
            if b:
                lines.append(f"Battery: {b.percent:.0f}%  ({'charging' if b.power_plugged else 'discharging'})")
            else:
                lines.append("Battery: N/A")
        if info_type in ("temperature", "all"):
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    for name, entries in temps.items():
                        if entries:
                            lines.append(f"Temp ({name}): {entries[0].current}°C")
                            break
            except Exception:
                pass
        return "\n".join(lines) if lines else "No data available"

    async def handle_file(self, action: dict) -> str:
        op = action.get("operation")
        path = Path(action.get("path", "")).expanduser()
        if op == "read":
            try:
                return path.read_text(errors="replace")[:2000]
            except Exception as e:
                return f"[Error reading: {e}]"
        elif op == "list":
            try:
                return "\n".join(str(i) for i in list(path.iterdir())[:50])
            except Exception as e:
                return f"[Error listing: {e}]"
        elif op == "write":
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(action.get("content", ""))
                return f"[Written: {path}]"
            except Exception as e:
                return f"[Error writing: {e}]"
        elif op == "delete":
            return f"[CONFIRMATION REQUIRED] Destructive command: rm '{path}'\nType 'confirm' to execute."
        return "[Unknown file operation]"

    def clear_history(self):
        self.conversation_history.clear()

    async def close(self):
        pass
