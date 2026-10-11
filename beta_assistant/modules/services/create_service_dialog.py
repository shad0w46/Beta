"""Modal wizard to design, validate, and install custom systemd services and daemons."""

import os
from typing import Dict, Any, List
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QCheckBox, QTextEdit, QFrame,
    QGroupBox, QMessageBox, QTabWidget, QWidget
)
from PyQt6.QtCore import Qt

from beta_assistant.modules.users.user_backend import UserBackend
from beta_assistant.modules.services.service_backend import ServiceBackend


class CreateServiceDialog(QDialog):
    """Wizard to configure and generate new systemd services and daemons."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Systemd Service / Daemon")
        self.setFixedWidth(580)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Title
        title_label = QLabel("Service & Daemon Creation Wizard")
        title_label.setStyleSheet("font-size: 16px; font-weight: 700; color: #58a6ff;")
        layout.addWidget(title_label)

        desc_label = QLabel("Define a custom background service or daemon with automatic systemd registration.")
        desc_label.setStyleSheet("color: #8b949e; font-size: 12px;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # Tabs: Configuration Form vs Unit File Preview
        self.tabs = QTabWidget()

        # Tab 1: Config
        tab_config = QWidget()
        config_layout = QVBoxLayout(tab_config)
        config_layout.setSpacing(10)

        # General Info
        box_gen = QGroupBox("Service Identity")
        ly_gen = QVBoxLayout(box_gen)
        ly_gen.setSpacing(8)

        # Name
        h_name = QHBoxLayout()
        lbl_name = QLabel("Unit Name:")
        lbl_name.setFixedWidth(120)
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("e.g. custom-worker.service")
        self.input_name.textChanged.connect(self.update_preview)
        h_name.addWidget(lbl_name)
        h_name.addWidget(self.input_name)
        ly_gen.addLayout(h_name)

        # Description
        h_desc = QHBoxLayout()
        lbl_desc = QLabel("Description:")
        lbl_desc.setFixedWidth(120)
        self.input_desc = QLineEdit()
        self.input_desc.setPlaceholderText("e.g. AlphaOS Custom Task Daemon")
        self.input_desc.textChanged.connect(self.update_preview)
        h_desc.addWidget(lbl_desc)
        h_desc.addWidget(self.input_desc)
        ly_gen.addLayout(h_desc)
        config_layout.addWidget(box_gen)

        # Execution Settings
        box_exec = QGroupBox("Execution and Commands")
        ly_exec = QVBoxLayout(box_exec)
        ly_exec.setSpacing(8)

        # ExecStart
        h_start = QHBoxLayout()
        lbl_start = QLabel("ExecStart Command:")
        lbl_start.setFixedWidth(120)
        self.input_exec_start = QLineEdit()
        self.input_exec_start.setPlaceholderText("e.g. /usr/bin/python3 /opt/worker.py")
        self.input_exec_start.textChanged.connect(self.update_preview)
        h_start.addWidget(lbl_start)
        h_start.addWidget(self.input_exec_start)
        ly_exec.addLayout(h_start)

        # Working Dir
        h_workdir = QHBoxLayout()
        lbl_workdir = QLabel("Working Directory:")
        lbl_workdir.setFixedWidth(120)
        self.input_workdir = QLineEdit()
        self.input_workdir.setPlaceholderText("e.g. /opt or /home/zero")
        self.input_workdir.textChanged.connect(self.update_preview)
        h_workdir.addWidget(lbl_workdir)
        h_workdir.addWidget(self.input_workdir)
        ly_exec.addLayout(h_workdir)

        # Service Type & Restart Policy
        h_type_row = QHBoxLayout()
        lbl_type = QLabel("Service Type:")
        lbl_type.setFixedWidth(120)
        self.combo_type = QComboBox()
        self.combo_type.addItems(["simple", "forking", "oneshot", "notify", "idle"])
        self.combo_type.currentIndexChanged.connect(self.update_preview)
        h_type_row.addWidget(lbl_type)
        h_type_row.addWidget(self.combo_type)

        lbl_restart = QLabel("Restart Policy:")
        self.combo_restart = QComboBox()
        self.combo_restart.addItems(["always", "on-failure", "on-abort", "no"])
        self.combo_restart.currentIndexChanged.connect(self.update_preview)
        h_type_row.addWidget(lbl_restart)
        h_type_row.addWidget(self.combo_restart)
        ly_exec.addLayout(h_type_row)
        config_layout.addWidget(box_exec)

        # User & Security
        box_sec = QGroupBox("User Account and Environment")
        ly_sec = QVBoxLayout(box_sec)
        ly_sec.setSpacing(8)

        h_user = QHBoxLayout()
        lbl_u = QLabel("Run as User:")
        lbl_u.setFixedWidth(120)
        self.combo_user = QComboBox()
        self.combo_user.addItem("root (Root Administrator)")
        # Load all system users
        users = UserBackend.get_all_users()
        for u in users:
            if u.username != "root":
                role_label = "Daemon" if u.is_system else "Standard"
                self.combo_user.addItem(f"{u.username} ({role_label})", u.username)
        self.combo_user.currentIndexChanged.connect(self.update_preview)
        h_user.addWidget(lbl_u)
        h_user.addWidget(self.combo_user)
        ly_sec.addLayout(h_user)

        # Environment Variables
        h_env = QHBoxLayout()
        lbl_env = QLabel("Environment:")
        lbl_env.setFixedWidth(120)
        self.input_env = QLineEdit()
        self.input_env.setPlaceholderText("VAR1=value VAR2=value")
        self.input_env.textChanged.connect(self.update_preview)
        h_env.addWidget(lbl_env)
        h_env.addWidget(self.input_env)
        ly_sec.addLayout(h_env)
        config_layout.addWidget(box_sec)

        # Options
        self.check_enable = QCheckBox("Enable service to start automatically on system boot")
        self.check_enable.setChecked(True)
        config_layout.addWidget(self.check_enable)

        self.check_start = QCheckBox("Start service immediately after creation")
        self.check_start.setChecked(True)
        config_layout.addWidget(self.check_start)

        self.tabs.addTab(tab_config, "Configuration")

        # Tab 2: Preview
        tab_preview = QWidget()
        preview_layout = QVBoxLayout(tab_preview)
        self.unit_preview = QTextEdit()
        self.unit_preview.setReadOnly(True)
        self.unit_preview.setStyleSheet("font-family: monospace; font-size: 12px; background-color: #05070a;")
        preview_layout.addWidget(self.unit_preview)
        self.tabs.addTab(tab_preview, "Unit File Preview (.service)")

        layout.addWidget(self.tabs)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_create = QPushButton("Create && Register Service")
        self.btn_create.setProperty("class", "btn-primary")
        self.btn_create.clicked.connect(self.validate_and_accept)
        btn_layout.addWidget(self.btn_create)

        layout.addLayout(btn_layout)

        self.update_preview()

    def get_selected_username(self) -> str:
        idx = self.combo_user.currentIndex()
        if idx == 0:
            return "root"
        return self.combo_user.itemData(idx) or self.combo_user.currentText().split()[0]

    def update_preview(self):
        name = self.input_name.text().strip()
        if name and not name.endswith(".service"):
            name += ".service"

        desc = self.input_desc.text().strip()
        exec_start = self.input_exec_start.text().strip() or "/usr/bin/echo 'Service running'"
        stype = self.combo_type.currentText()
        restart = self.combo_restart.currentText()
        user = self.get_selected_username()
        workdir = self.input_workdir.text().strip()
        env_raw = self.input_env.text().strip()

        unit_text = ServiceBackend.generate_unit_file_content(
            description=desc,
            exec_start=exec_start,
            service_type=stype,
            working_dir=workdir,
            user=user if user != "root" else "",
            restart=restart,
            env_vars=env_raw
        )
        self.unit_preview.setPlainText(unit_text)

    def validate_and_accept(self):
        name = self.input_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Invalid Name", "Please enter a valid unit name.")
            return

        if not self.input_exec_start.text().strip():
            QMessageBox.warning(self, "Missing ExecStart", "Please provide the command (ExecStart) to run.")
            return

        self.accept()

    def get_service_data(self) -> Dict[str, Any]:
        name = self.input_name.text().strip()
        if not name.endswith(".service"):
            name += ".service"

        return {
            "name": name,
            "unit_content": self.unit_preview.toPlainText(),
            "enable": self.check_enable.isChecked(),
            "start": self.check_start.isChecked()
        }
