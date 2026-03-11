#!/bin/bash
# ============================================================
# RAM OS Agent - Install & Setup Script
# Run: chmod +x install.sh && ./install.sh
# ============================================================

set -e

GREEN='\033[92m'
CYAN='\033[96m'
YELLOW='\033[93m'
RED='\033[91m'
RESET='\033[0m'
BOLD='\033[1m'

RAM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$HOME/.ram"

echo -e "${GREEN}${BOLD}"
echo "██████╗  █████╗ ███╗   ███╗"
echo "██╔══██╗██╔══██╗████╗ ████║"
echo "██████╔╝███████║██╔████╔██║"
echo "██╔══██╗██╔══██║██║╚██╔╝██║"
echo "██║  ██║██║  ██║██║ ╚═╝ ██║"
echo "╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝"
echo -e "${CYAN}  Ubuntu OS Agent - Installer${RESET}"
echo ""

echo -e "${CYAN}[1/5] Checking Python 3...${RESET}"
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}Python 3 not found! Install with: sudo apt install python3${RESET}"
    exit 1
fi
python3 --version

echo -e "${CYAN}[2/5] Installing Python dependencies...${RESET}"
pip3 install psutil ollama --break-system-packages 2>/dev/null || \
pip3 install psutil ollama 2>/dev/null || \
python3 -m pip install psutil ollama --user

echo -e "${CYAN}[3/5] Creating config directory...${RESET}"
mkdir -p "$CONFIG_DIR/kb"
if [ ! -f "$CONFIG_DIR/config.json" ]; then
    cat > "$CONFIG_DIR/config.json" << 'EOF'
{
  "ollama_api_key": "sk_4e2f36c12e409003ccf8da7c678de36ca802ed81d0cd26f3",
  "ollama_host": "https://api.ollama.ai",
  "ollama_model": "llama3.2",
  "telegram_bot_token": "",
  "telegram_chat_id": "",
  "timezone": "Asia/Kolkata"
}
EOF
    echo -e "  ${GREEN}✓ Config created at $CONFIG_DIR/config.json${RESET}"
else
    echo -e "  ${YELLOW}Config already exists, skipping.${RESET}"
fi

echo -e "${CYAN}[4/5] Making RAM executable...${RESET}"
chmod +x "$RAM_DIR/main.py"
mkdir -p "$HOME/.local/bin"

# Create a system-wide launcher
cat > "$HOME/.local/bin/ram" << LAUNCHEREOF
#!/bin/bash
cd "$RAM_DIR"
export OLLAMA_API_KEY="sk_4e2f36c12e409003ccf8da7c678de36ca802ed81d0cd26f3"
export OLLAMA_HOST="https://api.ollama.ai"
python3 "$RAM_DIR/main.py" "\$@"
LAUNCHEREOF
chmod +x "$HOME/.local/bin/ram"

# Ensure ~/.local/bin is in PATH
if ! grep -q ".local/bin" "$HOME/.bashrc" 2>/dev/null; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    echo -e "  ${GREEN}✓ Added ~/.local/bin to PATH in .bashrc${RESET}"
fi
echo -e "  ${GREEN}✓ Launcher created at ~/.local/bin/ram${RESET}"

echo -e "${CYAN}[5/5] Setting up keyboard shortcut (Super + A)...${RESET}"

# Detect desktop environment
if command -v gsettings &>/dev/null; then
    # GNOME / Ubuntu default
    SHORTCUT_NAME="RAM OS Agent"
    SHORTCUT_CMD="bash -c 'cd $RAM_DIR && OLLAMA_API_KEY=sk_4e2f36c12e409003ccf8da7c678de36ca802ed81d0cd26f3 OLLAMA_HOST=https://api.ollama.ai python3 $RAM_DIR/main.py'"
    
    # Create a .desktop launcher for terminal
    cat > "$HOME/.local/share/applications/ram-agent.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=RAM OS Agent
