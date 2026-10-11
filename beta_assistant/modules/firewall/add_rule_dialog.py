"""Interactive modal dialog for creating custom and preset firewall rules."""

from typing import List, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QRadioButton, QButtonGroup,
    QFrame, QMessageBox
)
from PyQt6.QtCore import Qt

from beta_assistant.modules.firewall.firewall_backend import FirewallBackend


class AddRuleDialog(QDialog):
    """Wizard for adding individual ports, ranges, or application profiles to UFW."""

    PRESETS = [
        {"name": "SSH (22)", "port": "22", "proto": "tcp", "desc": "Secure Shell Access"},
        {"name": "HTTP (80)", "port": "80", "proto": "tcp", "desc": "Web Server Traffic"},
        {"name": "HTTPS (443)", "port": "443", "proto": "tcp", "desc": "Encrypted Web Traffic"},
        {"name": "DNS (53)", "port": "53", "proto": "any", "desc": "Domain Name System"},
        {"name": "FTP (21)", "port": "21", "proto": "tcp", "desc": "File Transfer Protocol"},
        {"name": "MySQL (3306)", "port": "3306", "proto": "tcp", "desc": "MySQL / MariaDB Database"},
        {"name": "Postgres (5432)", "port": "5432", "proto": "tcp", "desc": "PostgreSQL Database"},
    ]

    def __init__(self, available_apps: Optional[List[str]] = None, parent=None):
        super().__init__(parent)
        self.available_apps = available_apps or []
        self.setWindowTitle("Add Firewall Rule - AlphaOS")
        self.setFixedWidth(540)
        self.setModal(True)

        self.generated_command: List[str] = []

        self.init_ui()
        self.update_command_preview()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header
        lbl_head = QLabel("Configure New Firewall Rule")
        lbl_head.setStyleSheet("font-size: 16px; font-weight: 700; color: #58a6ff;")
        lbl_sub = QLabel("Open or restrict network access for specific ports, protocols, or IP ranges.")
        lbl_sub.setStyleSheet("color: #8b949e; font-size: 12px;")
        layout.addWidget(lbl_head)
        layout.addWidget(lbl_sub)

        # 1. Quick Presets Bar
        preset_frame = QFrame()
        preset_frame.setStyleSheet("background-color: rgba(33, 38, 45, 0.6); border-radius: 6px; padding: 6px;")
        p_layout = QVBoxLayout(preset_frame)
        p_layout.setContentsMargins(8, 6, 8, 6)
        p_layout.setSpacing(6)

        lbl_presets = QLabel("Quick Presets:")
        lbl_presets.setStyleSheet("font-size: 11px; font-weight: 600; color: #c9d1d9;")
        p_layout.addWidget(lbl_presets)

        p_buttons = QHBoxLayout()
        p_buttons.setSpacing(6)
        for p in self.PRESETS[:5]:
            btn = QPushButton(p["name"])
            btn.setFixedHeight(26)
            btn.setStyleSheet("font-size: 11px; padding: 2px 6px;")
            btn.clicked.connect(lambda checked, preset=p: self.apply_preset(preset))
            p_buttons.addWidget(btn)
        p_layout.addLayout(p_buttons)
        layout.addWidget(preset_frame)

        # 2. Rule Type: Port vs Application Profile
        type_layout = QHBoxLayout()
        self.radio_port = QRadioButton("Custom Port / Range")
        self.radio_app = QRadioButton("Application Profile")
        self.radio_port.setChecked(True)

        self.type_group = QButtonGroup(self)
        self.type_group.addButton(self.radio_port, 1)
        self.type_group.addButton(self.radio_app, 2)
        self.type_group.idClicked.connect(self.on_type_changed)

        type_layout.addWidget(self.radio_port)
        type_layout.addWidget(self.radio_app)
        type_layout.addStretch()
        layout.addLayout(type_layout)

        # Port Input or App Dropdown
        self.port_row = QHBoxLayout()
        lbl_target = QLabel("Port / Range:")
        lbl_target.setFixedWidth(100)
        lbl_target.setStyleSheet("font-weight: 600;")
        self.input_port = QLineEdit("80")
        self.input_port.setPlaceholderText("e.g. 8080 or 3000:3010")
        self.input_port.textChanged.connect(self.update_command_preview)

        self.combo_apps = QComboBox()
        self.combo_apps.addItems(self.available_apps)
        self.combo_apps.hide()
        self.combo_apps.currentIndexChanged.connect(self.update_command_preview)

        self.port_row.addWidget(lbl_target)
        self.port_row.addWidget(self.input_port)
        self.port_row.addWidget(self.combo_apps)
        layout.addLayout(self.port_row)

        # 3. Action Policy
        action_row = QHBoxLayout()
        lbl_act = QLabel("Policy Action:")
        lbl_act.setFixedWidth(100)
        lbl_act.setStyleSheet("font-weight: 600;")
        self.combo_action = QComboBox()
        self.combo_action.addItems([
            "ALLOW (Accept incoming/outgoing)",
            "DENY (Silently drop packets)",
            "REJECT (Actively refuse connection)",
            "LIMIT (Rate limit brute force attacks)"
        ])
        self.combo_action.currentIndexChanged.connect(self.update_command_preview)
        action_row.addWidget(lbl_act)
        action_row.addWidget(self.combo_action)
        layout.addLayout(action_row)

        # 4. Protocol & Direction
        proto_row = QHBoxLayout()
        lbl_proto = QLabel("Protocol:")
        lbl_proto.setFixedWidth(100)
        lbl_proto.setStyleSheet("font-weight: 600;")
        self.combo_proto = QComboBox()
        self.combo_proto.addItems(["TCP", "UDP", "Both (Any)"])
        self.combo_proto.currentIndexChanged.connect(self.update_command_preview)

        lbl_dir = QLabel("Direction:")
        lbl_dir.setStyleSheet("font-weight: 600; margin-left: 10px;")
        self.combo_dir = QComboBox()
        self.combo_dir.addItems(["Inbound (IN)", "Outbound (OUT)"])
        self.combo_dir.currentIndexChanged.connect(self.update_command_preview)

        proto_row.addWidget(lbl_proto)
        proto_row.addWidget(self.combo_proto)
        proto_row.addWidget(lbl_dir)
        proto_row.addWidget(self.combo_dir)
        layout.addLayout(proto_row)

        # 5. Network Interface selector
        iface_row = QHBoxLayout()
        lbl_iface = QLabel("Interface:")
        lbl_iface.setFixedWidth(100)
        lbl_iface.setStyleSheet("font-weight: 600;")
        self.combo_iface = QComboBox()
        interfaces = FirewallBackend.get_interface_names()
        self.combo_iface.addItems(interfaces)
        self.combo_iface.currentIndexChanged.connect(self.update_command_preview)
        iface_row.addWidget(lbl_iface)
        iface_row.addWidget(self.combo_iface)
        layout.addLayout(iface_row)

        # 6. Source IP filter
        src_row = QHBoxLayout()
        lbl_src = QLabel("Source IP:")
        lbl_src.setFixedWidth(100)
        lbl_src.setStyleSheet("font-weight: 600;")
        self.input_src = QLineEdit("Anywhere")
        self.input_src.setPlaceholderText("Anywhere or e.g. 192.168.1.0/24")
        self.input_src.textChanged.connect(self.update_command_preview)
        src_row.addWidget(lbl_src)
        src_row.addWidget(self.input_src)
        layout.addLayout(src_row)

        # 6. Comment
        cmt_row = QHBoxLayout()
        lbl_cmt = QLabel("Rule Comment:")
        lbl_cmt.setFixedWidth(100)
        lbl_cmt.setStyleSheet("font-weight: 600;")
        self.input_comment = QLineEdit()
        self.input_comment.setPlaceholderText("Optional description (e.g. Local Web Server)")
        self.input_comment.textChanged.connect(self.update_command_preview)
        cmt_row.addWidget(lbl_cmt)
        cmt_row.addWidget(self.input_comment)
        layout.addLayout(cmt_row)

        # 7. Live Preview
        lbl_cmd_title = QLabel("UFW Command Preview:")
        lbl_cmd_title.setStyleSheet("font-size: 11px; font-weight: 600; color: #8b949e;")
        layout.addWidget(lbl_cmd_title)

        self.lbl_cmd_preview = QLabel("ufw allow ...")
        self.lbl_cmd_preview.setStyleSheet("""
            background-color: #05070a;
            color: #00d2ff;
            font-family: monospace;
            font-size: 11px;
            padding: 8px;
            border: 1px solid #30363d;
            border-radius: 4px;
        """)
        layout.addWidget(self.lbl_cmd_preview)

        # Buttons
        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        self.btn_submit = QPushButton("Add Firewall Rule")
        self.btn_submit.setProperty("class", "btn-primary")
        self.btn_submit.clicked.connect(self.on_submit)

        btn_box.addStretch()
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(self.btn_submit)
        layout.addLayout(btn_box)

    def apply_preset(self, preset: dict):
        self.radio_port.setChecked(True)
        self.on_type_changed(1)
        self.input_port.setText(preset["port"])
        if preset["proto"] == "tcp":
            self.combo_proto.setCurrentIndex(0)
        elif preset["proto"] == "udp":
            self.combo_proto.setCurrentIndex(1)
        else:
            self.combo_proto.setCurrentIndex(2)
        self.input_comment.setText(preset["desc"])
        self.update_command_preview()

    def on_type_changed(self, btn_id: int):
        if btn_id == 1:
            self.input_port.show()
            self.combo_apps.hide()
            self.combo_proto.setEnabled(True)
        else:
            self.input_port.hide()
            self.combo_apps.show()
            self.combo_proto.setEnabled(False)
        self.update_command_preview()

    def get_action_keyword(self) -> str:
        idx = self.combo_action.currentIndex()
        if idx == 0: return "allow"
        elif idx == 1: return "deny"
        elif idx == 2: return "reject"
        return "limit"

    def update_command_preview(self):
        action = self.get_action_keyword()
        direction = "in" if self.combo_dir.currentIndex() == 0 else "out"

        if self.radio_port.isChecked():
            target = self.input_port.text().strip() or "80"
            proto_idx = self.combo_proto.currentIndex()
            proto = "tcp" if proto_idx == 0 else ("udp" if proto_idx == 1 else "any")
            src = self.input_src.text().strip()
            comment = self.input_comment.text().strip()
            iface = self.combo_iface.currentText().strip() if hasattr(self, "combo_iface") else ""

            cmd = FirewallBackend.cmd_add_rule(
                port_or_app=target,
                action=action,
                protocol=proto,
                direction=direction,
                from_ip=src,
                interface=iface,
                comment=comment
            )
        else:
            app_name = self.combo_apps.currentText()
            cmd = [FirewallBackend.get_ufw_path(), action, app_name]

        self.generated_command = cmd
        self.lbl_cmd_preview.setText("sudo " + " ".join(cmd))

    def on_submit(self):
        if self.radio_port.isChecked():
            port_text = self.input_port.text().strip()
            if not port_text:
                QMessageBox.warning(self, "Invalid Port", "Please enter a valid port number, service name, or port range (e.g. 8080 or 3000:3010).")
                return

        self.accept()

    def get_command(self) -> List[str]:
        return self.generated_command
