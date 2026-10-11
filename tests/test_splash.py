"""Unit tests for SplashScreen and startup animation sequence."""

import os
import unittest
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from beta_assistant.ui.components.splash_screen import SplashScreen
from beta_assistant.core.config import get_setting, set_setting


app = QApplication.instance() or QApplication([])


class TestSplashScreen(unittest.TestCase):
    """Test suite for animated splash screen and startup lifecycle."""

    def test_splash_initialization(self):
        splash = SplashScreen()
        self.assertIsNotNone(splash)
        self.assertEqual(splash.width(), 540)
        self.assertEqual(splash.height(), 360)
        self.assertEqual(splash.progress_value, 0)
        self.assertGreater(len(splash.MILESTONES), 0)

    def test_splash_milestone_progression(self):
        callback_fired = []
        splash = SplashScreen(on_finish=lambda: callback_fired.append(True))
        self.assertFalse(splash.is_closing)

        # Advance progress manually
        splash._advance_progress()
        self.assertGreater(splash.progress_value, 0)

        # Force finish
        splash.finish_splash()
        self.assertTrue(splash.is_closing)

    def test_startup_animation_config(self):
        self.assertTrue(get_setting("enable_startup_animation", True))


if __name__ == "__main__":
    unittest.main()
