#!/bin/bash
# ============================================================
# RAM OS Agent - Fix Installer (venv-aware)
# Run from inside your RAM2 folder:
#   bash fix_install.sh
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

echo -e "${CYAN}RAM_DIR detected: ${GREEN}$RAM_DIR${RESET}"

# ── Detect Python to use ──────────────────────────────────────────────────────
# Priority: venv in RAM dir > activated venv > system python3
if [ -f "$RAM_DIR/venv/bin/python3" ]; then
    PYTHON="$RAM_DIR/venv/bin/python3"
    echo -e "${CYAN}Using venv Python: ${GREEN}$PYTHON${RESET}"
elif [ -n "$VIRTUAL_ENV" ] && [ -f "$VIRTUAL_ENV/bin/python3" ]; then
    PYTHON="$VIRTUAL_ENV/bin/python3"
    echo -e "${CYAN}Using active venv Python: ${GREEN}$PYTHON${RESET}"
else
    PYTHON="$(which python3)"
    echo -e "${CYAN}Using system Python: ${GREEN}$PYTHON${RESET}"
fi

# ── Install dependencies into detected Python ─────────────────────────────────
echo -e "\n${CYAN}Installing dependencies into correct Python...${RESET}"
"$PYTHON" -m pip install psutil ollama --quiet
echo -e "${GREEN}✓ psutil + ollama installed${RESET}"

# ── Create launcher script ────────────────────────────────────────────────────
mkdir -p "$HOME/.local/bin"
LAUNCHER="$HOME/.local/bin/ram"

cat > "$LAUNCHER" << LAUNCHEREOF
#!/bin/bash
export OLLAMA_API_KEY="e367096933634fe4a2c7c722e00a1330.eordImDQUFo0YlUAo-jD-AE0"
export OLLAMA_HOST="https://ollama.com"
export DISPLAY="\${DISPLAY:-:0}"
cd "$RAM_DIR"
exec "$PYTHON" "$RAM_DIR/main.py" "\$@"
LAUNCHEREOF

chmod +x "$LAUNCHER"
echo -e "${GREEN}✓ Launcher created: $LAUNCHER${RESET}"
echo -e "  Python: ${CYAN}$PYTHON${RESET}"

# Add ~/.local/bin to PATH if missing
if ! echo "$PATH" | grep -q "$HOME/.local/bin"; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    echo -e "${GREEN}✓ Added ~/.local/bin to PATH in .bashrc${RESET}"
fi

# ── Keyboard shortcut (Super+A) ───────────────────────────────────────────────
echo -e "\n${CYAN}Setting up Super+A keyboard shortcut...${RESET}"

if ! command -v gsettings &>/dev/null; then
    echo -e "${YELLOW}gsettings not found — set shortcut manually in Settings > Keyboard${RESET}"
else
    BINDING_PATH="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/ram-agent/"

    # Find best non-snap terminal
    TERMINAL=""
    for t in xterm lxterminal xfce4-terminal mate-terminal tilix alacritty kitty gnome-terminal; do
        if command -v "$t" &>/dev/null; then
            TERMINAL="$t"
            break
        fi
    done

    if [ -z "$TERMINAL" ]; then
        echo -e "${RED}No terminal found! Install one: sudo apt install xterm${RESET}"
        TERMINAL="xterm"
    fi
    echo -e "  Using terminal: ${GREEN}$TERMINAL${RESET}"

    # Build launch command based on terminal
    if [ "$TERMINAL" = "xterm" ]; then
        TERM_CMD="xterm -fa 'Monospace' -fs 12 -bg black -fg green -e bash -c 'export OLLAMA_API_KEY=e367096933634fe4a2c7c722e00a1330.eordImDQUFo0YlUAo-jD-AE0; export OLLAMA_HOST=https://ollama.com; cd $RAM_DIR && $PYTHON $RAM_DIR/main.py; bash'"
    elif [ "$TERMINAL" = "gnome-terminal" ]; then
        TERM_CMD="gnome-terminal -- bash -c 'export OLLAMA_API_KEY=e367096933634fe4a2c7c722e00a1330.eordImDQUFo0YlUAo-jD-AE0; export OLLAMA_HOST=https://ollama.com; cd $RAM_DIR && $PYTHON $RAM_DIR/main.py; bash'"
    else
        TERM_CMD="$TERMINAL -- bash -c 'export OLLAMA_API_KEY=e367096933634fe4a2c7c722e00a1330.eordImDQUFo0YlUAo-jD-AE0; export OLLAMA_HOST=https://ollama.com; cd $RAM_DIR && $PYTHON $RAM_DIR/main.py; bash'"
    fi

    # Register binding
    RAW=$(gsettings get org.gnome.settings-daemon.plugins.media-keys custom-keybindings 2>/dev/null || echo "[]")
    RAW=$(echo "$RAW" | sed "s/@as //g" | tr -d "\n")

    if echo "$RAW" | grep -q "ram-agent"; then
        # Already registered — just update command and binding
        echo -e "  ${YELLOW}Binding already exists — updating command...${RESET}"
    else
        if [ "$RAW" = "[]" ] || [ -z "$RAW" ]; then
            NEW_BINDINGS="['$BINDING_PATH']"
        else
            NEW_BINDINGS=$(echo "$RAW" | sed "s|]|, '$BINDING_PATH']|")
        fi
        gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings "$NEW_BINDINGS"
    fi

    gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:"$BINDING_PATH" name "RAM OS Agent"
    gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:"$BINDING_PATH" command "$TERM_CMD"
    gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:"$BINDING_PATH" binding "<Super>a"

    echo -e "${GREEN}✓ Super+A shortcut set!${RESET}"
    echo -e "  Command: ${CYAN}$TERM_CMD${RESET}"

    # Verify
    echo -e "\n${CYAN}Verification:${RESET}"
    echo -e "  Binding : $(gsettings get org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:"$BINDING_PATH" binding)"
    echo -e "  Name    : $(gsettings get org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:"$BINDING_PATH" name)"
fi

# ── .desktop file ─────────────────────────────────────────────────────────────
mkdir -p "$HOME/.local/share/applications"
cat > "$HOME/.local/share/applications/ram-agent.desktop" << DESKTOPEOF
[Desktop Entry]
Version=1.0
Type=Application
Name=RAM OS Agent
Comment=Ubuntu AI OS Agent
Exec=$LAUNCHER
Icon=utilities-terminal
Terminal=true
Categories=Utility;System;
Keywords=ram;agent;ai;assistant;
DESKTOPEOF
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
echo -e "${GREEN}✓ .desktop entry created${RESET}"

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}════════════════════════════════════════════════${RESET}"
echo -e "${GREEN}${BOLD}  RAM Fixed & Ready!${RESET}"
echo -e "${GREEN}${BOLD}════════════════════════════════════════════════${RESET}"
echo ""
echo -e "  ${CYAN}Test now (open new terminal):${RESET}"
echo -e "    ${GREEN}source ~/.bashrc && ram${RESET}"
echo ""
echo -e "  ${CYAN}Or press:${RESET} ${GREEN}Super + A${RESET}"
echo ""
echo -e "  ${YELLOW}If Super+A still doesn't work:${RESET}"
echo -e "  Settings → Keyboard → Custom Shortcuts → find 'RAM OS Agent'"
echo -e "  If it shows 'disabled', click it and press Super+A manually."
echo ""
