"""Unit tests for AlphaOS Beta Assistant backends."""

import unittest
from beta_assistant.core.system_info import get_os_release, get_system_metrics
from beta_assistant.modules.packages.apt_backend import AptBackend
from beta_assistant.modules.users.user_backend import UserBackend
from beta_assistant.modules.services.service_backend import ServiceBackend


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


if __name__ == "__main__":
    unittest.main()
