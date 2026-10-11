"""Application entry point for Beta Assistant."""

import os
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

from beta_assistant.core.config import (
    APP_NAME, APP_ID, THEME_LIGHT, get_saved_theme, get_setting
)
from beta_assistant.core.module_manager import ModuleManager
from beta_assistant.ui.main_window import MainWindow
from beta_assistant.ui.theme import ALPHAOS_DARK_THEME, ALPHAOS_LIGHT_THEME
from beta_assistant.ui.components.splash_screen import SplashScreen


def main():
    # Wayland / X11 compatibility
    if "QT_QPA_PLATFORM" not in os.environ and "WAYLAND_DISPLAY" in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "wayland;xcb"

    app = QApplication(sys.argv)
    app.setApplicationName("beta-assistant")
    app.setOrganizationName("AlphaOS")
    app.setDesktopFileName("beta-assistant")

    # Apply saved theme (Dark or Light)
    saved_theme = get_saved_theme()
    if saved_theme == THEME_LIGHT:
        app.setStyleSheet(ALPHAOS_LIGHT_THEME)
    else:
        app.setStyleSheet(ALPHAOS_DARK_THEME)

    # Set icon if available
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "alphaos_logo.svg")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Initialize modular engine
    manager = ModuleManager()
    manager.discover_and_load_all()

    # Create main window
    window = MainWindow(manager)

    # Check startup splash animation preference
    enable_anim = bool(get_setting("enable_startup_animation", True))
    if "--no-splash" in sys.argv or os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        enable_anim = False

    if enable_anim:
        # Launch animated splash screen with seamless transition into MainWindow
        splash = SplashScreen(on_finish=window.show_with_animation)
        app._splash = splash
        splash.start_animation()
    else:
        window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
