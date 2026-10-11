"""Boot analysis and system journal diagnostics backend."""

import re
import subprocess
from typing import Dict, List, Any


class BlameItem:
    def __init__(self, service: str, duration_str: str, duration_ms: int):
        self.service = service
        self.duration_str = duration_str
        self.duration_ms = duration_ms

    @property
    def impact_level(self) -> str:
        if self.duration_ms >= 2000:
            return "high"
        elif self.duration_ms >= 500:
            return "medium"
        return "low"


class LogsBackend:
    """Queries systemd boot metrics and journal logs."""

    @staticmethod
    def get_boot_times() -> Dict[str, str]:
        """Parse systemd-analyze boot times."""
        data = {
            "firmware": "N/A",
            "loader": "N/A",
            "kernel": "N/A",
            "userspace": "N/A",
            "total": "N/A"
        }
        try:
            res = subprocess.run(["systemd-analyze"], capture_output=True, text=True, timeout=4)
            line = res.stdout.strip().splitlines()[0] if res.stdout else ""

            # Example: "Startup finished in 8.739s (firmware) + 6.285s (loader) + 6.181s (kernel) + 2.000s (userspace) = 23.206s"
            fw = re.search(r'([\d\.]+(?:s|ms))\s*\(firmware\)', line)
            if fw: data["firmware"] = fw.group(1)

            loader = re.search(r'([\d\.]+(?:s|ms))\s*\(loader\)', line)
            if loader: data["loader"] = loader.group(1)

            kern = re.search(r'([\d\.]+(?:s|ms))\s*\(kernel\)', line)
            if kern: data["kernel"] = kern.group(1)

            user = re.search(r'([\d\.]+(?:s|ms))\s*\(userspace\)', line)
            if user: data["userspace"] = user.group(1)

            tot = re.search(r'=\s*([\d\.]+(?:s|ms))', line)
            if tot: data["total"] = tot.group(1)

        except Exception:
            pass
        return data

    @staticmethod
    def get_boot_blame(limit: int = 50) -> List[BlameItem]:
        """Parse systemd-analyze blame output."""
        items: List[BlameItem] = []
        try:
            res = subprocess.run(["systemd-analyze", "blame"], capture_output=True, text=True, timeout=5)
            for line in res.stdout.splitlines()[:limit]:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(None, 1)
                if len(parts) == 2:
                    dur_str = parts[0]
                    svc = parts[1]

                    ms = 0
                    if dur_str.endswith("ms"):
                        try: ms = int(float(dur_str[:-2]))
                        except Exception: pass
                    elif dur_str.endswith("s"):
                        try: ms = int(float(dur_str[:-1]) * 1000)
                        except Exception: pass
                    elif dur_str.endswith("min"):
                        try: ms = int(float(dur_str[:-3]) * 60000)
                        except Exception: pass

                    items.append(BlameItem(service=svc, duration_str=dur_str, duration_ms=ms))
        except Exception:
            pass
        return items

    @staticmethod
    def query_journal(priority: str = "warning", lines: int = 80, query: str = "") -> str:
        """Fetch filtered journalctl entries."""
        try:
            cmd = ["journalctl", "-p", priority, "-n", str(lines), "--no-pager"]
            if query:
                cmd.extend(["-g", query])
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return res.stdout if res.stdout else "No log messages found for this filter."
        except Exception as e:
            return f"Error retrieving journal: {e}"
