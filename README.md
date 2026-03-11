# RAM — Ubuntu OS Agent

```
██████╗  █████╗ ███╗   ███╗
██╔══██╗██╔══██╗████╗ ████║
██████╔╝███████║██╔████╔██║
██╔══██╗██╔══██║██║╚██╔╝██║
██║  ██║██║  ██║██║ ╚═╝ ██║
╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝
     Ubuntu OS Agent v1.0
```

RAM is a powerful, terminal-based AI agent for your Ubuntu machine. It uses the Ollama Cloud API and runs right in your terminal with a dark hacker aesthetic.

---

## Quick Start

```bash
chmod +x install.sh
./install.sh
```

Then press **Super + A** (Windows key + A) to launch RAM from anywhere.

Or just run:
```bash
python3 main.py
# or after install:
ram
```

---

## Project Structure

```
RAM/
├── main.py              ← Entry point
├── agent_core.py        ← Core AI agent (Ollama Cloud API)
├── install.sh           ← Installer + keyboard shortcut setup
├── requirements.txt     ← Python dependencies
├── README.md
├── ui/
│   └── terminal_ui.py   ← Dark terminal UI (hacker aesthetic)
├── tools/
│   ├── shell_tool.py    ← Run bash commands
│   ├── sysdiag_tool.py  ← CPU, RAM, disk, temp, network
│   ├── process_tool.py  ← Processes, uptime, connections
│   ├── file_tool.py     ← File operations + cron jobs
│   ├── email_tool.py    ← Gmail + Google Calendar + Tasks
│   ├── telegram_tool.py ← Telegram messaging
│   ├── browser_tool.py  ← Web browsing automation
│   ├── media_tool.py    ← Webcam photos, video, timelapse
│   ├── games_tool.py    ← Terminal games launcher
│   ├── maps_tool.py     ← Google Maps + directions
│   └── kb_tool.py       ← Knowledge base
└── config/
```

---

## Capabilities

| Category | What RAM can do |
|---|---|
| **Shell** | Run any bash command (confirms destructive ops) |
| **Diagnostics** | CPU, RAM, disk, temperature, network ping |
| **Processes** | List processes, kill by PID, active connections |
| **Files** | Search, read, write, delete, cron jobs |
| **Email** | Read Gmail, send/reply, search, drafts |
| **Calendar** | List/create/delete Google Calendar events |
| **Tasks** | List/add/complete/delete Google Tasks |
| **Telegram** | Send messages, list recent chats |
| **Browser** | Open pages, fill forms, screenshots, search |
| **Maps** | Search Google Maps, get directions |
| **Media** | Take photos, record video, timelapse |
| **Games** | Launch terminal games, install new ones |
| **Knowledge Base** | Store/retrieve notes, scripts, references |

---

## Setup for Optional Features

### Gmail + Google Calendar
```bash
# 1. Enable Gmail API + Calendar API at console.cloud.google.com
# 2. Download credentials.json to ~/.ram/credentials.json
# 3. Run:
python3 tools/email_tool.py --setup
```

### Telegram
```bash
# 1. Create a bot via @BotFather → get token
# 2. Message @userinfobot → get your chat_id
python3 tools/telegram_tool.py --setup YOUR_BOT_TOKEN YOUR_CHAT_ID
```

### Web Browser Automation
```bash
pip3 install playwright
python3 -m playwright install chromium
```

### Webcam (photos/video)
```bash
sudo apt install fswebcam ffmpeg
```

### Terminal Games
```bash
sudo apt install nethack-console tint moon-buggy nsnake ninvaders nudoku
```

---

## Configuration

Edit `~/.ram/config.json`:
```json
{
  "ollama_api_key": "sk_4e2f36c12e409003ccf8da7c678de36ca802ed81d0cd26f3",
  "ollama_host": "https://api.ollama.ai",
  "ollama_model": "llama3.2",
  "telegram_bot_token": "YOUR_TOKEN",
  "telegram_chat_id": "YOUR_CHAT_ID",
  "timezone": "Asia/Kolkata"
}
```

---

## Keyboard Shortcut

The installer sets **Super + A** (Windows key + A) as the global hotkey.

To set it manually in GNOME:
1. Settings → Keyboard → Custom Shortcuts
2. Add: Name = `RAM Agent`, Command = `/path/to/RAM/main.py`, Shortcut = `Super+A`

---

## Example Conversations

```
You: what's my system status?
RAM: CPU: 12% (8 cores) | RAM: 4.2GB / 16GB (26%) | Disk: 89GB / 500GB (18%)...

You: run ls -la in my downloads folder
RAM: [CMD: ls -la ~/Downloads]
total 1.2G
drwxr-xr-x  12 user user 4096 Mar 9 20:00 .
...

You: find all python files in my Projects folder
RAM: Searching ~/Projects for *.py...

You: what games can I play?
RAM: Installed: nethack, cmatrix
Available to install: tetris, pacman, chess, 2048...

You: take a screenshot of github.com
RAM: Opening headless browser... Screenshot saved to ~/RAM_media/screenshot.png

You: show me directions from Mumbai to Pune
RAM: Opening Google Maps directions (driving) Mumbai → Pune...
```

---

## Dependencies

- **Python 3.8+**
- **psutil** — system metrics
- **httpx** — async HTTP for Ollama API
- **agno** — agent framework (optional enhanced features)

Install: `pip3 install psutil httpx agno --break-system-packages`

---

*Built for Ubuntu. Made to be fast, sharp, and yours.*
