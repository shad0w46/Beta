"""Firewall management backend interfacing with UFW and Linux netfilter."""

import re
import shutil
import subprocess
from typing import List, Dict, Optional, Any


class FirewallRule:
    """Represents a single firewall rule in UFW."""

    def __init__(self, number: int, to_destination: str, action: str,
                 from_source: str, comment: str = "", is_v6: bool = False):
        self.number = number
        self.to_destination = to_destination
        self.action = action.strip()
        self.from_source = from_source.strip()
        self.comment = comment.strip()
        self.is_v6 = is_v6

    @property
    def action_type(self) -> str:
        act = self.action.upper()
        if "ALLOW" in act:
            return "allow"
        elif "DENY" in act:
            return "deny"
        elif "REJECT" in act:
            return "reject"
        elif "LIMIT" in act:
            return "limit"
        return "other"

    @property
    def direction(self) -> str:
        act = self.action.upper()
        if "OUT" in act:
            return "OUT"
        return "IN"

    def __repr__(self) -> str:
        return f"<FirewallRule #{self.number} {self.action} {self.to_destination} from {self.from_source}>"


class ListeningSocket:
    """Represents a service actively listening on a network port."""

    def __init__(self, proto: str, local_ip: str, port: int, process: str, pid: Optional[int]):
        self.proto = proto.upper()
        self.local_ip = local_ip
        self.port = port
        self.process = process
        self.pid = pid

    @property
    def is_loopback_only(self) -> bool:
        return self.local_ip in ("127.0.0.1", "::1", "localhost")

    @property
    def display_endpoint(self) -> str:
        return f"{self.local_ip}:{self.port} ({self.proto})"

    def __repr__(self) -> str:
        return f"<ListeningSocket {self.proto} {self.local_ip}:{self.port} [{self.process}]>"


class ApplicationProfile:
    """UFW application profile with port information and metadata."""

    def __init__(self, name: str, title: str = "", description: str = "", ports: str = ""):
        self.name = name
        self.title = title or name
        self.description = description or name
        self.ports = ports

    def __repr__(self) -> str:
        return f"<ApplicationProfile {self.name} ports={self.ports}>"


class FirewallStatus:
    """Complete snapshot of system firewall state."""

    def __init__(self, is_active: bool, default_incoming: str = "deny",
                 default_outgoing: str = "allow", default_routed: str = "disabled",
                 logging: str = "low", rules: Optional[List[FirewallRule]] = None,
                 available_apps: Optional[List[str]] = None, raw_output: str = "",
                 ipv6_enabled: bool = True, ping_allowed: bool = True):
        self.is_active = is_active
        self.default_incoming = default_incoming
        self.default_outgoing = default_outgoing
        self.default_routed = default_routed
        self.logging = logging
        self.rules = rules or []
        self.available_apps = available_apps or []
        self.raw_output = raw_output
        self.ipv6_enabled = ipv6_enabled
        self.ping_allowed = ping_allowed


