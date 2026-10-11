"""System information and diagnostic telemetry for AlphaOS."""

import os
import platform
import subprocess
import time
from typing import Dict, Any, List
import psutil


def get_os_release() -> Dict[str, str]:
    """Parse /etc/os-release into a dictionary."""
    data = {}
    if os.path.exists("/etc/os-release"):
        try:
            with open("/etc/os-release", "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        data[k.strip()] = v.strip().strip('"').strip("'")
        except Exception:
            pass
    return data


def get_uptime_str() -> str:
    """Return formatted system uptime."""
    try:
        boot_time = psutil.boot_time()
        uptime_secs = int(time.time() - boot_time)
        hours, remainder = divmod(uptime_secs, 3600)
        minutes, _ = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        return f"{hours}h {minutes}m"
    except Exception:
        return "Unknown"


def get_system_metrics() -> Dict[str, Any]:
    """Get real-time CPU, RAM, and Disk metrics."""
    try:
        cpu_pct = psutil.cpu_percent(interval=None)
        cpu_count = psutil.cpu_count(logical=True)

        mem = psutil.virtual_memory()
        mem_pct = mem.percent
        mem_used_gb = round(mem.used / (1024 ** 3), 2)
        mem_total_gb = round(mem.total / (1024 ** 3), 2)

        disk = psutil.disk_usage("/")
        disk_pct = disk.percent
        disk_used_gb = round(disk.used / (1024 ** 3), 1)
        disk_total_gb = round(disk.total / (1024 ** 3), 1)

        return {
            "cpu_percent": cpu_pct,
            "cpu_count": cpu_count,
            "mem_percent": mem_pct,
            "mem_used_gb": mem_used_gb,
            "mem_total_gb": mem_total_gb,
            "disk_percent": disk_pct,
            "disk_used_gb": disk_used_gb,
            "disk_total_gb": disk_total_gb,
        }
    except Exception as e:
        return {
            "cpu_percent": 0.0,
            "cpu_count": 1,
            "mem_percent": 0.0,
            "mem_used_gb": 0.0,
            "mem_total_gb": 0.0,
            "disk_percent": 0.0,
            "disk_used_gb": 0.0,
            "disk_total_gb": 0.0,
            "error": str(e)
        }


def get_failed_services() -> List[str]:
    """Retrieve list of currently failed systemd services."""
    try:
        res = subprocess.run(
            ["systemctl", "--failed", "--type=service", "--no-legend", "--no-pager"],
            capture_output=True,
            text=True,
            timeout=3
        )
        failed = []
        for line in res.stdout.splitlines():
            line = line.strip()
            if line:
                parts = line.split()
                # parts[0] might be bullet '●', parts[1] is service name
                svc_name = parts[1] if parts[0] == "●" and len(parts) > 1 else parts[0]
                if svc_name.endswith(".service"):
                    failed.append(svc_name)
        return failed
    except Exception:
        return []


def count_upgradable_packages() -> int:
    """Quick count of upgradable packages using apt."""
    try:
        import apt
        cache = apt.Cache()
        count = 0
        for pkg in cache:
            if pkg.is_upgradable:
                count += 1
        return count
    except Exception:
        # Fallback to apt list --upgradable
        try:
            res = subprocess.run(
                ["apt", "list", "--upgradable"],
                capture_output=True,
                text=True,
                timeout=4
            )
            lines = [l for l in res.stdout.splitlines() if "/" in l]
            return len(lines)
        except Exception:
            return 0
