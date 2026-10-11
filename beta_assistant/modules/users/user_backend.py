"""Backend for Linux user and daemon account management."""

import grp
import os
import pwd
import subprocess
from typing import Dict, List, Optional, Any


class UserInfo:
    def __init__(self, username: str, uid: int, gid: int, comment: str,
                 home_dir: str, shell: str, groups: List[str] = None):
        self.username = username
        self.uid = uid
        self.gid = gid
        self.comment = comment  # Full name or description
        self.home_dir = home_dir
        self.shell = shell
        self.groups = groups or []

    @property
    def is_nologin(self) -> bool:
        """True if user has nologin or false as their login shell."""
        sh = self.shell.lower()
        return sh.endswith("/nologin") or sh.endswith("/false")

    @property
    def is_system(self) -> bool:
        """True if UID < 1000 or username is system reserved (like nobody)."""
        return self.uid < 1000 or self.username == "nobody"

    @property
    def is_standard(self) -> bool:
        """Standard human interactive user."""
        return not self.is_system and not self.is_nologin

    @property
    def account_type_display(self) -> str:
        if self.is_standard:
            return "Standard User"
        elif self.is_nologin and self.is_system:
            return "System Daemon (No-Login)"
        elif self.is_nologin:
            return "No-Login Account"
        elif self.is_system:
            return "System / Daemon"
        return "Custom Account"


class UserBackend:
    """Manages system user accounts, groups, shells, and user creation/deletion."""

    @staticmethod
    def get_all_users() -> List[UserInfo]:
        """Fetch all system users and map their group memberships."""
        # Build map of user -> list of group names
        user_groups_map: Dict[str, List[str]] = {}
        try:
            for g in grp.getgrall():
                for member in g.gr_mem:
                    user_groups_map.setdefault(member, []).append(g.gr_name)
        except Exception:
            pass

        users: List[UserInfo] = []
        try:
            for u in pwd.getpwall():
                user_grps = user_groups_map.get(u.pw_name, [])
                # Also include primary group
                try:
                    prim_grp = grp.getgrgid(u.pw_gid).gr_name
                    if prim_grp not in user_grps:
                        user_grps.insert(0, prim_grp)
                except Exception:
                    pass

                users.append(UserInfo(
                    username=u.pw_name,
                    uid=u.pw_uid,
                    gid=u.pw_gid,
                    comment=u.pw_gecos,
                    home_dir=u.pw_dir,
                    shell=u.pw_shell,
                    groups=user_grps
                ))
        except Exception:
            pass

        # Sort: Standard users first, then by UID
        return sorted(users, key=lambda x: (not x.is_standard, x.uid))

    @staticmethod
    def get_available_shells() -> List[str]:
        """Read valid shells from /etc/shells and common system locations."""
        shells = []
        if os.path.exists("/etc/shells"):
            try:
                with open("/etc/shells", "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            shells.append(line)
            except Exception:
                pass
        for sh in ["/bin/bash", "/bin/sh", "/bin/zsh", "/usr/sbin/nologin", "/bin/false"]:
            if os.path.exists(sh) and sh not in shells:
                shells.append(sh)
        return shells

    @staticmethod
    def get_all_groups() -> List[str]:
        """Get list of all group names."""
        try:
            return sorted([g.gr_name for g in grp.getgrall()])
        except Exception:
            return ["sudo", "adm", "users", "audio", "video", "plugdev", "systemd-journal"]

    # Command generators for Runner
    @staticmethod
    def cmd_create_user(username: str, comment: str = "", shell: str = "/bin/bash",
                        home_dir: str = "", create_home: bool = True,
                        is_system: bool = False, groups: List[str] = None) -> List[str]:
        """Generate command to create user."""
        cmd = ["useradd"]
        if is_system:
            cmd.append("--system")
        if create_home:
            cmd.append("-m")
        else:
            cmd.append("-M")

        if home_dir:
            cmd.extend(["-d", home_dir])
        if shell:
            cmd.extend(["-s", shell])
        if comment:
            cmd.extend(["-c", comment])
        if groups:
            cmd.extend(["-G", ",".join(groups)])

        cmd.append(username)
        return cmd

    @staticmethod
    def cmd_set_password(username: str, password: str) -> List[str]:
        """Generate chpasswd command."""
        return ["sh", "-c", f"echo '{username}:{password}' | chpasswd"]

    @staticmethod
    def cmd_delete_user(username: str, remove_home: bool = False) -> List[str]:
        """Generate userdel command."""
        cmd = ["userdel"]
        if remove_home:
            cmd.append("-r")
        cmd.append(username)
        return cmd

    @staticmethod
    def cmd_lock_user(username: str) -> List[str]:
        return ["usermod", "-L", username]

    @staticmethod
    def cmd_unlock_user(username: str) -> List[str]:
        return ["usermod", "-U", username]

    @staticmethod
    def cmd_change_shell(username: str, new_shell: str) -> List[str]:
        return ["usermod", "-s", new_shell, username]

    @staticmethod
    def cmd_modify_groups(username: str, groups: List[str]) -> List[str]:
        return ["usermod", "-G", ",".join(groups), username]
