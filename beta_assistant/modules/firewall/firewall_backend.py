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


class FirewallStatus:
    """Complete snapshot of system firewall state."""

    def __init__(self, is_active: bool, default_incoming: str = "deny",
                 default_outgoing: str = "allow", default_routed: str = "disabled",
                 logging: str = "low", rules: Optional[List[FirewallRule]] = None,
                 available_apps: Optional[List[str]] = None, raw_output: str = ""):
        self.is_active = is_active
        self.default_incoming = default_incoming
        self.default_outgoing = default_outgoing
        self.default_routed = default_routed
        self.logging = logging
        self.rules = rules or []
        self.available_apps = available_apps or []
        self.raw_output = raw_output


class FirewallBackend:
    """Provides status queries and rule management via UFW CLI."""

    @staticmethod
    def is_ufw_installed() -> bool:
        """Check if ufw is installed and executable in PATH or /usr/sbin."""
        return shutil.which("ufw") is not None or shutil.which("/usr/sbin/ufw") is not None

    @staticmethod
    def get_ufw_path() -> str:
        return shutil.which("ufw") or "/usr/sbin/ufw"

    @classmethod
    def get_status(cls) -> FirewallStatus:
        """Query UFW for verbose status, defaults, and numbered rules."""
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

            # Rules appear after the header line "-- -- --"
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

                # Pattern: [ 1] 22/tcp ALLOW IN Anywhere # comment
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

        return FirewallStatus(
            is_active=is_active,
            default_incoming=def_in,
            default_outgoing=def_out,
            default_routed=def_routed,
            logging=logging,
            rules=rules,
            available_apps=sorted(apps),
            raw_output=raw_text
        )

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
        # ufw default <allow|deny|reject> <incoming|outgoing|routed>
        return [cls.get_ufw_path(), "default", policy.lower(), direction.lower()]

    @classmethod
    def cmd_set_logging(cls, level: str) -> List[str]:
        return [cls.get_ufw_path(), "logging", level.lower()]

    @classmethod
    def cmd_delete_rule(cls, rule_number: int) -> List[str]:
        return [cls.get_ufw_path(), "--force", "delete", str(rule_number)]

    @classmethod
    def cmd_add_rule(cls, port_or_app: str, action: str = "allow",
                     protocol: str = "any", direction: str = "in",
                     from_ip: str = "any", comment: str = "") -> List[str]:
        """Construct full UFW command for fine-grained rule addition."""
        cmd = [cls.get_ufw_path()]

        action = action.lower()
        direction = direction.lower()

        # If it's a known application profile
        if "/" not in port_or_app and not port_or_app.isdigit() and " " in port_or_app:
            cmd.extend([action, port_or_app])
            return cmd

        # Standard rule with direction & protocol
        cmd.append(action)
        if direction in ("in", "incoming"):
            cmd.append("in")
        elif direction in ("out", "outgoing"):
            cmd.append("out")

        # Protocol if not 'any'
        proto = protocol.lower()
        if proto in ("tcp", "udp"):
            cmd.extend(["proto", proto])

        # Source IP
        src = from_ip.strip()
        if src and src.lower() != "any" and src.lower() != "anywhere":
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
