"""Unit tests for modular engine, module manager, and all 6 modules."""

import os
import unittest
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication
from beta_assistant.core.module_manager import ModuleManager
from beta_assistant.modules.dashboard import DashboardModule
from beta_assistant.modules.packages import PackagesModule
from beta_assistant.modules.storage import StorageModule
from beta_assistant.modules.users import UsersModule
from beta_assistant.modules.services import ServicesModule
from beta_assistant.modules.logs import LogsModule


class TestModules(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_module_manager_discovery(self):
        manager = ModuleManager()
        manager.discover_and_load_all()
        modules = manager.get_all_modules()

        mod_ids = [m.module_id for m in modules]
        self.assertEqual(len(mod_ids), 6)
        self.assertIn("dashboard", mod_ids)
        self.assertIn("packages", mod_ids)
        self.assertIn("storage", mod_ids)
        self.assertIn("users", mod_ids)
        self.assertIn("services", mod_ids)
        self.assertIn("logs", mod_ids)

        # Priority order verification
        self.assertEqual(mod_ids, ["dashboard", "packages", "users", "storage", "services", "logs"])

    def test_module_widgets_instantiation(self):
        manager = ModuleManager()
        manager.discover_and_load_all()

        for mod in manager.get_all_modules():
            widget = mod.get_widget()
            self.assertIsNotNone(widget)


if __name__ == "__main__":
    unittest.main()
