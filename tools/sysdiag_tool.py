#!/usr/bin/env python3
"""
RAM Tool: System Diagnostics
CPU, RAM, disk, temperature, network, processes, battery, uptime.
"""

import subprocess
import platform
import socket
from datetime import datetime, timedelta

import psutil


def get_cpu_info() -> dict:
    freq = psutil.cpu_freq()
    return {
        "percent": psutil.cpu_percent(interval=0.5),
        "count_logical": psutil.cpu_count(logical=True),
        "count_physical": psutil.cpu_count(logical=False),
        "freq_mhz": round(freq.current, 1) if freq else None,
        "per_core": psutil.cpu_percent(interval=0.1, percpu=True),
    }


def get_ram_info() -> dict:
    vm = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {
        "total_mb": vm.total // 1024**2,
        "used_mb": vm.used // 1024**2,
        "available_mb": vm.available // 1024**2,
        "percent": vm.percent,
        "swap_total_mb": swap.total // 1024**2,
        "swap_used_mb": swap.used // 1024**2,
        "swap_percent": swap.percent,
    }


def get_disk_info(path: str = "/") -> dict:
    disk = psutil.disk_usage(path)
    io = psutil.disk_io_counters()
    return {
        "path": path,
        "total_gb": round(disk.total / 1024**3, 2),
        "used_gb": round(disk.used / 1024**3, 2),
        "free_gb": round(disk.free / 1024**3, 2),
        "percent": disk.percent,
        "read_mb": round(io.read_bytes / 1024**2, 1) if io else None,
        "write_mb": round(io.write_bytes / 1024**2, 1) if io else None,
    }


def get_temperature() -> dict:
    try:
        temps = psutil.sensors_temperatures()
        result = {}
        for chip, entries in temps.items():
            result[chip] = [
                {"label": e.label or f"core{i}", "current": e.current,
                 "high": e.high, "critical": e.critical}
                for i, e in enumerate(entries)
            ]
        return result
    except Exception as e:
        return {"error": str(e)}


def get_network_info() -> dict:
    try:
        # Ping test
        ping = subprocess.run(
            ["ping", "-c", "1", "-W", "2", "8.8.8.8"],
            capture_output=True, text=True, timeout=5
        )
        ping_ok = ping.returncode == 0

        # Get interfaces
        interfaces = {}
        for iface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    interfaces[iface] = addr.address

        # Net IO
        net_io = psutil.net_io_counters()
        return {
            "ping_google": ping_ok,
            "interfaces": interfaces,
            "bytes_sent_mb": round(net_io.bytes_sent / 1024**2, 1),
            "bytes_recv_mb": round(net_io.bytes_recv / 1024**2, 1),
        }
    except Exception as e:
        return {"error": str(e)}


def get_processes(top_n: int = 10) -> list:
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
        try:
            procs.append(p.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    procs.sort(key=lambda x: x.get('cpu_percent', 0) or 0, reverse=True)
    return procs[:top_n]


def get_uptime() -> dict:
    boot_time = psutil.boot_time()
    uptime_seconds = datetime.now().timestamp() - boot_time
    td = timedelta(seconds=int(uptime_seconds))
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return {
        "boot_time": datetime.fromtimestamp(boot_time).strftime("%Y-%m-%d %H:%M"),
        "uptime_seconds": int(uptime_seconds),
        "uptime_human": f"{days}d {hours}h {minutes}m",
    }


def get_battery() -> dict:
    batt = psutil.sensors_battery()
    if not batt:
        return {"available": False}
    secs_left = batt.secsleft
    if secs_left == psutil.POWER_TIME_UNLIMITED:
        time_left = "unlimited (plugged in)"
    elif secs_left == psutil.POWER_TIME_UNKNOWN:
        time_left = "unknown"
    else:
        h, m = divmod(secs_left // 60, 60)
        time_left = f"{h}h {m}m"
    return {
        "available": True,
        "percent": round(batt.percent, 1),
        "power_plugged": batt.power_plugged,
        "time_left": time_left,
    }


def get_active_connections(top_n: int = 20) -> list:
    conns = []
    try:
        for c in psutil.net_connections(kind='inet')[:top_n]:
            try:
                conns.append({
                    "local": f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "-",
                    "remote": f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "-",
                    "status": c.status,
                    "pid": c.pid,
                })
            except Exception:
                pass
    except Exception as e:
        conns.append({"error": str(e)})
    return conns


def full_sysinfo() -> dict:
    return {
        "hostname": platform.node(),
        "os": f"{platform.system()} {platform.release()}",
        "arch": platform.machine(),
        "python": platform.python_version(),
        "cpu": get_cpu_info(),
        "ram": get_ram_info(),
        "disk": get_disk_info(),
        "network": get_network_info(),
        "uptime": get_uptime(),
        "battery": get_battery(),
        "temperature": get_temperature(),
        "top_processes": get_processes(5),
    }


def format_sysinfo(info: dict) -> str:
    lines = [
        f"Host: {info['hostname']}  |  OS: {info['os']}  |  Arch: {info['arch']}",
        "",
        f"CPU:     {info['cpu']['percent']}% used  |  {info['cpu']['count_logical']} cores  |  {info['cpu']['freq_mhz']} MHz",
        f"RAM:     {info['ram']['used_mb']}MB / {info['ram']['total_mb']}MB  ({info['ram']['percent']}%)",
        f"Swap:    {info['ram']['swap_used_mb']}MB / {info['ram']['swap_total_mb']}MB  ({info['ram']['swap_percent']}%)",
        f"Disk:    {info['disk']['used_gb']}GB / {info['disk']['total_gb']}GB  ({info['disk']['percent']}%)",
        f"Uptime:  {info['uptime']['uptime_human']}  (since {info['uptime']['boot_time']})",
        f"Network: {'Online' if info['network'].get('ping_google') else 'Offline'}",
    ]

    batt = info["battery"]
    if batt.get("available"):
        lines.append(f"Battery: {batt['percent']}%  |  {'Charging' if batt['power_plugged'] else 'Discharging'}  |  {batt['time_left']}")

    temps = info["temperature"]
    if temps and "error" not in temps:
        for chip, entries in temps.items():
            for e in entries[:2]:
                lines.append(f"Temp [{chip}/{e['label']}]: {e['current']}°C")

    lines.append("")
    lines.append("Top Processes:")
    for p in info["top_processes"]:
        lines.append(f"  [{p['pid']:>6}] {p['name']:<25} CPU: {p.get('cpu_percent', 0):.1f}%  MEM: {p.get('memory_percent', 0):.1f}%")

    return "\n".join(lines)


if __name__ == "__main__":
    info = full_sysinfo()
    print(format_sysinfo(info))
