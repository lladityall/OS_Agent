#!/usr/bin/env python3
"""
RAM - Ubuntu OS Agent
Main entry point - launches the terminal UI and agent
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from ui.terminal_ui import RAMTerminalUI


def main():
    os.environ.setdefault("OLLAMA_API_KEY", "e367096933634fe4a2c7c722e00a1330.eordImDQUFo0YlUAo-jD-AE0")
    os.environ.setdefault("OLLAMA_HOST", "https://ollama.com")

    app = RAMTerminalUI()
    try:
        app.run()
    except KeyboardInterrupt:
        print("\n\033[92mRAM: Goodbye, Boss.\033[0m")
        sys.exit(0)


if __name__ == "__main__":
    main()
