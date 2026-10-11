"""Modal dialog for creating Standard, Daemon, and No-Login users."""

import os
from typing import Dict, Any, List
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QRadioButton, QButtonGroup, QCheckBox,
    QComboBox, QFrame, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt

from beta_assistant.modules.users.user_backend import UserBackend


class CreateUserDialog(QDialog):
    """Wizard/form dialog to create standard, system daemon, and no-login users."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New User / Daemon Account")
        self.setFixedWidth(520)
        self.available_shells = UserBackend.get_available_shells()
        self.common_groups = ["sudo", "adm", "users", "audio", "video", "plugdev", "systemd-journal", "docker"]
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Title
        title_label = QLabel("New User Account Wizard")
        title_label.setStyleSheet("font-size: 16px; font-weight: 700; color: #58a6ff;")
        layout.addWidget(title_label)

        desc_label = QLabel("Configure standard users, background daemons, or restricted no-login service accounts.")
        desc_label.setStyleSheet("color: #8b949e; font-size: 12px;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # Account Type Selector Box
        type_box = QGroupBox("Account Purpose and Type")
        type_layout = QVBoxLayout(type_box)
        type_layout.setSpacing(8)

        self.btn_group = QButtonGroup(self)
        self.radio_standard = QRadioButton("Standard User (Interactive desktop/shell account with home folder)")
        self.radio_daemon = QRadioButton("System Daemon (Dedicated non-human service account, UID < 1000)")
        self.radio_nologin = QRadioButton("No-Login User (Restricted account with /usr/sbin/nologin shell)")

        self.btn_group.addButton(self.radio_standard, 1)
        self.btn_group.addButton(self.radio_daemon, 2)
        self.btn_group.addButton(self.radio_nologin, 3)

        self.radio_standard.setChecked(True)
        type_layout.addWidget(self.radio_standard)
        type_layout.addWidget(self.radio_daemon)
        type_layout.addWidget(self.radio_nologin)
        layout.addWidget(type_box)

        # User Credentials Box
        cred_box = QGroupBox("User Identification")
        cred_layout = QVBoxLayout(cred_box)
        cred_layout.setSpacing(8)

        # Username
        h_user = QHBoxLayout()
        lbl_user = QLabel("Username:")
        lbl_user.setFixedWidth(100)
        self.input_username = QLineEdit()
        self.input_username.setPlaceholderText("e.g. devuser or nginx-svc")
        self.input_username.textChanged.connect(self.on_username_changed)
        h_user.addWidget(lbl_user)
        h_user.addWidget(self.input_username)
        cred_layout.addLayout(h_user)

        # Full Name / Comment
        h_comment = QHBoxLayout()
        lbl_comment = QLabel("Description / Name:")
        lbl_comment.setFixedWidth(100)
        self.input_comment = QLineEdit()
        self.input_comment.setPlaceholderText("e.g. John Doe or Web Application Service")
        self.input_comment.textChanged.connect(self.update_command_preview)
        h_comment.addWidget(lbl_comment)
        h_comment.addWidget(self.input_comment)
        cred_layout.addLayout(h_comment)

        # Password (for standard users)
        self.h_pass = QHBoxLayout()
        lbl_pass = QLabel("Password:")
        lbl_pass.setFixedWidth(100)
        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password.setPlaceholderText("Optional initial password")
        self.h_pass.addWidget(lbl_pass)
        self.h_pass.addWidget(self.input_password)
        cred_layout.addLayout(self.h_pass)

        layout.addWidget(cred_box)

        # Environment & Shell Box
        env_box = QGroupBox("Environment and Permissions")
        env_layout = QVBoxLayout(env_box)
        env_layout.setSpacing(8)

        # Shell
        h_shell = QHBoxLayout()
        lbl_shell = QLabel("Login Shell:")
        lbl_shell.setFixedWidth(100)
        self.combo_shell = QComboBox()
        self.combo_shell.addItems(self.available_shells)
        if "/bin/bash" in self.available_shells:
            self.combo_shell.setCurrentText("/bin/bash")
        self.combo_shell.currentIndexChanged.connect(self.update_command_preview)
        h_shell.addWidget(lbl_shell)
        h_shell.addWidget(self.combo_shell)
        env_layout.addLayout(h_shell)

        # Home Directory
        h_home = QHBoxLayout()
        lbl_home = QLabel("Home Directory:")
        lbl_home.setFixedWidth(100)
        self.input_home = QLineEdit()
        self.input_home.textChanged.connect(self.update_command_preview)
        h_home.addWidget(lbl_home)
        h_home.addWidget(self.input_home)
        env_layout.addLayout(h_home)

        # Checkbox Create Home
        self.check_create_home = QCheckBox("Create Home Directory on Disk")
        self.check_create_home.setChecked(True)
        self.check_create_home.stateChanged.connect(self.update_command_preview)
        env_layout.addWidget(self.check_create_home)

        # Group Memberships
        grp_label = QLabel("Supplementary Groups:")
        grp_label.setStyleSheet("color: #8b949e; font-size: 11px; margin-top: 4px;")
        env_layout.addWidget(grp_label)

        self.group_checkboxes: Dict[str, QCheckBox] = {}
        h_groups = QHBoxLayout()
        for g in self.common_groups[:4]:
            cb = QCheckBox(g)
            cb.stateChanged.connect(self.update_command_preview)
            self.group_checkboxes[g] = cb
            h_groups.addWidget(cb)
        env_layout.addLayout(h_groups)

        h_groups2 = QHBoxLayout()
        for g in self.common_groups[4:]:
            cb = QCheckBox(g)
            cb.stateChanged.connect(self.update_command_preview)
            self.group_checkboxes[g] = cb
            h_groups2.addWidget(cb)
        env_layout.addLayout(h_groups2)

        layout.addWidget(env_box)

        # Command Preview Label
        lbl_preview = QLabel("Generated CLI Command:")
        lbl_preview.setStyleSheet("color: #8b949e; font-size: 11px;")
        layout.addWidget(lbl_preview)

        self.preview_cmd = QLineEdit()
        self.preview_cmd.setReadOnly(True)
        self.preview_cmd.setStyleSheet("background-color: #0d1117; color: #58a6ff; font-family: monospace; font-size: 11px;")
        layout.addWidget(self.preview_cmd)

        # Dialog Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_create = QPushButton("Create Account")
        self.btn_create.setProperty("class", "btn-primary")
        self.btn_create.clicked.connect(self.validate_and_accept)
        btn_layout.addWidget(self.btn_create)

        layout.addLayout(btn_layout)

        # Connect radio buttons
        self.btn_group.idClicked.connect(self.on_type_changed)
        self.update_command_preview()

    def on_username_changed(self, text: str):
        uname = text.strip()
        if self.radio_standard.isChecked():
            self.input_home.setText(f"/home/{uname}" if uname else "")
        elif self.radio_daemon.isChecked():
            self.input_home.setText(f"/var/lib/{uname}" if uname else "")
        self.update_command_preview()

    def on_type_changed(self, btn_id: int):
        uname = self.input_username.text().strip()

        if btn_id == 1: # Standard
            self.combo_shell.setEnabled(True)
            if "/bin/bash" in self.available_shells:
                self.combo_shell.setCurrentText("/bin/bash")
            self.input_home.setText(f"/home/{uname}" if uname else "")
            self.check_create_home.setChecked(True)
            self.input_password.setEnabled(True)
            # enable group checkboxes
            for cb in self.group_checkboxes.values():
                cb.setEnabled(True)

        elif btn_id == 2: # Daemon
            # Default nologin or false for daemon
            nologin_shell = "/usr/sbin/nologin" if "/usr/sbin/nologin" in self.available_shells else "/bin/false"
            if nologin_shell in self.available_shells:
                self.combo_shell.setCurrentText(nologin_shell)
            self.input_home.setText(f"/var/lib/{uname}" if uname else "")
            self.check_create_home.setChecked(False)
            self.input_password.clear()
            self.input_password.setEnabled(False)
            for cb in self.group_checkboxes.values():
                cb.setChecked(False)
                cb.setEnabled(False)

        elif btn_id == 3: # No-login
            nologin_shell = "/usr/sbin/nologin" if "/usr/sbin/nologin" in self.available_shells else "/bin/false"
            if nologin_shell in self.available_shells:
                self.combo_shell.setCurrentText(nologin_shell)
            self.combo_shell.setEnabled(False)
            self.check_create_home.setChecked(False)
            self.input_password.clear()
            self.input_password.setEnabled(False)
            for cb in self.group_checkboxes.values():
                cb.setChecked(False)
                cb.setEnabled(False)

        self.update_command_preview()

    def get_selected_groups(self) -> List[str]:
        return [g for g, cb in self.group_checkboxes.items() if cb.isChecked() and cb.isEnabled()]

    def update_command_preview(self):
        uname = self.input_username.text().strip() or "<username>"
        comment = self.input_comment.text().strip()
        shell = self.combo_shell.currentText()
        home = self.input_home.text().strip()
        create_home = self.check_create_home.isChecked()
        is_system = self.radio_daemon.isChecked()
        groups = self.get_selected_groups()

        cmd = UserBackend.cmd_create_user(
            username=uname,
            comment=comment,
            shell=shell,
            home_dir=home,
            create_home=create_home,
            is_system=is_system,
            groups=groups
        )
        self.preview_cmd.setText("sudo " + " ".join(cmd))

    def validate_and_accept(self):
        uname = self.input_username.text().strip()
        if not uname:
            QMessageBox.warning(self, "Invalid Username", "Please enter a valid username.")
            return

        if not uname.replace("-", "").replace("_", "").isalnum():
            QMessageBox.warning(self, "Invalid Username", "Username should only contain alphanumeric characters, hyphens, and underscores.")
            return

        self.accept()

    def get_creation_data(self) -> Dict[str, Any]:
        return {
            "username": self.input_username.text().strip(),
            "comment": self.input_comment.text().strip(),
            "shell": self.combo_shell.currentText(),
            "home": self.input_home.text().strip(),
            "create_home": self.check_create_home.isChecked(),
            "is_system": self.radio_daemon.isChecked(),
            "is_nologin": self.radio_nologin.isChecked(),
            "password": self.input_password.text(),
            "groups": self.get_selected_groups()
        }
