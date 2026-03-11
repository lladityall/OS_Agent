#!/usr/bin/env python3
"""
RAM Tool: Terminal Games
Launch and list available terminal-based games.
"""

import subprocess
import shutil
from typing import Optional

KNOWN_GAMES = {
    "nethack": {
        "cmd": "nethack",
        "install": "sudo apt install nethack-console",
        "desc": "Classic dungeon crawler RPG"
    },
    "snake": {
        "cmd": "python3 -c \"import curses; from curses import wrapper; ...\"",
        "install": "pip install curses-menu",
        "desc": "Classic snake game"
    },
    "tetris": {
        "cmd": "tint",
        "install": "sudo apt install tint",
        "desc": "Tetris in the terminal"
    },
    "pacman": {
        "cmd": "myman",
        "install": "sudo apt install myman",
        "desc": "Pac-Man clone"
    },
    "chess": {
        "cmd": "gnuchess",
        "install": "sudo apt install gnuchess",
        "desc": "GNU Chess engine"
    },
    "2048": {
        "cmd": "2048",
        "install": "sudo apt install 2048",
        "desc": "Sliding tile puzzle 2048"
    },
    "bastet": {
        "cmd": "bastet",
        "install": "sudo apt install bastet",
        "desc": "Tetris with the worst pieces"
    },
    "cmatrix": {
        "cmd": "cmatrix",
        "install": "sudo apt install cmatrix",
        "desc": "Matrix rain effect"
    },
    "cowsay": {
        "cmd": "cowsay",
        "install": "sudo apt install cowsay",
        "desc": "Talking cow ASCII art"
    },
    "sl": {
        "cmd": "sl",
        "install": "sudo apt install sl",
        "desc": "Steam Locomotive animation"
    },
    "nudoku": {
        "cmd": "nudoku",
        "install": "sudo apt install nudoku",
        "desc": "Sudoku in terminal"
    },
    "moon-buggy": {
        "cmd": "moon-buggy",
        "install": "sudo apt install moon-buggy",
        "desc": "Drive a moon buggy and shoot rocks"
    },
    "nsnake": {
        "cmd": "nsnake",
        "install": "sudo apt install nsnake",
        "desc": "Snake with ncurses"
    },
    "ninvaders": {
        "cmd": "ninvaders",
        "install": "sudo apt install ninvaders",
        "desc": "Space Invaders clone"
    },
    "greed": {
        "cmd": "greed",
        "install": "sudo apt install greed",
        "desc": "Tron-like eating game"
    },
}


def list_games() -> dict:
    """Return installed and available games"""
    installed = []
    available = []

    for name, info in KNOWN_GAMES.items():
        cmd_base = info["cmd"].split()[0]
        if shutil.which(cmd_base):
            installed.append({
                "name": name,
                "command": info["cmd"],
                "description": info["desc"],
                "status": "installed"
            })
        else:
            available.append({
                "name": name,
                "install": info["install"],
                "description": info["desc"],
                "status": "not installed"
            })

    return {
        "installed": installed,
        "available": available,
        "total_installed": len(installed),
        "total_available": len(available),
    }


def launch_game(name: str) -> dict:
    """Launch a game in a new terminal window"""
    if name not in KNOWN_GAMES:
        return {"success": False, "error": f"Unknown game: {name}. Use list_games() to see options."}

    info = KNOWN_GAMES[name]
    cmd_base = info["cmd"].split()[0]

    if not shutil.which(cmd_base):
        return {
            "success": False,
            "error": f"{name} is not installed.",
            "install_cmd": info["install"]
        }

    try:
        # Try to launch in a new terminal
        for term in ["gnome-terminal", "xterm", "konsole", "xfce4-terminal"]:
            if shutil.which(term):
                if term == "gnome-terminal":
                    subprocess.Popen([term, "--", "bash", "-c", f"{info['cmd']}; bash"])
                else:
                    subprocess.Popen([term, "-e", info['cmd']])
                return {"success": True, "launched": name, "terminal": term}

        # Fallback: run inline
        subprocess.Popen(info['cmd'], shell=True)
        return {"success": True, "launched": name, "terminal": "inline"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def install_game(name: str) -> dict:
    """Install a game"""
    if name not in KNOWN_GAMES:
        return {"success": False, "error": f"Unknown game: {name}"}

    install_cmd = KNOWN_GAMES[name]["install"]
    try:
        result = subprocess.run(
            install_cmd, shell=True, capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            return {"success": True, "installed": name}
        return {"success": False, "error": result.stderr[:500]}
    except Exception as e:
        return {"success": False, "error": str(e)}


def format_games_list(games: dict) -> str:
    lines = []
    lines.append("=== INSTALLED GAMES ===")
    if games["installed"]:
        for g in games["installed"]:
            lines.append(f"  ✓ {g['name']:<15}  {g['description']}")
    else:
        lines.append("  (none installed)")

    lines.append("\n=== AVAILABLE TO INSTALL ===")
    for g in games["available"][:10]:
        lines.append(f"  • {g['name']:<15}  {g['description']}")
        lines.append(f"    Install: {g['install']}")

    return "\n".join(lines)


if __name__ == "__main__":
    games = list_games()
    print(format_games_list(games))
