#!/usr/bin/env python3
"""
RAM Tool: Knowledge Base
Store and retrieve notes, scripts, skill instructions, and references.
The knowledge base lives in ~/.ram/kb/ as markdown files.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List

KB_DIR = Path.home() / ".ram" / "kb"
KB_DIR.mkdir(parents=True, exist_ok=True)

INDEX_PATH = KB_DIR / "_index.json"


def _load_index() -> dict:
    if INDEX_PATH.exists():
        with open(INDEX_PATH) as f:
            return json.load(f)
    return {}


def _save_index(index: dict):
    with open(INDEX_PATH, "w") as f:
        json.dump(index, f, indent=2)


def add_entry(title: str, content: str, tags: Optional[List[str]] = None) -> dict:
    """Add or update a knowledge base entry"""
    slug = title.lower().replace(" ", "_").replace("/", "-")[:50]
    file_path = KB_DIR / f"{slug}.md"

    tags = tags or []
    frontmatter = (
        f"---\ntitle: {title}\ntags: {tags}\n"
        f"created: {datetime.now().isoformat()}\n---\n\n"
    )
    file_path.write_text(frontmatter + content)

    index = _load_index()
    index[slug] = {
        "title": title,
        "tags": tags,
        "path": str(file_path),
        "updated": datetime.now().isoformat(),
    }
    _save_index(index)
    return {"success": True, "slug": slug, "path": str(file_path)}


def search_kb(query: str) -> List[dict]:
    """Search knowledge base by title or content"""
    query_lower = query.lower()
    results = []
    index = _load_index()

    for slug, meta in index.items():
        file_path = Path(meta["path"])
        if not file_path.exists():
            continue

        content = file_path.read_text(errors="replace").lower()
        title_match = query_lower in meta["title"].lower()
        content_match = query_lower in content
        tag_match = any(query_lower in tag.lower() for tag in meta.get("tags", []))

        if title_match or content_match or tag_match:
            # Get a snippet
            idx = content.find(query_lower)
            snippet = ""
            if idx >= 0:
                start = max(0, idx - 50)
                snippet = file_path.read_text(errors="replace")[start:start+200]

            results.append({
                "slug": slug,
                "title": meta["title"],
                "tags": meta.get("tags", []),
                "snippet": snippet.strip(),
                "path": str(file_path),
            })

    return results


def get_entry(slug_or_title: str) -> dict:
    """Retrieve a knowledge base entry"""
    index = _load_index()
    slug = slug_or_title.lower().replace(" ", "_")[:50]

    if slug in index:
        path = Path(index[slug]["path"])
        content = path.read_text(errors="replace") if path.exists() else ""
        return {"success": True, **index[slug], "content": content}

    # Try title search
    for s, meta in index.items():
        if meta["title"].lower() == slug_or_title.lower():
            path = Path(meta["path"])
            content = path.read_text(errors="replace") if path.exists() else ""
            return {"success": True, **meta, "content": content}

    return {"success": False, "error": f"Entry not found: {slug_or_title}"}


def list_entries(tag: Optional[str] = None) -> List[dict]:
    """List all KB entries, optionally filtered by tag"""
    index = _load_index()
    entries = []
    for slug, meta in index.items():
        if tag and tag not in meta.get("tags", []):
            continue
        entries.append({"slug": slug, **meta})
    return sorted(entries, key=lambda x: x.get("updated", ""), reverse=True)


def delete_entry(slug: str) -> dict:
    index = _load_index()
    if slug not in index:
        return {"success": False, "error": f"Entry '{slug}' not found"}
    path = Path(index[slug]["path"])
    if path.exists():
        path.unlink()
    del index[slug]
    _save_index(index)
    return {"success": True, "deleted": slug}


# Seed some default entries
def _seed_defaults():
    defaults = [
        {
            "title": "RAM Quick Reference",
            "tags": ["ram", "help", "reference"],
            "content": """# RAM Quick Reference

## Shell Commands
Ask RAM to run any bash command. Examples:
- "Run ls -la in my home directory"
- "Show me the contents of /etc/hosts"
- "Create a folder called Projects"

## System Diagnostics
- "Show system status" → full diagnostics
- "What's my CPU usage?" → CPU info
- "How much RAM do I have left?" → memory info

## File Operations
- "Find all .py files in ~/Projects"
- "Read my .bashrc file"
- "Create a file called notes.txt with content..."

## Quick Tips
- Say "confirm" to execute destructive operations
- Use "clear" to reset conversation history
- Use "sysinfo" as a shortcut for full system status
""",
        },
        {
            "title": "Useful Ubuntu Commands",
            "tags": ["ubuntu", "linux", "commands"],
            "content": """# Useful Ubuntu Commands

## System Management
```
sudo apt update && sudo apt upgrade   # Update system
systemctl status <service>            # Check service status
journalctl -xe                        # View system logs
df -h                                 # Disk usage
free -h                               # Memory usage
htop                                  # Interactive process viewer
```

## Networking
```
ip addr show                          # List network interfaces
ss -tulpn                             # List open ports
nmcli device status                   # Network manager status
ping -c 4 8.8.8.8                    # Test connectivity
```

## File Management
```
find / -name "*.log" -mtime -7        # Find recent log files
du -sh ~/*/                           # Directory sizes
tar -czf archive.tar.gz /path         # Create archive
rsync -av src/ dst/                   # Sync directories
```
""",
        },
    ]

    index = _load_index()
    if not index:
        for d in defaults:
            add_entry(d["title"], d["content"], d["tags"])


# Seed on first import
_seed_defaults()


if __name__ == "__main__":
    print("=== KNOWLEDGE BASE ===")
    entries = list_entries()
    for e in entries:
        print(f"  [{e['slug']}] {e['title']}  tags={e['tags']}")

    print("\n=== SEARCH TEST ===")
    results = search_kb("ubuntu")
    for r in results:
        print(f"  Found: {r['title']}")
        print(f"  Snippet: {r['snippet'][:100]}")
