"""Comprehensive Application Settings & Preferences Dialog for Beta Assistant."""

import os
import shutil
import subprocess
from typing import Dict, Any, Callable, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QCheckBox, QTabWidget, QWidget, QFrame,
    QMessageBox, QScrollArea, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal

from beta_assistant.core.config import (
    APP_NAME, APP_VERSION, APP_SUBTITLE, DEFAULT_SETTINGS,
    CONFIG_DIR, LOG_DIR, THEME_DARK, THEME_LIGHT,
    load_all_settings, save_all_settings, get_setting, set_setting, save_theme
)
from beta_assistant.core.system_info import get_os_release
from beta_assistant.ui.theme import ALPHAOS_DARK_THEME, ALPHAOS_LIGHT_THEME
from beta_assistant.ui.components.badges import StatusBadge


class SettingsDialog(QDialog):
    """Modern multi-tab preferences modal for customizing Beta Assistant."""

    settings_applied = pyqtSignal()

    def __init__(self, current_theme: str = THEME_DARK, on_theme_change: Optional[Callable[[str], None]] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings & Preferences - Beta Assistant")
        self.setFixedSize(680, 550)
        self.setModal(True)

        self.current_theme = current_theme
        self.on_theme_change = on_theme_change
        self.settings = load_all_settings()

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 18, 20, 18)
        main_layout.setSpacing(14)

        # Header
        head_layout = QHBoxLayout()
        v_head = QVBoxLayout()
        lbl_head = QLabel("Preferences & System Settings")
        lbl_head.setStyleSheet("font-size: 17px; font-weight: 800; color: #58a6ff;")
        lbl_sub = QLabel("Configure AlphaOS administration defaults, interface behavior, and telemetry.")
        lbl_sub.setStyleSheet("color: #8b949e; font-size: 12px;")
        v_head.addWidget(lbl_head)
        v_head.addWidget(lbl_sub)
        head_layout.addLayout(v_head)
        head_layout.addStretch()

        badge_distro = StatusBadge("AlphaOS", "installed")
        head_layout.addWidget(badge_distro)
        main_layout.addLayout(head_layout)

        # Tabs
        self.tabs = QTabWidget()
        self.tab_general = QWidget()
        self.tab_telemetry = QWidget()
        self.tab_safety = QWidget()
        self.tab_about = QWidget()

        self.setup_general_tab()
        self.setup_telemetry_tab()
        self.setup_safety_tab()
        self.setup_about_tab()

        self.tabs.addTab(self.tab_general, "🎨 Appearance")
        self.tabs.addTab(self.tab_telemetry, "⚡ Telemetry")
        self.tabs.addTab(self.tab_safety, "🛡️ Safeguards")
        self.tabs.addTab(self.tab_about, "ℹ️ System Info")
        main_layout.addWidget(self.tabs)

        # Bottom Buttons
        btn_box = QHBoxLayout()
        btn_reset_all = QPushButton("Reset to Defaults")
        btn_reset_all.setStyleSheet("color: #8b949e; font-size: 12px;")
        btn_reset_all.clicked.connect(self.action_reset_defaults)
        btn_box.addWidget(btn_reset_all)

        btn_box.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_save = QPushButton("Save Preferences")
        btn_save.setProperty("class", "btn-primary")
        btn_save.clicked.connect(self.action_save)
        btn_box.addWidget(btn_save)

        main_layout.addLayout(btn_box)

    # -------------------------------------------------------------
    # Tab 1: Appearance & UI
    # -------------------------------------------------------------
    def setup_general_tab(self):
        layout = QVBoxLayout(self.tab_general)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Theme selection
        f_theme = QFrame()
        f_theme.setProperty("class", "card")
        l_th = QVBoxLayout(f_theme)
        l_th.setContentsMargins(14, 12, 14, 12)
        l_th.setSpacing(6)

        lbl_th_title = QLabel("Application Theme")
        lbl_th_title.setStyleSheet("font-weight: 700; color: #58a6ff;")
        lbl_th_sub = QLabel("Select between AlphaOS dark glassmorphism or high-contrast light theme.")
        lbl_th_sub.setStyleSheet("color: #8b949e; font-size: 11px;")
        l_th.addWidget(lbl_th_title)
        l_th.addWidget(lbl_th_sub)

        self.combo_theme = QComboBox()
        self.combo_theme.addItems(["🌙 Dark Mode (Default)", "☀️ Light Mode"])
        if self.current_theme == THEME_LIGHT:
            self.combo_theme.setCurrentIndex(1)
        else:
            self.combo_theme.setCurrentIndex(0)
        l_th.addWidget(self.combo_theme)
        layout.addWidget(f_theme)

        # Default Startup Module
        f_startup = QFrame()
        f_startup.setProperty("class", "card")
        l_st = QVBoxLayout(f_startup)
        l_st.setContentsMargins(14, 12, 14, 12)
        l_st.setSpacing(6)

        lbl_st_title = QLabel("Default Startup View")
        lbl_st_title.setStyleSheet("font-weight: 700; color: #58a6ff;")
        lbl_st_sub = QLabel("Select which module loads automatically when opening Beta Assistant.")
        lbl_st_sub.setStyleSheet("color: #8b949e; font-size: 11px;")
        l_st.addWidget(lbl_st_title)
        l_st.addWidget(lbl_st_sub)

        self.combo_default_module = QComboBox()
        self.module_ids = [
            ("dashboard", "📊 System Dashboard"),
            ("packages", "📦 Package Manager (APT)"),
            ("storage", "🧹 Storage & Cleaner"),
            ("users", "👤 Users & Groups"),
            ("services", "⚙️ Service & Daemon Manager"),
            ("firewall", "🛡️ Network Firewall (UFW)"),
            ("logs", "🔍 System Logs & Journal")
        ]
        for mid, mlabel in self.module_ids:
            self.combo_default_module.addItem(mlabel, mid)

        curr_def = self.settings.get("default_module", "dashboard")
        for i, (mid, _) in enumerate(self.module_ids):
            if mid == curr_def:
                self.combo_default_module.setCurrentIndex(i)
                break
        l_st.addWidget(self.combo_default_module)
        layout.addWidget(f_startup)

        # Compact Sidebar Toggle
        self.chk_compact_sidebar = QCheckBox("Enable Compact Sidebar (Icon-Only Mode)")
        self.chk_compact_sidebar.setChecked(bool(self.settings.get("compact_sidebar", False)))
        layout.addWidget(self.chk_compact_sidebar)

        # Startup Animation Toggle
        self.chk_startup_anim = QCheckBox("Show Animated Splash Screen on Application Startup")
        self.chk_startup_anim.setChecked(bool(self.settings.get("enable_startup_animation", True)))
        layout.addWidget(self.chk_startup_anim)

        layout.addStretch()

    # -------------------------------------------------------------
    # Tab 2: Telemetry & Drawer
    # -------------------------------------------------------------
    def setup_telemetry_tab(self):
        layout = QVBoxLayout(self.tab_telemetry)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Metrics refresh rate
        f_tele = QFrame()
        f_tele.setProperty("class", "card")
        l_te = QVBoxLayout(f_tele)
        l_te.setContentsMargins(14, 12, 14, 12)
        l_te.setSpacing(6)

        lbl_te_title = QLabel("Hardware Telemetry Poll Rate")
        lbl_te_title.setStyleSheet("font-weight: 700; color: #58a6ff;")
        lbl_te_sub = QLabel("Controls how frequently CPU, RAM, and Disk metrics refresh on the Dashboard.")
        lbl_te_sub.setStyleSheet("color: #8b949e; font-size: 11px;")
        l_te.addWidget(lbl_te_title)
        l_te.addWidget(lbl_te_sub)

        self.combo_refresh_rate = QComboBox()
        self.refresh_rates = [
            (1, "Fast (Every 1 second)"),
            (2, "Balanced (Every 2 seconds)"),
            (3, "Standard (Every 3 seconds - Default)"),
            (5, "Battery Saver (Every 5 seconds)"),
            (10, "Low Power (Every 10 seconds)")
        ]
        curr_rate = int(self.settings.get("auto_refresh_seconds", 3))
        selected_idx = 2
        for i, (secs, label) in enumerate(self.refresh_rates):
            self.combo_refresh_rate.addItem(label, secs)
            if secs == curr_rate:
                selected_idx = i
        self.combo_refresh_rate.setCurrentIndex(selected_idx)
        l_te.addWidget(self.combo_refresh_rate)
        layout.addWidget(f_tele)

        # Auto-open console drawer
        f_drawer = QFrame()
        f_drawer.setProperty("class", "card")
        l_dr = QVBoxLayout(f_drawer)
        l_dr.setContentsMargins(14, 12, 14, 12)
        l_dr.setSpacing(8)

        lbl_dr_title = QLabel("Terminal Console Drawer Automation")
        lbl_dr_title.setStyleSheet("font-weight: 700; color: #58a6ff;")

        self.chk_auto_drawer = QCheckBox("Automatically slide open Console Drawer when executing root actions")
        self.chk_auto_drawer.setChecked(bool(self.settings.get("auto_open_terminal", True)))
        l_dr.addWidget(lbl_dr_title)
        l_dr.addWidget(self.chk_auto_drawer)

        lbl_dr_hint = QLabel("When enabled, real-time output from apt, systemctl, and ufw commands will be displayed automatically.")
        lbl_dr_hint.setStyleSheet("color: #8b949e; font-size: 11px;")
        l_dr.addWidget(lbl_dr_hint)
        layout.addWidget(f_drawer)

        layout.addStretch()

    # -------------------------------------------------------------
    # Tab 3: Safety & Confirmations
    # -------------------------------------------------------------
    def setup_safety_tab(self):
        layout = QVBoxLayout(self.tab_safety)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        f_safe = QFrame()
        f_safe.setProperty("class", "card")
        l_sf = QVBoxLayout(f_safe)
        l_sf.setContentsMargins(14, 12, 14, 12)
        l_sf.setSpacing(10)

        lbl_sf_title = QLabel("Dangerous Actions Safeguards")
        lbl_sf_title.setStyleSheet("font-weight: 700; color: #58a6ff;")
        l_sf.addWidget(lbl_sf_title)

        self.chk_confirm_critical = QCheckBox("Require confirmation dialogs for critical system operations")
        self.chk_confirm_critical.setChecked(bool(self.settings.get("confirm_critical_actions", True)))
        l_sf.addWidget(self.chk_confirm_critical)

        lbl_sf_desc = QLabel(
            "Protects against accidental actions:\n"
            "• Stopping critical systemd background services\n"
            "• Deleting user accounts and user home directories\n"
            "• Wiping and resetting firewall netfilter rules\n"
            "• Purging system package packages via APT"
        )
        lbl_sf_desc.setStyleSheet("color: #8b949e; font-size: 11px; line-height: 1.4;")
        l_sf.addWidget(lbl_sf_desc)
        layout.addWidget(f_safe)

        # Cache & Log Directory Operations
        f_cache = QFrame()
        f_cache.setProperty("class", "card")
        l_cc = QVBoxLayout(f_cache)
        l_cc.setContentsMargins(14, 12, 14, 12)
        l_cc.setSpacing(8)

        lbl_cc_title = QLabel("Data & Storage Maintenance")
        lbl_cc_title.setStyleSheet("font-weight: 700; color: #58a6ff;")
        l_cc.addWidget(lbl_cc_title)

        b_row = QHBoxLayout()
        btn_open_cfg = QPushButton("📁 Open Config Folder")
        btn_open_cfg.clicked.connect(self.action_open_config_folder)
        b_row.addWidget(btn_open_cfg)

        btn_clear_logs = QPushButton("🧹 Clear Log History")
        btn_clear_logs.clicked.connect(self.action_clear_logs)
        b_row.addWidget(btn_clear_logs)

        l_cc.addLayout(b_row)
        layout.addWidget(f_cache)

        layout.addStretch()

    # -------------------------------------------------------------
    # Tab 4: System & About
    # -------------------------------------------------------------
    def setup_about_tab(self):
        layout = QVBoxLayout(self.tab_about)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        os_info = get_os_release()
        distro_name = os_info.get("NAME", "AlphaOS")
        version_id = os_info.get("VERSION_ID", "Rolling")
        kernel_ver = "Unknown"
        try:
            kernel_ver = subprocess.check_output(["uname", "-r"], text=True).strip()
        except Exception:
            pass

        # App card
        card_app = QFrame()
        card_app.setProperty("class", "card-elevated")
        c_layout = QVBoxLayout(card_app)
        c_layout.setContentsMargins(16, 14, 16, 14)
        c_layout.setSpacing(6)

        lbl_aname = QLabel(f"{APP_NAME} v{APP_VERSION}")
        lbl_aname.setStyleSheet("font-size: 16px; font-weight: 800; color: #58a6ff;")
        lbl_asub = QLabel(APP_SUBTITLE)
        lbl_asub.setStyleSheet("color: #8b949e; font-size: 12px;")
        c_layout.addWidget(lbl_aname)
        c_layout.addWidget(lbl_asub)
        layout.addWidget(card_app)

        # Specs info
        info_lines = [
            ("Operating System:", f"{distro_name} ({version_id})"),
            ("Linux Kernel:", kernel_ver),
            ("Build System:", "Meson & Ninja Native Debian Package"),
            ("License:", "GNU General Public License v3.0 (GPL-3.0)"),
            ("Repository:", "https://github.com/shad0w46/Beta"),
            ("Config Directory:", str(CONFIG_DIR)),
        ]

        f_info = QFrame()
        f_info.setProperty("class", "card")
        l_inf = QVBoxLayout(f_info)
        l_inf.setContentsMargins(14, 12, 14, 12)
        l_inf.setSpacing(6)

        for label, val in info_lines:
            row = QHBoxLayout()
            lbl_k = QLabel(label)
            lbl_k.setStyleSheet("color: #8b949e; font-weight: 600; min-width: 140px;")
            lbl_v = QLabel(val)
            lbl_v.setStyleSheet("color: #c9d1d9;")
            lbl_v.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            row.addWidget(lbl_k)
            row.addWidget(lbl_v)
            row.addStretch()
            l_inf.addLayout(row)

        layout.addWidget(f_info)
        layout.addStretch()

    # -------------------------------------------------------------
    # Actions
    # -------------------------------------------------------------
    def action_save(self):
        theme_idx = self.combo_theme.currentIndex()
        chosen_theme = THEME_LIGHT if theme_idx == 1 else THEME_DARK
        save_theme(chosen_theme)

        def_mod = self.combo_default_module.currentData() or "dashboard"
        set_setting("default_module", def_mod)

        refresh_sec = self.combo_refresh_rate.currentData() or 3
        set_setting("auto_refresh_seconds", refresh_sec)

        set_setting("auto_open_terminal", self.chk_auto_drawer.isChecked())
        set_setting("confirm_critical_actions", self.chk_confirm_critical.isChecked())
        set_setting("compact_sidebar", self.chk_compact_sidebar.isChecked())
        set_setting("enable_startup_animation", self.chk_startup_anim.isChecked())

        if self.on_theme_change and chosen_theme != self.current_theme:
            self.on_theme_change(chosen_theme)

        self.settings_applied.emit()
        self.accept()

    def action_reset_defaults(self):
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to restore all application settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            save_all_settings(dict(DEFAULT_SETTINGS))
            self.settings = dict(DEFAULT_SETTINGS)
            self.combo_theme.setCurrentIndex(0)
            self.combo_default_module.setCurrentIndex(0)
            self.combo_refresh_rate.setCurrentIndex(2)
            self.chk_auto_drawer.setChecked(True)
            self.chk_confirm_critical.setChecked(True)
            self.chk_compact_sidebar.setChecked(False)
            self.chk_startup_anim.setChecked(True)
            if self.on_theme_change:
                self.on_theme_change(THEME_DARK)
            self.settings_applied.emit()

    def action_open_config_folder(self):
        try:
            subprocess.Popen(["xdg-open", str(CONFIG_DIR)])
        except Exception:
            QMessageBox.information(self, "Config Path", f"Config path: {CONFIG_DIR}")

    def action_clear_logs(self):
        try:
            if LOG_DIR.exists():
                for item in LOG_DIR.iterdir():
                    if item.is_file():
                        item.unlink()
            QMessageBox.information(self, "Logs Cleared", "Application log history cleared successfully.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not clear logs: {e}")
