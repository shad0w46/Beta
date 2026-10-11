"""Storage analysis and system junk cleaner backend."""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Any
import psutil


class MountInfo:
    def __init__(self, device: str, mountpoint: str, fstype: str,
                 total_gb: float, used_gb: float, free_gb: float, percent: float):
        self.device = device
        self.mountpoint = mountpoint
        self.fstype = fstype
        self.total_gb = total_gb
        self.used_gb = used_gb
        self.free_gb = free_gb
        self.percent = percent


class StorageBackend:
    """Provides disk partition inspections and junk space calculations."""

    @staticmethod
    def get_mounted_partitions() -> List[MountInfo]:
        """Fetch all primary physical mounted filesystems."""
        partitions: List[MountInfo] = []
        seen = set()

        for p in psutil.disk_partitions(all=False):
            # Skip snap, loop, squashfs, and virtual pseudo filesystems
            if p.mountpoint in seen or "loop" in p.device or p.fstype in ("squashfs", "tmpfs", "devtmpfs", "overlay"):
                continue

            seen.add(p.mountpoint)
            try:
                usage = psutil.disk_usage(p.mountpoint)
                total_gb = round(usage.total / (1024 ** 3), 1)
                used_gb = round(usage.used / (1024 ** 3), 1)
                free_gb = round(usage.free / (1024 ** 3), 1)
                pct = round(usage.percent, 1)

                partitions.append(MountInfo(
                    device=p.device,
                    mountpoint=p.mountpoint,
                    fstype=p.fstype,
                    total_gb=total_gb,
                    used_gb=used_gb,
                    free_gb=free_gb,
                    percent=pct
                ))
            except Exception:
                pass

        return sorted(partitions, key=lambda m: m.mountpoint)

    @staticmethod
    def scan_junk_sizes() -> Dict[str, Any]:
        """Calculate cleanable junk sizes across common system caches."""
        # 1. APT Cache
        apt_cache_bytes = 0
        apt_dir = Path("/var/cache/apt/archives")
        if apt_dir.exists():
            try:
                for f in apt_dir.glob("*.deb"):
                    apt_cache_bytes += f.stat().st_size
            except Exception:
                pass

        # 2. Thumbnail Cache
        thumb_bytes = 0
        thumb_dir = Path.home() / ".cache" / "thumbnails"
        if thumb_dir.exists():
            try:
                for root, _, files in os.walk(thumb_dir):
                    for f in files:
                        thumb_bytes += os.path.getsize(os.path.join(root, f))
            except Exception:
                pass

        # 3. Systemd Journal Size
        journal_bytes = 0
        try:
            res = subprocess.run(["journalctl", "--disk-usage"], capture_output=True, text=True, timeout=3)
            # Parses line like "Archived and active journals take up 21.1M in the file system."
            for token in res.stdout.split():
                if token.endswith("M"):
                    try:
                        journal_bytes = int(float(token[:-1]) * 1024 * 1024)
                        break
                    except Exception:
                        pass
                elif token.endswith("G"):
                    try:
                        journal_bytes = int(float(token[:-1]) * 1024 * 1024 * 1024)
                        break
                    except Exception:
                        pass
        except Exception:
            pass

        def fmt(b: int) -> str:
            if b <= 0:
                return "0 MB"
            if b < 1024 * 1024:
                return f"{b / 1024:.1f} KB"
            elif b < 1024 * 1024 * 1024:
                return f"{b / (1024 * 1024):.1f} MB"
            else:
                return f"{b / (1024 ** 3):.2f} GB"

        total_cleanable = apt_cache_bytes + thumb_bytes + max(0, journal_bytes - 15 * 1024 * 1024)

        return {
            "apt_bytes": apt_cache_bytes,
            "apt_display": fmt(apt_cache_bytes),
            "thumb_bytes": thumb_bytes,
            "thumb_display": fmt(thumb_bytes),
            "journal_bytes": journal_bytes,
            "journal_display": fmt(journal_bytes),
            "total_bytes": total_cleanable,
            "total_display": fmt(total_cleanable)
        }

    # Command generators for Runner
    @staticmethod
    def cmd_clean_apt() -> List[str]:
        return ["apt-get", "clean"]

    @staticmethod
    def cmd_vacuum_journal() -> List[str]:
        return ["journalctl", "--vacuum-time=3d"]

    @staticmethod
    def cmd_autoremove() -> List[str]:
        return ["apt-get", "autoremove", "--purge", "-y"]

    @staticmethod
    def cmd_clean_all() -> List[str]:
        # Clean APT archives, vacuum journal, and autoremove
        return ["sh", "-c", "apt-get clean && journalctl --vacuum-time=3d && rm -rf ~/.cache/thumbnails/* && apt-get autoremove -y"]