class FirewallBackend:
    """Provides status queries, socket scanning, and rule management via UFW CLI."""

    @staticmethod
    def is_ufw_installed() -> bool:
        """Check if ufw is installed and executable in PATH or /usr/sbin."""
        return shutil.which("ufw") is not None or shutil.which("/usr/sbin/ufw") is not None

    @staticmethod
    def get_ufw_path() -> str:
        return shutil.which("ufw") or "/usr/sbin/ufw"

    @classmethod
    def get_status(cls) -> FirewallStatus:
        """Query UFW for verbose status, defaults, advanced flags, and numbered rules."""
        ufw_bin = cls.get_ufw_path()

        # 1. Fetch verbose status
        is_active = False
        def_in = "deny"
        def_out = "allow"
        def_routed = "disabled"
        logging = "low"
        raw_text = ""

        try:
            res_verbose = subprocess.run(
                ["sudo", "-n", ufw_bin, "status", "verbose"],
                capture_output=True, text=True, timeout=4
            )
            raw_text = res_verbose.stdout or ""

            if "Status: active" in raw_text:
                is_active = True

            # Parse Default: deny (incoming), allow (outgoing), disabled (routed)
            m_def = re.search(r"Default:\s*([^\n\r]+)", raw_text, re.IGNORECASE)
            if m_def:
                def_line = m_def.group(1).lower()
                m_in = re.search(r"(\w+)\s*\(incoming\)", def_line)
                if m_in: def_in = m_in.group(1)
                m_out = re.search(r"(\w+)\s*\(outgoing\)", def_line)
                if m_out: def_out = m_out.group(1)
                m_routed = re.search(r"(\w+)\s*\(routed\)", def_line)
                if m_routed: def_routed = m_routed.group(1)

            # Parse Logging: on (low)
            m_log = re.search(r"Logging:\s*([^\n\r]+)", raw_text, re.IGNORECASE)
            if m_log:
                logging = m_log.group(1).strip()

        except Exception:
            pass

        # 2. Fetch numbered rules
        rules: List[FirewallRule] = []
        try:
            res_num = subprocess.run(
                ["sudo", "-n", ufw_bin, "status", "numbered"],
                capture_output=True, text=True, timeout=4
            )
            out_num = res_num.stdout or ""

            header_passed = False
            for line in out_num.splitlines():
                if "--" in line and not header_passed:
                    header_passed = True
                    continue

                if not header_passed:
                    continue

                line_str = line.strip()
                if not line_str.startswith("["):
                    continue

                m_rule = re.match(r"^\[\s*(\d+)\]\s+(.+?)\s{2,}(ALLOW IN|DENY IN|REJECT IN|LIMIT IN|ALLOW OUT|DENY OUT|REJECT OUT|LIMIT OUT|ALLOW|DENY|REJECT|LIMIT)\s{2,}(.+)$", line_str, re.IGNORECASE)
                if m_rule:
                    num = int(m_rule.group(1))
                    to_dest = m_rule.group(2).strip()
                    action = m_rule.group(3).strip()
                    rest = m_rule.group(4).strip()

                    comment = ""
                    if "#" in rest:
                        from_src, comment = rest.split("#", 1)
                        from_src = from_src.strip()
                        comment = comment.strip()
                    else:
                        from_src = rest

                    is_v6 = "(v6)" in to_dest or "(v6)" in from_src
                    rules.append(FirewallRule(
                        number=num,
                        to_destination=to_dest,
                        action=action,
                        from_source=from_src,
                        comment=comment,
                        is_v6=is_v6
                    ))

        except Exception:
            pass

        # 3. Available Application Profiles
        apps: List[str] = []
        try:
            res_apps = subprocess.run(
                ["sudo", "-n", ufw_bin, "app", "list"],
                capture_output=True, text=True, timeout=4
            )
            in_list = False
            for line in (res_apps.stdout or "").splitlines():
                if "Available applications:" in line:
                    in_list = True
                    continue
                if in_list and line.strip():
                    apps.append(line.strip())
        except Exception:
            pass

        # 4. Check IPv6 & Ping settings
        ipv6_on = True
        try:
            with open("/etc/default/ufw", "r") as f:
                content = f.read()
                m_ip6 = re.search(r"^IPV6=(\w+)", content, re.MULTILINE)
                if m_ip6 and m_ip6.group(1).lower() in ("no", "0", "false"):
                    ipv6_on = False
        except Exception:
            pass

        ping_on = True
        try:
            res_ping = subprocess.run(
                ["sudo", "-n", "grep", "-q", "echo-request.*ACCEPT", "/etc/ufw/before.rules"],
                capture_output=True, timeout=2
            )
            if res_ping.returncode != 0:
                ping_on = False
        except Exception:
            pass

        return FirewallStatus(
            is_active=is_active,
            default_incoming=def_in,
            default_outgoing=def_out,
            default_routed=def_routed,
            logging=logging,
            rules=rules,
            available_apps=sorted(apps),
            raw_output=raw_text,
            ipv6_enabled=ipv6_on,
            ping_allowed=ping_on
        )

    @classmethod
    def get_listening_sockets(cls) -> List[ListeningSocket]:
        """Scan active TCP and UDP listening sockets via ss."""
        sockets: List[ListeningSocket] = []
        try:
            res = subprocess.run(
                ["sudo", "-n", "ss", "-tulnp"],
                capture_output=True, text=True, timeout=3
            )
            for line in res.stdout.splitlines()[1:]:
                parts = line.split()
                if len(parts) >= 5:
                    proto = parts[0].upper()
                    local = parts[4]
                    if ":" in local:
                        ip, port_str = local.rsplit(":", 1)
                        try:
                            port = int(port_str)
                        except ValueError:
                            continue

                        proc = "Unknown"
                        pid = None
                        if len(parts) >= 7:
                            m = re.search(r'users:\(\(\"([^\"]+)\",pid=(\d+)', parts[6])
                            if m:
                                proc = m.group(1)
                                pid = int(m.group(2))

                        sockets.append(ListeningSocket(
                            proto=proto,
                            local_ip=ip,
                            port=port,
                            process=proc,
                            pid=pid
                        ))
        except Exception:
            pass

        # Sort by port ascending
        return sorted(sockets, key=lambda s: s.port)

    @classmethod
    def get_app_profile_details(cls, app_name: str) -> ApplicationProfile:
        """Query specific application profile details from UFW."""
        ufw_bin = cls.get_ufw_path()
        title = app_name
        desc = ""
        ports = ""
        try:
            res = subprocess.run(
                ["sudo", "-n", ufw_bin, "app", "info", app_name],
                capture_output=True, text=True, timeout=3
            )
            text = res.stdout or ""
            m_t = re.search(r"Title:\s*([^\n\r]+)", text)
            if m_t: title = m_t.group(1).strip()
            m_d = re.search(r"Description:\s*([^\n\r]+)", text)
            if m_d: desc = m_d.group(1).strip()
            m_p = re.search(r"Ports?:\s*([^\n\r]+)", text)
            if m_p: ports = m_p.group(1).strip()
        except Exception:
            pass

        return ApplicationProfile(name=app_name, title=title, description=desc, ports=ports)

    @classmethod
    def get_interface_names(cls) -> List[str]:
        """Detect available network interfaces on the system."""
        interfaces = ["Any Interface"]
        try:
            res = subprocess.run(["ip", "-o", "link", "show"], capture_output=True, text=True, timeout=3)
            for line in res.stdout.splitlines():
                parts = line.split(":", 2)
                if len(parts) >= 2:
                    iface = parts[1].strip()
                    if iface and iface not in interfaces:
                        interfaces.append(iface)
        except Exception:
            pass
        return interfaces

    # Command generators for Runner execution
    @classmethod
    def cmd_enable(cls) -> List[str]:
        return [cls.get_ufw_path(), "--force", "enable"]

    @classmethod
    def cmd_disable(cls) -> List[str]:
        return [cls.get_ufw_path(), "disable"]

    @classmethod
    def cmd_reload(cls) -> List[str]:
        return [cls.get_ufw_path(), "reload"]

    @classmethod
    def cmd_reset(cls) -> List[str]:
        return [cls.get_ufw_path(), "--force", "reset"]

    @classmethod
    def cmd_set_default(cls, direction: str, policy: str) -> List[str]:
        return [cls.get_ufw_path(), "default", policy.lower(), direction.lower()]

    @classmethod
    def cmd_set_logging(cls, level: str) -> List[str]:
        return [cls.get_ufw_path(), "logging", level.lower()]

    @classmethod
    def cmd_delete_rule(cls, rule_number: int) -> List[str]:
        return [cls.get_ufw_path(), "--force", "delete", str(rule_number)]

    @classmethod
    def cmd_set_ipv6(cls, enabled: bool) -> List[str]:
        val = "yes" if enabled else "no"
        return ["/bin/sh", "-c", f"sed -i 's/^IPV6=.*/IPV6={val}/' /etc/default/ufw && {cls.get_ufw_path()} reload"]

    @classmethod
    def cmd_set_ping(cls, allow: bool) -> List[str]:
        target = "ACCEPT" if allow else "DROP"
        return [
            "/bin/sh", "-c",
            f"sed -i '/ufw-before-input.*echo-request/s/-j \\(ACCEPT\\|DROP\\)/-j {target}/' /etc/ufw/before.rules && {cls.get_ufw_path()} reload"
        ]

    @classmethod
    def cmd_set_routed(cls, policy: str) -> List[str]:
        return [cls.get_ufw_path(), "default", policy.lower(), "routed"]

    @classmethod
    def cmd_add_rule(cls, port_or_app: str, action: str = "allow",
                     protocol: str = "any", direction: str = "in",
                     from_ip: str = "any", interface: str = "",
                     comment: str = "") -> List[str]:
        """Construct fine-grained UFW rule command with interface and IP binding."""
        cmd = [cls.get_ufw_path()]

        action = action.lower()
        direction = direction.lower()

        # Check if known application profile
        if "/" not in port_or_app and not port_or_app.isdigit() and " " in port_or_app:
            cmd.extend([action, port_or_app])
            return cmd

        cmd.append(action)
        if direction in ("in", "incoming"):
            cmd.append("in")
        elif direction in ("out", "outgoing"):
            cmd.append("out")

        # Network interface binding
        if interface and interface.lower() not in ("any", "any interface"):
            cmd.extend(["on", interface])

        # Protocol if not 'any'
        proto = protocol.lower()
        if proto in ("tcp", "udp"):
            cmd.extend(["proto", proto])

        # Source IP
        src = from_ip.strip()
        if src and src.lower() not in ("any", "anywhere"):
            cmd.extend(["from", src])
        else:
            cmd.extend(["from", "any"])

        # Destination & Port
        target = port_or_app.strip()
        if target and target.lower() != "any":
            cmd.extend(["to", "any", "port", target])

        if comment.strip():
            cmd.extend(["comment", comment.strip()])

        return cmd
