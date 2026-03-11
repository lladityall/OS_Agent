#!/usr/bin/env python3
"""
RAM Terminal UI - Dark hacker aesthetic
"""

import os
import sys
import asyncio
import threading
import time
from pathlib import Path

class Colors:
    RESET        = "\033[0m"
    BOLD         = "\033[1m"
    GREEN        = "\033[92m"
    DARK_GREEN   = "\033[32m"
    BRIGHT_GREEN = "\033[92m"
    CYAN         = "\033[96m"
    DARK_CYAN    = "\033[36m"
    WHITE        = "\033[97m"
    GRAY         = "\033[90m"
    YELLOW       = "\033[93m"
    RED          = "\033[91m"

C = Colors

RAM_ASCII = r"""
██████╗  █████╗ ███╗   ███╗
██╔══██╗██╔══██╗████╗ ████║
██████╔╝███████║██╔████╔██║
██╔══██╗██╔══██║██║╚██╔╝██║
██║  ██║██║  ██║██║ ╚═╝ ██║
╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝"""

SEPARATOR = "─" * 80
THIN_SEP  = "·" * 80


def clear_screen():
    os.system("clear")


def get_terminal_width():
    try:
        return os.get_terminal_size().columns
    except Exception:
        return 80


def print_header(width=80):
    print(f"{C.DARK_GREEN}{SEPARATOR}{C.RESET}")
    for line in RAM_ASCII.strip("\n").split("\n"):
        pad = max(0, (width - len(line)) // 2)
        print(f"{C.BRIGHT_GREEN}{' ' * pad}{line}{C.RESET}")
    print()
    subtitle = "Ubuntu OS Agent  •  v1.0  •  Online"
    pad = max(0, (width - len(subtitle)) // 2)
    print(f"{C.GRAY}{' ' * pad}{subtitle}{C.RESET}")
    print(f"{C.DARK_GREEN}{SEPARATOR}{C.RESET}")

    try:
        import datetime, platform, psutil
        now = datetime.datetime.now().strftime("%b %d  %I:%M %p")
        cpu = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory().percent
        uname = platform.node()
        status = f"  {now}   CPU {cpu}%   RAM {ram}%   Host: {uname}"
        print(f"{C.DARK_CYAN}{status}{C.RESET}")
    except Exception:
        pass
    print(f"{C.DARK_GREEN}{THIN_SEP}{C.RESET}\n")


def print_connection_msg():
    print(f"{C.GRAY}Connected to RAM Terminal.{C.RESET}\n")


def print_user_prompt():
    sys.stdout.write(f"\n{C.GREEN}You:{C.RESET} ")
    sys.stdout.flush()


def clean_response(text: str) -> str:
    """Remove ```json, ```, and other markdown artifacts from shell output"""
    import re
    # Remove ```json ... ``` and ``` ... ``` wrappers
    text = re.sub(r'```(?:json|bash|shell)?\s*\n?', '', text)
    text = re.sub(r'```', '', text)
    return text.strip()


def print_ram_response(text: str):
    text = clean_response(text)
    print(f"\n{C.BRIGHT_GREEN}RAM:{C.RESET}")
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("[CMD:"):
            print(f"  {C.YELLOW}{line}{C.RESET}")
        elif stripped.startswith("[CONFIRMATION REQUIRED]") or stripped.startswith("[Error"):
            print(f"  {C.RED}{line}{C.RESET}")
        elif stripped.startswith("CPU:") or stripped.startswith("RAM:") or \
             stripped.startswith("Disk:") or stripped.startswith("Network:") or \
             stripped.startswith("Battery:") or stripped.startswith("Uptime:") or \
             stripped.startswith("Processes:") or stripped.startswith("Temp"):
            print(f"  {C.CYAN}{line}{C.RESET}")
        else:
            print(f"  {C.WHITE}{line}{C.RESET}")


def animate_thinking(stop_event: threading.Event):
    frames = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
    i = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\r  {C.DARK_GREEN}{frames[i % len(frames)]} RAM is thinking...{C.RESET}")
        sys.stdout.flush()
        time.sleep(0.08)
        i += 1
    sys.stdout.write(f"\r{' ' * 35}\r")
    sys.stdout.flush()


class RAMTerminalUI:
    def __init__(self):
        self.width = get_terminal_width()
        # Pending destructive command waiting for 'confirm'
        self._pending_destructive: str | None = None

    def run(self):
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from agent_core import RAMAgent

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        agent = RAMAgent()

        try:
            loop.run_until_complete(self._main_loop(agent))
        finally:
            loop.run_until_complete(agent.close())
            loop.close()

    async def _main_loop(self, agent):
        clear_screen()
        print_header(self.width)
        print_connection_msg()

        welcome = (
            f"Online and ready, Boss. I'm RAM — your Ubuntu OS Agent.\n"
            f"  Type {C.GREEN}'help'{C.WHITE} to see what I can do, "
            f"{C.GREEN}'clear'{C.WHITE} to reset, "
            f"{C.GREEN}'exit'{C.WHITE} to quit."
        )
        print_ram_response(welcome)

        while True:
            print_user_prompt()
            try:
                user_input = input().strip()
            except (EOFError, KeyboardInterrupt):
                print(f"\n{C.BRIGHT_GREEN}RAM: Shutting down. Stay sharp, Boss.{C.RESET}")
                break

            if not user_input:
                continue

            # ── Built-in commands ──────────────────────────────────────────
            if user_input.lower() in ("exit", "quit", "bye"):
                print_ram_response("Shutting down. Stay sharp, Boss.")
                break

            if user_input.lower() == "clear":
                agent.clear_history()
                self._pending_destructive = None
                clear_screen()
                print_header(self.width)
                print_connection_msg()
                print_ram_response("Memory cleared. Fresh start, Boss.")
                continue

            if user_input.lower() == "help":
                self._print_help()
                continue

            if user_input.lower() == "sysinfo":
                user_input = "Give me a full system overview: CPU, RAM, disk, uptime, battery, temperature, processes, and network."

            # ── Confirm pending destructive command ────────────────────────
            if user_input.lower() == "confirm" and self._pending_destructive:
                cmd = self._pending_destructive
                self._pending_destructive = None
                print_ram_response(f"Executing confirmed command: {cmd}")
                import subprocess
                try:
                    result = subprocess.run(
                        cmd, shell=True, capture_output=True, text=True, timeout=30
                    )
                    out = (result.stdout + result.stderr).strip() or "(done)"
                    print_ram_response(out)
                except Exception as e:
                    print_ram_response(f"[Error: {e}]")
                continue

            # ── Thinking animation ─────────────────────────────────────────
            stop_event = threading.Event()
            think_thread = threading.Thread(
                target=animate_thinking, args=(stop_event,), daemon=True
            )
            think_thread.start()

            try:
                response = await agent.chat(user_input)
            except Exception as e:
                response = f"[Error: {e}]"
            finally:
                stop_event.set()
                think_thread.join()

            # ── Check if response contains a pending destructive action ────
            if "[CONFIRMATION REQUIRED]" in response:
                import re
                # Extract the command from the confirmation message
                m = re.search(r'Destructive command: (.+?)\n', response)
                if m:
                    self._pending_destructive = m.group(1).strip()
                print_ram_response(response)
                print(f"\n  {C.YELLOW}Type {C.GREEN}'confirm'{C.YELLOW} to execute, or anything else to cancel.{C.RESET}")
            else:
                self._pending_destructive = None
                print_ram_response(response)

    def _print_help(self):
        help_text = f"""
{C.BRIGHT_GREEN}RAM Capabilities:{C.RESET}

{C.DARK_GREEN}System{C.RESET}
  • Shell commands    — just ask, e.g. "run ls -la"
  • System info       — "sysinfo", "CPU usage", "memory"
  • Process manager   — "list processes", "kill PID 1234"
  • File ops          — "find files", "read ~/.bashrc"

{C.DARK_GREEN}Apps & GUI{C.RESET}
  • Open apps         — "open calculator", "open browser"
  • Screenshots       — "take a screenshot"  (needs: scrot)
  • Webcam            — "take a photo"        (needs: fswebcam)

{C.DARK_GREEN}Web & Search{C.RESET}
  • Browser           — "search YouTube for...", "open google.com"
  • Maps              — "directions from X to Y"

{C.DARK_GREEN}Media & Games{C.RESET}
  • Games             — "list games", "launch nethack"
  • Video/photo       — "record 10 second video"

{C.DARK_GREEN}Quick Commands{C.RESET}
  {C.GREEN}sysinfo{C.WHITE}   — full system status
  {C.GREEN}clear{C.WHITE}     — reset conversation
  {C.GREEN}confirm{C.WHITE}   — confirm a pending destructive action
  {C.GREEN}exit{C.WHITE}      — quit RAM
"""
        print(help_text)