Comment=Ubuntu OS Agent
Exec=bash -c 'cd $RAM_DIR && OLLAMA_API_KEY=sk_4e2f36c12e409003ccf8da7c678de36ca802ed81d0cd26f3 OLLAMA_HOST=https://api.ollama.ai python3 $RAM_DIR/main.py; bash'
Icon=utilities-terminal
Terminal=true
Categories=Utility;
Keywords=ram;agent;ai;
EOF
    chmod +x "$HOME/.local/share/applications/ram-agent.desktop"

    # Set Super+A shortcut
    BINDING_PATH="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/ram-agent/"
    RAM_LAUNCH_CMD="gnome-terminal -- bash -c 'cd $RAM_DIR && OLLAMA_API_KEY=sk_4e2f36c12e409003ccf8da7c678de36ca802ed81d0cd26f3 OLLAMA_HOST=https://api.ollama.ai python3 $RAM_DIR/main.py; exec bash'"

    # Check if already set
    if gsettings get org.gnome.settings-daemon.plugins.media-keys custom-keybindings 2>/dev/null | grep -q "ram-agent"; then
        echo -e "  ${YELLOW}Shortcut already configured.${RESET}"
    else
        # Build new bindings list using pure bash (no JSON parsing needed)
        RAW=$(gsettings get org.gnome.settings-daemon.plugins.media-keys custom-keybindings 2>/dev/null || echo "")
        # Strip @as prefix if present, normalize to a clean list
        RAW=$(echo "$RAW" | sed "s/@as //g" | tr -d "\n")

        if [ -z "$RAW" ] || [ "$RAW" = "[]" ]; then
            NEW_BINDINGS="['$BINDING_PATH']"
        else
            # Insert before the closing ] — works even with existing entries
            NEW_BINDINGS=$(echo "$RAW" | sed "s|]|, '$BINDING_PATH']|")
        fi

        gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings "$NEW_BINDINGS" 2>/dev/null \
        && gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:"$BINDING_PATH" name "RAM OS Agent" 2>/dev/null \
        && gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:"$BINDING_PATH" command "$RAM_LAUNCH_CMD" 2>/dev/null \
        && gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:"$BINDING_PATH" binding "<Super>a" 2>/dev/null \
        && echo -e "  ${GREEN}✓ Keyboard shortcut set: Super + A${RESET}" \
        || echo -e "  ${YELLOW}⚠ Could not set shortcut automatically. See manual setup below.${RESET}"
    fi
else
    echo -e "  ${YELLOW}Non-GNOME desktop detected. Set shortcut manually.${RESET}"
fi

echo ""
echo -e "${GREEN}${BOLD}═══════════════════════════════════════════${RESET}"
echo -e "${GREEN}${BOLD}  RAM OS Agent Installed Successfully!${RESET}"
echo -e "${GREEN}${BOLD}═══════════════════════════════════════════${RESET}"
echo ""
echo -e "${CYAN}How to launch RAM:${RESET}"
echo -e "  • ${GREEN}Super + A${RESET} (keyboard shortcut)"
echo -e "  • Type ${GREEN}ram${RESET} in terminal"
echo -e "  • Run: ${GREEN}python3 $RAM_DIR/main.py${RESET}"
echo ""
echo -e "${CYAN}Optional setup:${RESET}"
echo -e "  • Gmail/Calendar: ${YELLOW}python3 $RAM_DIR/tools/email_tool.py --setup${RESET}"
echo -e "  • Telegram:       ${YELLOW}python3 $RAM_DIR/tools/telegram_tool.py --setup TOKEN CHAT_ID${RESET}"
echo -e "  • Browser tools:  ${YELLOW}pip3 install playwright && python3 -m playwright install chromium${RESET}"
echo ""
echo -e "${CYAN}Config file: ${YELLOW}$CONFIG_DIR/config.json${RESET}"
echo ""
