"""Unit tests for AlphaOS Beta Assistant backends."""

import unittest
from beta_assistant.core.system_info import get_os_release, get_system_metrics
from beta_assistant.modules.packages.apt_backend import AptBackend
from beta_assistant.modules.users.user_backend import UserBackend
from beta_assistant.modules.services.service_backend import ServiceBackend


from beta_assistant.modules.storage.storage_backend import StorageBackend
from beta_assistant.modules.logs.logs_backend import LogsBackend
from beta_assistant.modules.firewall.firewall_backend import FirewallBackend


class TestBackends(unittest.TestCase):

    def test_os_release(self):
        info = get_os_release()
        self.assertIsInstance(info, dict)
        self.assertEqual(info.get("ID"), "alphaos")

    def test_system_metrics(self):
        metrics = get_system_metrics()
        self.assertIn("cpu_percent", metrics)
        self.assertIn("mem_percent", metrics)
        self.assertIn("disk_percent", metrics)
        self.assertGreaterEqual(metrics["cpu_count"], 1)

    def test_apt_backend_commands(self):
        self.assertEqual(AptBackend.cmd_update(), ["apt-get", "update"])
        self.assertEqual(AptBackend.cmd_upgrade(), ["apt-get", "upgrade", "-y"])
        self.assertEqual(AptBackend.cmd_install("htop"), ["apt-get", "install", "-y", "htop"])
        self.assertEqual(AptBackend.cmd_remove("htop"), ["apt-get", "remove", "-y", "htop"])

    def test_user_backend_listing(self):
        users = UserBackend.get_all_users()
        self.assertGreater(len(users), 0)
        # Check standard user exists (e.g., zero)
        usernames = [u.username for u in users]
        self.assertIn("root", usernames)
        self.assertIn("zero", usernames)

    def test_user_backend_creation_cmd(self):
        cmd_std = UserBackend.cmd_create_user(
            username="alex",
            comment="Alex Standard",
            shell="/bin/bash",
            home_dir="/home/alex",
            create_home=True,
            is_system=False,
            groups=["sudo", "audio"]
        )
        self.assertIn("useradd", cmd_std)
        self.assertIn("-m", cmd_std)
        self.assertIn("-s", cmd_std)
        self.assertIn("/bin/bash", cmd_std)
        self.assertIn("alex", cmd_std)

        # Daemon user command with nologin
        cmd_daemon = UserBackend.cmd_create_user(
            username="my-daemon",
            comment="Telemetry Daemon",
            shell="/usr/sbin/nologin",
            home_dir="/var/lib/my-daemon",
            create_home=False,
            is_system=True
        )
        self.assertIn("--system", cmd_daemon)
        self.assertIn("-M", cmd_daemon)
        self.assertIn("/usr/sbin/nologin", cmd_daemon)

    def test_service_backend_unit_generation(self):
        content = ServiceBackend.generate_unit_file_content(
            description="Alpha Telemetry Daemon",
            exec_start="/usr/bin/python3 /opt/telemetry.py",
            service_type="simple",
            user="telemetry-user",
            restart="always"
        )
        self.assertIn("[Unit]", content)
        self.assertIn("Description=Alpha Telemetry Daemon", content)
        self.assertIn("[Service]", content)
        self.assertIn("ExecStart=/usr/bin/python3 /opt/telemetry.py", content)
        self.assertIn("User=telemetry-user", content)
        self.assertIn("Restart=always", content)
        self.assertIn("[Install]", content)
        self.assertIn("WantedBy=multi-user.target", content)

    def test_storage_backend(self):
        parts = StorageBackend.get_mounted_partitions()
        self.assertIsInstance(parts, list)
        self.assertGreater(len(parts), 0)
        root_part = next((p for p in parts if p.mountpoint == "/"), None)
        self.assertIsNotNone(root_part)
        self.assertGreater(root_part.total_gb, 0)

        junk = StorageBackend.scan_junk_sizes()
        self.assertIn("apt_bytes", junk)
        self.assertIn("total_display", junk)

        self.assertEqual(StorageBackend.cmd_clean_apt(), ["apt-get", "clean"])
        self.assertIn("journalctl", StorageBackend.cmd_vacuum_journal()[0])

    def test_logs_backend(self):
        boot_times = LogsBackend.get_boot_times()
        self.assertIn("kernel", boot_times)
        self.assertIn("total", boot_times)

        blame = LogsBackend.get_boot_blame(limit=10)
        self.assertIsInstance(blame, list)
        if blame:
            self.assertTrue(hasattr(blame[0], "service"))
            self.assertTrue(hasattr(blame[0], "duration_ms"))
            self.assertIn(blame[0].impact_level, ["high", "medium", "low"])

    def test_firewall_backend(self):
        self.assertTrue(FirewallBackend.is_ufw_installed())
        status = FirewallBackend.get_status()
        self.assertIsInstance(status.is_active, bool)
        self.assertIn(status.default_incoming, ["deny", "allow", "reject"])
        self.assertIn(status.default_outgoing, ["allow", "deny", "reject"])
        self.assertIsInstance(status.available_apps, list)

        cmd_add = FirewallBackend.cmd_add_rule(
            port_or_app="8080",
            action="allow",
            protocol="tcp",
            direction="in",
            from_ip="192.168.1.0/24",
            comment="Dev Port"
        )
        self.assertIn("allow", cmd_add)
        self.assertIn("8080", cmd_add)
        self.assertIn("192.168.1.0/24", cmd_add)


if __name__ == "__main__":
    unittest.main()

