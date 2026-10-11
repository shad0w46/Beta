"""Backend for systemd service and daemon management."""

import os
import re
import subprocess
from typing import Dict, List, Optional, Any


class ServiceInfo:
    def __init__(self, name: str, load_state: str, active_state: str,
                 sub_state: str, description: str, enabled_state: str = "unknown"):
        self.name = name
        self.load_state = load_state
        self.active_state = active_state
        self.sub_state = sub_state
        self.description = description
        self.enabled_state = enabled_state

    @property
    def is_active(self) -> bool:
        return self.active_state == "active"

    @property
    def is_failed(self) -> bool:
        return self.active_state == "failed"

    @property
    def is_enabled(self) -> bool:
        return self.enabled_state == "enabled"

    @property
    def status_display(self) -> str:
        if self.is_failed:
            return "Failed"
        if self.is_active:
            return "Running" if self.sub_state == "running" else "Active"
        return "Inactive"


class ServiceBackend:
    """Manages systemd unit listing, inspection, status logs, and unit file creation."""

    @staticmethod
    def get_all_services() -> List[ServiceInfo]:
        """Fetch all systemd services with active/sub state and description."""
        services: List[ServiceInfo] = []
        try:
            cmd = ["systemctl", "list-units", "--type=service", "--all", "--no-legend", "--no-pager"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            for line in res.stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                # Remove leading bullet symbol if present
                if line.startswith("●"):
                    line = line[1:].strip()

                # Typically columns are: UNIT LOAD ACTIVE SUB DESCRIPTION...
                parts = line.split(None, 4)
                if len(parts) >= 4:
                    unit_name = parts[0]
                    load_state = parts[1]
                    active_state = parts[2]
                    sub_state = parts[3]
                    desc = parts[4] if len(parts) > 4 else ""

                    if unit_name.endswith(".service"):
                        services.append(ServiceInfo(
                            name=unit_name,
                            load_state=load_state,
                            active_state=active_state,
                            sub_state=sub_state,
                            description=desc
                        ))
        except Exception:
            pass

        # Sort: Failed first, then Active, then Inactive
        def sort_key(s: ServiceInfo):
            prio = 2
            if s.is_failed:
                prio = 0
            elif s.is_active:
                prio = 1
            return (prio, s.name.lower())

        return sorted(services, key=sort_key)

    @staticmethod
    def get_service_details(service_name: str) -> Dict[str, str]:
        """Fetch systemctl show properties for a specific service."""
        details = {
            "name": service_name,
            "MainPID": "0",
            "ActiveState": "unknown",
            "SubState": "unknown",
            "Description": "",
            "FragmentPath": "",
            "UnitFileState": "unknown",
            "MemoryCurrent": "0",
            "ActiveEnterTimestamp": "N/A"
        }
        try:
            cmd = [
                "systemctl", "show", service_name,
                "-p", "MainPID",
                "-p", "ActiveState",
                "-p", "SubState",
                "-p", "Description",
                "-p", "FragmentPath",
                "-p", "UnitFileState",
                "-p", "MemoryCurrent",
                "-p", "ActiveEnterTimestamp",
                "--no-pager"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=4)
            for line in res.stdout.splitlines():
                if "=" in line:
                    k, v = line.split("=", 1)
                    details[k.strip()] = v.strip()
        except Exception:
            pass
        return details

    @staticmethod
    def get_service_logs(service_name: str, lines: int = 50) -> str:
        """Fetch latest journalctl logs for a service."""
        try:
            cmd = ["journalctl", "-u", service_name, "-n", str(lines), "--no-pager"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=4)
            return res.stdout if res.stdout else "No log entries found for this service."
        except Exception as e:
            return f"Error retrieving logs: {e}"

    @staticmethod
    def generate_unit_file_content(description: str, exec_start: str,
                                   service_type: str = "simple",
                                   working_dir: str = "",
                                   user: str = "",
                                   group: str = "",
                                   restart: str = "always",
                                   restart_sec: str = "5s",
                                   env_vars: str = "",
                                   exec_stop: str = "") -> str:
        """Generates validated systemd unit file content."""
        lines = [
            "[Unit]",
            f"Description={description or 'AlphaOS Custom Service'}",
            "After=network.target",
            "",
            "[Service]",
            f"Type={service_type or 'simple'}",
            f"ExecStart={exec_start}"
        ]

        if exec_stop:
            lines.append(f"ExecStop={exec_stop}")
        if working_dir:
            lines.append(f"WorkingDirectory={working_dir}")
        if user:
            lines.append(f"User={user}")
        if group:
            lines.append(f"Group={group}")
        if restart:
            lines.append(f"Restart={restart}")
            if restart_sec:
                lines.append(f"RestartSec={restart_sec}")

        if env_vars:
            for env_line in env_vars.strip().splitlines():
                env_line = env_line.strip()
                if env_line and "=" in env_line:
                    lines.append(f"Environment=\"{env_line}\"")

        lines.extend([
            "",
            "[Install]",
            "WantedBy=multi-user.target",
            ""
        ])

        return "\n".join(lines)

    # Command generators for Runner
    @staticmethod
    def cmd_start(service_name: str) -> List[str]:
        return ["systemctl", "start", service_name]

    @staticmethod
    def cmd_stop(service_name: str) -> List[str]:
        return ["systemctl", "stop", service_name]

    @staticmethod
    def cmd_restart(service_name: str) -> List[str]:
        return ["systemctl", "restart", service_name]

    @staticmethod
    def cmd_reload(service_name: str) -> List[str]:
        return ["systemctl", "reload", service_name]

    @staticmethod
    def cmd_enable(service_name: str) -> List[str]:
        return ["systemctl", "enable", service_name]

    @staticmethod
    def cmd_disable(service_name: str) -> List[str]:
        return ["systemctl", "disable", service_name]

    @staticmethod
    def cmd_mask(service_name: str) -> List[str]:
        return ["systemctl", "mask", service_name]

    @staticmethod
    def cmd_unmask(service_name: str) -> List[str]:
        return ["systemctl", "unmask", service_name]

    @staticmethod
    def cmd_daemon_reload() -> List[str]:
        return ["systemctl", "daemon-reload"]
