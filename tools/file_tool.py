#!/usr/bin/env python3
"""
RAM Tool: File Operations
Search, read, write, modify, delete files; manage cron jobs.
"""

import os
import shutil
import fnmatch
import subprocess
from pathlib import Path
from typing import Optional, List
from datetime import datetime


def search_files(
    root: str = "~",
    pattern: str = "*",
    content: Optional[str] = None,
    max_results: int = 50,
) -> List[dict]:
    """Search for files by name pattern and optionally content"""
    root_path = Path(root).expanduser()
    results = []

    try:
        for p in root_path.rglob(pattern):
            if len(results) >= max_results:
                break
            try:
                info = {
                    "path": str(p),
                    "size_bytes": p.stat().st_size if p.is_file() else None,
                    "modified": datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                    "type": "file" if p.is_file() else "dir",
                }

                if content and p.is_file():
                    try:
                        text = p.read_text(errors="ignore")
                        if content.lower() in text.lower():
                            info["content_match"] = True
                            results.append(info)
                    except Exception:
                        pass
                else:
                    results.append(info)
            except (PermissionError, OSError):
                pass
    except Exception as e:
        results.append({"error": str(e)})

    return results


def read_file(path: str, max_chars: int = 4000) -> dict:
    p = Path(path).expanduser()
    try:
        if not p.exists():
            return {"success": False, "error": f"File not found: {path}"}
        if not p.is_file():
            return {"success": False, "error": f"Not a file: {path}"}

        content = p.read_text(errors="replace")
        truncated = len(content) > max_chars
        return {
            "success": True,
            "path": str(p),
            "content": content[:max_chars],
            "truncated": truncated,
            "total_chars": len(content),
            "size_bytes": p.stat().st_size,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def write_file(path: str, content: str, append: bool = False) -> dict:
    p = Path(path).expanduser()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if append else "w"
        with open(p, mode, encoding="utf-8") as f:
            f.write(content)
        return {
            "success": True,
            "path": str(p),
            "bytes_written": len(content.encode()),
            "mode": "append" if append else "write",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def list_directory(path: str = "~", show_hidden: bool = False) -> dict:
    p = Path(path).expanduser()
    try:
        items = []
        for entry in sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            if not show_hidden and entry.name.startswith("."):
                continue
            try:
                stat = entry.stat()
                items.append({
                    "name": entry.name,
                    "type": "dir" if entry.is_dir() else "file",
                    "size_bytes": stat.st_size if entry.is_file() else None,
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    "permissions": oct(stat.st_mode)[-3:],
                })
            except (PermissionError, OSError):
                items.append({"name": entry.name, "type": "unknown"})

        return {"success": True, "path": str(p), "items": items, "count": len(items)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def delete_file(path: str, confirm: bool = False) -> dict:
    if not confirm:
        return {
            "success": False,
            "requires_confirmation": True,
            "message": f"Are you sure you want to delete: {path}? Call with confirm=True to proceed.",
        }
    p = Path(path).expanduser()
    try:
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()
        return {"success": True, "deleted": str(p)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def copy_file(src: str, dst: str) -> dict:
    try:
        src_p = Path(src).expanduser()
        dst_p = Path(dst).expanduser()
        dst_p.parent.mkdir(parents=True, exist_ok=True)
        if src_p.is_dir():
            shutil.copytree(src_p, dst_p)
        else:
            shutil.copy2(src_p, dst_p)
        return {"success": True, "src": str(src_p), "dst": str(dst_p)}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Cron Jobs ──────────────────────────────────────────────────────────────

def list_cron_jobs() -> dict:
    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        if result.returncode != 0:
            return {"success": True, "jobs": [], "raw": "(no crontab)"}
        lines = [l for l in result.stdout.splitlines() if l.strip() and not l.startswith("#")]
        return {"success": True, "jobs": lines, "raw": result.stdout}
    except Exception as e:
        return {"success": False, "error": str(e)}


def add_cron_job(schedule: str, command: str) -> dict:
    """Add a cron job. schedule like '*/5 * * * *'"""
    try:
        existing = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        current = existing.stdout if existing.returncode == 0 else ""
        new_entry = f"{schedule} {command}\n"
        new_crontab = current.rstrip("\n") + "\n" + new_entry
        proc = subprocess.run(["crontab", "-"], input=new_crontab, capture_output=True, text=True)
        if proc.returncode == 0:
            return {"success": True, "added": new_entry.strip()}
        return {"success": False, "error": proc.stderr}
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # Test
    result = list_directory("~")
    for item in result.get("items", [])[:10]:
        t = "📁" if item["type"] == "dir" else "📄"
        print(f"  {t} {item['name']}")
