"""Main application window hosting modular views, navigation, and terminal drawer."""

import os
from typing import Dict, Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QFrame, QButtonGroup, QMessageBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap

from beta_assistant.core.config import APP_NAME, APP_SUBTITLE, APP_VERSION
from beta_assistant.core.module_base import BaseModule
from beta_assistant.core.module_manager import ModuleManager
from beta_assistant.core.system_info import get_os_release
from beta_assistant.ui.components.terminal_drawer import TerminalDrawer
from beta_assistant.ui.components.badges import StatusBadge


class MainWindow(QMainWindow):
    """Main window orchestrator for Beta_Assistant."""

    def __init__(self, module_manager: ModuleManager):
        super().__init__()
        self.module_manager = module_manager
        self.module_buttons: Dict[str, QPushButton] = {}
        self.module_badges: Dict[str, QLabel] = {}
        self.module_widgets: Dict[str, QWidget] = {}

        self.setWindowTitle(f"{APP_NAME} - {APP_SUBTITLE}")
        self.resize(1180, 780)
        self.setMinimumSize(960, 640)

        # Connect context for modules to trigger tab switches
        self.module_manager.set_app_context({
            "switch_tab": self.switch_to_module,
            "main_window": self
        })

        self.init_ui()
        self.load_modules()

    def init_ui(self):
        # Central widget container
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Top Header Bar
        top_header = QFrame()
        top_header.setObjectName("top_header")
        th_layout = QHBoxLayout(top_header)
        th_layout.setContentsMargins(16, 10, 16, 10)

        # Title & Distro Name
        os_info = get_os_release()
        distro_str = os_info.get("PRETTY_NAME", "AlphaOS Linux")

        header_title = QLabel(APP_NAME)
        header_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #58a6ff;")

        header_badge = StatusBadge(f"{distro_str} v{APP_VERSION}", "installed")

        th_layout.addWidget(header_title)
        th_layout.addSpacing(8)
        th_layout.addWidget(header_badge)
        th_layout.addStretch()

        # Terminal toggle button
        self.btn_toggle_terminal = QPushButton("💻 Toggle Console Drawer")
        self.btn_toggle_terminal.clicked.connect(self.toggle_terminal_drawer)
        th_layout.addWidget(self.btn_toggle_terminal)

        # Global Refresh button
        btn_refresh = QPushButton("⟳ Refresh")
        btn_refresh.clicked.connect(self.refresh_current_view)
        th_layout.addWidget(btn_refresh)

        root_layout.addWidget(top_header)

        # 2. Main Work Area (Sidebar + Stacked Content)
        content_frame = QFrame()
        content_layout = QHBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(10, 14, 10, 14)
        self.sidebar_layout.setSpacing(6)

        # Sidebar Header / Section
        lbl_nav = QLabel("MODULES")
        lbl_nav.setStyleSheet("color: #6e7681; font-size: 11px; font-weight: 700; margin-left: 6px; margin-bottom: 4px;")
        self.sidebar_layout.addWidget(lbl_nav)

        self.nav_button_group = QButtonGroup(self)
        self.nav_button_group.setExclusive(True)

        content_layout.addWidget(self.sidebar)

        # Stacked Pages
        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack, stretch=1)

        root_layout.addWidget(content_frame, stretch=1)

        # 3. Bottom Terminal Drawer
        self.terminal_drawer = TerminalDrawer(self)
        self.terminal_drawer.hide() # Hidden by default until command is triggered
        root_layout.addWidget(self.terminal_drawer)

    def load_modules(self):
        """Build dynamic sidebar and stack entries for each discovered module."""
        modules = self.module_manager.get_all_modules()

        icon_map = {
            "dashboard": "📊",
            "packages": "📦",
            "users": "👤",
            "services": "⚙️"
        }

        for idx, mod in enumerate(modules):
            # Create navigation button with icon and escaped ampersand
            icon_symbol = icon_map.get(mod.module_id, "🔧")
            display_title = mod.title.replace("&", "&&")
            btn = QPushButton(f"{icon_symbol}  {display_title}")
            btn.setProperty("class", "nav-btn")
            btn.setCheckable(True)
            btn.setFixedHeight(40)

            # Container with optional badge for count
            h_btn_box = QHBoxLayout()
            h_btn_box.setContentsMargins(0, 0, 0, 0)

            badge = QLabel("")
            badge.setStyleSheet("""
                QLabel {
                    background-color: #d29922;
                    color: #0d1117;
                    font-size: 10px;
                    font-weight: 700;
                    border-radius: 8px;
                    padding: 1px 6px;
                }
            """)
            badge.hide()
            self.module_badges[mod.module_id] = badge

            # Layout for button content
            btn_ly = QHBoxLayout(btn)
            btn_ly.setContentsMargins(10, 0, 10, 0)
            btn_ly.addStretch()
            btn_ly.addWidget(badge)

            # Connect button click
            m_id = mod.module_id
            btn.clicked.connect(lambda checked, mid=m_id: self.switch_to_module(mid))

            self.nav_button_group.addButton(btn, idx)
            self.sidebar_layout.addWidget(btn)
            self.module_buttons[mod.module_id] = btn

            # Create module view widget and add to stacked widget
            widget = mod.get_widget()
            self.stack.addWidget(widget)
            self.module_widgets[mod.module_id] = widget

            # Connect module signals
            mod.request_command.connect(self.on_module_request_command)
            mod.badge_updated.connect(self.on_module_badge_updated)
            mod.show_notification.connect(self.on_module_notification)

        self.sidebar_layout.addStretch()

        # Add About / Version Info at bottom of sidebar
        lbl_foot = QLabel("AlphaOS • Modular Engine")
        lbl_foot.setStyleSheet("color: #484f58; font-size: 11px; margin-left: 6px;")
        self.sidebar_layout.addWidget(lbl_foot)

        # Select first module by default
        if modules:
            self.switch_to_module(modules[0].module_id)

    def switch_to_module(self, module_id: str):
        """Switch active view to specified module."""
        if module_id in self.module_buttons and module_id in self.module_widgets:
            self.module_buttons[module_id].setChecked(True)
            self.stack.setCurrentWidget(self.module_widgets[module_id])
            mod = self.module_manager.get_module(module_id)
            if mod:
                mod.on_activated()

    def on_module_badge_updated(self, module_id: str, badge_text: str):
        badge = self.module_badges.get(module_id)
        if badge:
            if badge_text:
                badge.setText(badge_text)
                badge.show()
            else:
                badge.hide()

    def on_module_request_command(self, cmd: list, as_root: bool, title: str, callback: object):
        """Route module command requests to the live streaming terminal drawer."""
        self.terminal_drawer.show()
        self.terminal_drawer.execute_command(
            cmd=cmd,
            as_root=as_root,
            title=title,
            callback=callback
        )

    def on_module_notification(self, title: str, message: str):
        QMessageBox.information(self, title, message)

    def toggle_terminal_drawer(self):
        if self.terminal_drawer.isVisible():
            self.terminal_drawer.hide()
        else:
            self.terminal_drawer.show()

    def refresh_current_view(self):
        # Refresh current active module
        curr_widget = self.stack.currentWidget()
        for mod in self.module_manager.get_all_modules():
            if mod.get_widget() == curr_widget:
                mod.refresh()
                break
