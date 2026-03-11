#!/usr/bin/env python3
"""
RAM Tool: Process & Resource Info
List running processes, uptime, battery, disk space, active network connections.
"""

import subprocess
import psutil
import socket
from datetime import datetime, timedelta
from typing import Optional


def list_processes(
    sort_by: str = "cpu",  # cpu | memory | pid | name
    top_n: int = 20,
    filter_name: Optional[str] = None,
) -> list:
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent',
                                   'memory_percent', 'status', 'cmdline', 'create_time']):
        try:
            info = p.info
            if filter_name and filter_name.lower() not in (info.get('name') or '').lower():
                continue
            info['create_time_human'] = datetime.fromtimestamp(
                info.get('create_time', 0)
            ).strftime("%H:%M:%S") if info.get('create_time') else '-'
            procs.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    key_map = {
        "cpu": lambda x: x.get('cpu_percent') or 0,
        "memory": lambda x: x.get('memory_percent') or 0,
        "pid": lambda x: x.get('pid') or 0,
        "name": lambda x: (x.get('name') or '').lower(),
    }
    procs.sort(key=key_map.get(sort_by, key_map["cpu"]), reverse=(sort_by != "name"))
    return procs[:top_n]


def kill_process(pid: int, confirm: bool = False) -> dict:
    if not confirm:
        return {
            "success": False,
            "requires_confirmation": True,
            "message": f"Kill PID {pid}? Call with confirm=True to proceed."
        }
    try:
        p = psutil.Process(pid)
        name = p.name()
        p.terminate()
        return {"success": True, "killed_pid": pid, "name": name}
    except psutil.NoSuchProcess:
        return {"success": False, "error": f"No process with PID {pid}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_uptime() -> dict:
    boot = psutil.boot_time()
    now = datetime.now().timestamp()
    secs = int(now - boot)
    td = timedelta(seconds=secs)
    days = td.days
    hours, rem = divmod(td.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    return {
        "boot_time": datetime.fromtimestamp(boot).strftime("%Y-%m-%d %H:%M:%S"),
        "uptime_seconds": secs,
        "days": days,
        "hours": hours,
        "minutes": minutes,
        "seconds": seconds,
        "human": f"{days}d {hours}h {minutes}m {seconds}s",
    }


def get_disk_space(paths: Optional[list] = None) -> list:
    if not paths:
        paths = ["/"]
    results = []
    for path in paths:
        try:
            usage = psutil.disk_usage(path)
            results.append({
                "path": path,
                "total_gb": round(usage.total / 1024**3, 2),
                "used_gb": round(usage.used / 1024**3, 2),
                "free_gb": round(usage.free / 1024**3, 2),
                "percent": usage.percent,
            })
        except Exception as e:
            results.append({"path": path, "error": str(e)})
    return results


def get_active_connections(kind: str = "inet", top_n: int = 30) -> list:
    conns = []
    try:
        for c in psutil.net_connections(kind=kind):
            try:
                # Try to get process name
                pname = None
                if c.pid:
                    try:
                        pname = psutil.Process(c.pid).name()
                    except Exception:
                        pass

                conns.append({
                    "local": f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "-",
                    "remote": f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "-",
                    "status": c.status,
                    "pid": c.pid,
                    "process": pname,
                })
            except Exception:
                pass
    except Exception as e:
        conns.append({"error": str(e)})
    return conns[:top_n]


def get_open_ports() -> list:
    """List locally open/listening ports"""
    result = []
    for c in psutil.net_connections():
        if c.status == psutil.CONN_LISTEN:
            try:
                result.append({
                    "port": c.laddr.port,
                    "ip": c.laddr.ip,
                    "pid": c.pid,
                    "process": psutil.Process(c.pid).name() if c.pid else None,
                })
            except Exception:
                pass
    return result


def format_process_table(procs: list) -> str:
    lines = [f"{'PID':>7}  {'Name':<25}  {'CPU%':>6}  {'MEM%':>6}  {'Status':<12}  {'User':<15}"]
    lines.append("─" * 80)
    for p in procs:
        lines.append(
            f"{p.get('pid', 0):>7}  "
            f"{(p.get('name') or '-'):<25}  "
            f"{(p.get('cpu_percent') or 0):>6.1f}  "
            f"{(p.get('memory_percent') or 0):>6.1f}  "
            f"{(p.get('status') or '-'):<12}  "
            f"{(p.get('username') or '-'):<15}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    print("=== TOP PROCESSES ===")
    procs = list_processes(top_n=10)
    print(format_process_table(procs))

    print("\n=== UPTIME ===")
    u = get_uptime()
    print(u["human"])

    print("\n=== DISK SPACE ===")
    for d in get_disk_space(["/"]):
        print(f"{d['path']}: {d['used_gb']}GB / {d['total_gb']}GB ({d['percent']}%)")
