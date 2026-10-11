"""Application entry point for Beta Assistant."""

import os
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

from beta_assistant.core.config import APP_NAME, APP_ID, THEME_LIGHT, get_saved_theme
from beta_assistant.core.module_manager import ModuleManager
from beta_assistant.ui.main_window import MainWindow
from beta_assistant.ui.theme import ALPHAOS_DARK_THEME, ALPHAOS_LIGHT_THEME


def main():
    # Wayland / X11 compatibility
    if "QT_QPA_PLATFORM" not in os.environ and "WAYLAND_DISPLAY" in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "wayland;xcb"

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("AlphaOS")
    app.setDesktopFileName(f"{APP_ID}.desktop")

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

    # Create and present main window
    window = MainWindow(manager)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
