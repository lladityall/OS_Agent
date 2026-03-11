#!/usr/bin/env python3
"""
RAM Tool: Telegram Messaging
Send messages and list contacts via Telegram Bot API.

SETUP:
1. Create a bot via @BotFather on Telegram → get BOT_TOKEN
2. Get your CHAT_ID by messaging @userinfobot
3. Add to ~/.ram/config.json:
   {
     "telegram_bot_token": "YOUR_BOT_TOKEN",
     "telegram_chat_id": "YOUR_CHAT_ID"
   }
"""

import json
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional

CONFIG_PATH = Path.home() / ".ram" / "config.json"


def _load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}


def _api_call(token: str, method: str, params: dict = None) -> dict:
    url = f"https://api.telegram.org/bot{token}/{method}"
    if params:
        data = urllib.parse.urlencode(params).encode()
        req = urllib.request.Request(url, data=data)
    else:
        req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"ok": False, "error": str(e)}


def send_message(
    text: str,
    chat_id: Optional[str] = None,
    bot_token: Optional[str] = None,
    parse_mode: str = "Markdown",
) -> dict:
    """Send a Telegram message"""
    config = _load_config()
    token = bot_token or config.get("telegram_bot_token")
    cid = chat_id or config.get("telegram_chat_id")

    if not token:
        return {"success": False, "error": "No bot token. Add telegram_bot_token to ~/.ram/config.json"}
    if not cid:
        return {"success": False, "error": "No chat_id. Add telegram_chat_id to ~/.ram/config.json"}

    result = _api_call(token, "sendMessage", {
        "chat_id": cid,
        "text": text,
        "parse_mode": parse_mode,
    })
    if result.get("ok"):
        return {"success": True, "message_id": result["result"]["message_id"]}
    return {"success": False, "error": result.get("description", str(result))}


def get_updates(limit: int = 10, bot_token: Optional[str] = None) -> dict:
    """Get recent Telegram updates (messages received)"""
    config = _load_config()
    token = bot_token or config.get("telegram_bot_token")
    if not token:
        return {"success": False, "error": "No bot token configured"}

    result = _api_call(token, "getUpdates", {"limit": limit})
    if not result.get("ok"):
        return {"success": False, "error": result.get("description")}

    messages = []
    for update in result.get("result", []):
        msg = update.get("message", {})
        if msg:
            messages.append({
                "from": msg.get("from", {}).get("username") or msg.get("from", {}).get("first_name"),
                "chat_id": msg.get("chat", {}).get("id"),
                "text": msg.get("text", ""),
                "date": msg.get("date"),
            })
    return {"success": True, "messages": messages}


def get_bot_info(bot_token: Optional[str] = None) -> dict:
    config = _load_config()
    token = bot_token or config.get("telegram_bot_token")
    if not token:
        return {"success": False, "error": "No bot token configured"}
    result = _api_call(token, "getMe")
    if result.get("ok"):
        return {"success": True, "bot": result["result"]}
    return {"success": False, "error": result.get("description")}


def setup_config(bot_token: str, chat_id: str):
    """Save Telegram config"""
    config = _load_config()
    config["telegram_bot_token"] = bot_token
    config["telegram_chat_id"] = chat_id
    CONFIG_PATH.parent.mkdir(exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
    print(f"✓ Telegram config saved to {CONFIG_PATH}")


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    if len(args) >= 2 and args[0] == "--setup":
        # python3 telegram_tool.py --setup TOKEN CHAT_ID
        setup_config(args[1], args[2] if len(args) > 2 else "")
    else:
        info = get_bot_info()
        print(info)
