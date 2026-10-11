"""Firewall (UFW / netfilter) Management Module with non-blocking GUI."""

from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QComboBox, QMessageBox, QProgressBar, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer

from beta_assistant.core.module_base import BaseModule
from beta_assistant.core.async_worker import AsyncRunner, WorkerThread
from beta_assistant.modules.firewall.firewall_backend import FirewallBackend, FirewallStatus, FirewallRule
from beta_assistant.modules.firewall.add_rule_dialog import AddRuleDialog
from beta_assistant.ui.components.badges import StatusBadge


class FirewallWidget(QWidget):
    """Main responsive GUI for inspecting and configuring system firewall rules."""

    def __init__(self, module: 'FirewallModule'):
        super().__init__()
        self.module = module
        self.status: Optional[FirewallStatus] = None
        self.worker: Optional[WorkerThread] = None

        self.init_ui()
        QTimer.singleShot(50, self.load_status)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # 1. Hero Card: Global Status & Toggle Controls
        self.hero_card = QFrame()
        self.hero_card.setProperty("class", "card")
        hero_layout = QVBoxLayout(self.hero_card)
        hero_layout.setContentsMargins(16, 14, 16, 14)
        hero_layout.setSpacing(10)

        # Top row: Status, Badges, and Master Toggle
        top_row = QHBoxLayout()
        v_title = QVBoxLayout()
        lbl_head = QLabel("Network Firewall (UFW)")
        lbl_head.setStyleSheet("font-size: 18px; font-weight: 800; color: #58a6ff;")
        self.lbl_status_desc = QLabel("Querying firewall engine status...")
        self.lbl_status_desc.setStyleSheet("color: #8b949e; font-size: 12px;")
        v_title.addWidget(lbl_head)
        v_title.addWidget(self.lbl_status_desc)

        top_row.addLayout(v_title)
        top_row.addStretch()

        self.badge_status = StatusBadge("CHECKING", "inactive")
        top_row.addWidget(self.badge_status)
        top_row.addSpacing(12)

        self.btn_toggle_power = QPushButton("Enable Firewall")
        self.btn_toggle_power.setFixedHeight(36)
        self.btn_toggle_power.setProperty("class", "btn-primary")
        self.btn_toggle_power.clicked.connect(self.action_toggle_power)
        top_row.addWidget(self.btn_toggle_power)

        hero_layout.addLayout(top_row)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("color: #30363d; margin: 4px 0;")
        hero_layout.addWidget(div)

        # Controls Row: Default Policies & Logging
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(14)

        # Incoming Policy
        ctrl_row.addWidget(QLabel("Incoming Traffic:"))
        self.combo_incoming = QComboBox()
        self.combo_incoming.addItems(["Deny (Recommended)", "Allow", "Reject"])
        self.combo_incoming.setFixedHeight(30)
        self.combo_incoming.activated.connect(self.on_change_incoming)
        ctrl_row.addWidget(self.combo_incoming)

        # Outgoing Policy
        ctrl_row.addWidget(QLabel("Outgoing Traffic:"))
        self.combo_outgoing = QComboBox()
        self.combo_outgoing.addItems(["Allow (Recommended)", "Deny", "Reject"])
        self.combo_outgoing.setFixedHeight(30)
        self.combo_outgoing.activated.connect(self.on_change_outgoing)
        ctrl_row.addWidget(self.combo_outgoing)

        # Logging level
        ctrl_row.addWidget(QLabel("Logging:"))
        self.combo_logging = QComboBox()
        self.combo_logging.addItems(["Off", "Low", "Medium", "High"])
        self.combo_logging.setFixedHeight(30)
        self.combo_logging.activated.connect(self.on_change_logging)
        ctrl_row.addWidget(self.combo_logging)

        ctrl_row.addStretch()

        btn_reload = QPushButton("⟳ Reload")
        btn_reload.setFixedHeight(30)
        btn_reload.setToolTip("Reload UFW firewall rules without dropping connections")
        btn_reload.clicked.connect(self.action_reload)
        ctrl_row.addWidget(btn_reload)

        btn_reset = QPushButton("⚠ Reset Defaults")
        btn_reset.setFixedHeight(30)
        btn_reset.setProperty("class", "btn-danger")
        btn_reset.setToolTip("Reset all firewall rules to factory default settings")
        btn_reset.clicked.connect(self.action_reset)
        ctrl_row.addWidget(btn_reset)

        hero_layout.addLayout(ctrl_row)
        main_layout.addWidget(self.hero_card)

        # Subtle progress indicator
        self.loading_bar = QProgressBar()
        self.loading_bar.setFixedHeight(2)
        self.loading_bar.setRange(0, 0)
        self.loading_bar.setTextVisible(False)
        self.loading_bar.hide()
        main_layout.addWidget(self.loading_bar)

        # 2. Rules Bar: Filter, Category, and Add Button
        rules_bar = QHBoxLayout()
        rules_bar.setSpacing(10)

        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("Filter rules live by port, IP, or comment...")
        self.input_search.setFixedHeight(36)
        self.input_search.setClearButtonEnabled(True)
        self.input_search.textChanged.connect(self.populate_rules_table)
        rules_bar.addWidget(self.input_search, stretch=2)

        self.combo_filter_action = QComboBox()
        self.combo_filter_action.addItems(["All Actions", "Allow Rules Only", "Deny/Reject Rules Only"])
        self.combo_filter_action.setFixedHeight(36)
        self.combo_filter_action.currentIndexChanged.connect(self.populate_rules_table)
        rules_bar.addWidget(self.combo_filter_action)

        btn_refresh = QPushButton("Refresh")
        btn_refresh.setFixedHeight(36)
        btn_refresh.clicked.connect(self.load_status)
        rules_bar.addWidget(btn_refresh)

        btn_add = QPushButton("+ Add Firewall Rule")
        btn_add.setProperty("class", "btn-primary")
        btn_add.setFixedHeight(36)
        btn_add.clicked.connect(self.open_add_rule_dialog)
        rules_bar.addWidget(btn_add)

        main_layout.addLayout(rules_bar)

        # 3. Rules Table
        self.lbl_rule_count = QLabel("Active Rules (0)")
        self.lbl_rule_count.setStyleSheet("color: #8b949e; font-size: 12px; font-weight: 600;")
        main_layout.addWidget(self.lbl_rule_count)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "#", "Policy", "Direction", "Destination (To)", "Source (From)", "Comment", "Action"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        main_layout.addWidget(self.table)

    def load_status(self):
        """Asynchronously queries UFW status."""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()

        self.loading_bar.show()

        def on_done(st: FirewallStatus):
            self.status = st
            self.render_status()

        self.worker = AsyncRunner.run(
            func=FirewallBackend.get_status,
            on_success=on_done,
            on_finish=lambda: self.loading_bar.hide()
        )

    def render_status(self):
        if not self.status:
            return

        is_act = self.status.is_active

        # Badge and Descriptions
        if is_act:
            self.badge_status.setStatus("ACTIVE (PROTECTED)", "active")
            self.lbl_status_desc.setText("Firewall is active and filtering network traffic according to rules below.")
            self.btn_toggle_power.setText("Disable Firewall")
            self.btn_toggle_power.setProperty("class", "btn-danger")
            self.module.badge_updated.emit("firewall", "ON")
        else:
            self.badge_status.setStatus("INACTIVE (UNPROTECTED)", "inactive")
            self.lbl_status_desc.setText("Firewall is currently disabled. All network ports are open.")
            self.btn_toggle_power.setText("🛡️ Enable Firewall")
            self.btn_toggle_power.setProperty("class", "btn-primary")
            self.module.badge_updated.emit("firewall", "OFF")

        # Repaint toggle button style
        self.btn_toggle_power.style().unpolish(self.btn_toggle_power)
        self.btn_toggle_power.style().polish(self.btn_toggle_power)

        # Block signals during combo update
        self.combo_incoming.blockSignals(True)
        self.combo_outgoing.blockSignals(True)
        self.combo_logging.blockSignals(True)

        # Incoming combo
        inc = self.status.default_incoming.lower()
        if "deny" in inc: self.combo_incoming.setCurrentIndex(0)
        elif "allow" in inc: self.combo_incoming.setCurrentIndex(1)
        elif "reject" in inc: self.combo_incoming.setCurrentIndex(2)

        # Outgoing combo
        out = self.status.default_outgoing.lower()
        if "allow" in out: self.combo_outgoing.setCurrentIndex(0)
        elif "deny" in out: self.combo_outgoing.setCurrentIndex(1)
        elif "reject" in out: self.combo_outgoing.setCurrentIndex(2)

        # Logging combo
        log = self.status.logging.lower()
        if "off" in log: self.combo_logging.setCurrentIndex(0)
        elif "medium" in log: self.combo_logging.setCurrentIndex(2)
        elif "high" in log: self.combo_logging.setCurrentIndex(3)
        else: self.combo_logging.setCurrentIndex(1)

        self.combo_incoming.blockSignals(False)
        self.combo_outgoing.blockSignals(False)
        self.combo_logging.blockSignals(False)

        self.populate_rules_table()

    def populate_rules_table(self):
        if not self.status:
            return

        query = self.input_search.text().strip().lower()
        act_filter = self.combo_filter_action.currentIndex()

        filtered: List[FirewallRule] = []
        for r in self.status.rules:
            # Action filter
            if act_filter == 1 and r.action_type != "allow":
                continue
            elif act_filter == 2 and r.action_type not in ("deny", "reject"):
                continue

            # Query filter
            if query:
                match = (
                    query in str(r.number) or
                    query in r.to_destination.lower() or
                    query in r.from_source.lower() or
                    query in r.action.lower() or
                    query in r.comment.lower()
                )
                if not match:
                    continue

            filtered.append(r)

        self.lbl_rule_count.setText(f"Active Rules ({len(self.status.rules)} total, {len(filtered)} displayed)")
        self.table.setRowCount(len(filtered))

        for row, r in enumerate(filtered):
            # 0. Number
            it_num = QTableWidgetItem(f"[{r.number}]")
            it_num.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, it_num)

            # 1. Policy Badge
            badge = StatusBadge(r.action.upper(), "active" if r.action_type == "allow" else "failed")
            self.table.setCellWidget(row, 1, badge)

            # 2. Direction
            it_dir = QTableWidgetItem(r.direction)
            it_dir.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, it_dir)

            # 3. Destination (To)
            it_to = QTableWidgetItem(r.to_destination)
            self.table.setItem(row, 3, it_to)

            # 4. Source (From)
            it_from = QTableWidgetItem(r.from_source)
            self.table.setItem(row, 4, it_from)

            # 5. Comment
            it_cmt = QTableWidgetItem(r.comment)
            it_cmt.setForeground(Qt.GlobalColor.gray)
            self.table.setItem(row, 5, it_cmt)

            # 6. Delete Action
            btn_del = QPushButton("Delete")
            btn_del.setFixedHeight(26)
            btn_del.setStyleSheet("font-size: 11px; padding: 2px 8px; color: #f85149;")
            num = r.number
            rule_desc = f"#{r.number} ({r.action} {r.to_destination})"
            btn_del.clicked.connect(lambda checked, n=num, d=rule_desc: self.action_delete_rule(n, d))
            self.table.setCellWidget(row, 6, btn_del)

    # User Actions
    def action_toggle_power(self):
        if not self.status:
            return

        if self.status.is_active:
            cmd = FirewallBackend.cmd_disable()
            title = "Disable System Firewall"
        else:
            cmd = FirewallBackend.cmd_enable()
            title = "Enable System Firewall"

        self.module.request_command.emit(
            cmd,
            True,
            title,
            lambda ok: self.load_status()
        )

    def on_change_incoming(self, idx: int):
        policies = ["deny", "allow", "reject"]
        policy = policies[idx]
        self.module.request_command.emit(
            FirewallBackend.cmd_set_default("incoming", policy),
            True,
            f"Set Default Incoming Policy to {policy.upper()}",
            lambda ok: self.load_status()
        )

    def on_change_outgoing(self, idx: int):
        policies = ["allow", "deny", "reject"]
        policy = policies[idx]
        self.module.request_command.emit(
            FirewallBackend.cmd_set_default("outgoing", policy),
            True,
            f"Set Default Outgoing Policy to {policy.upper()}",
            lambda ok: self.load_status()
        )

    def on_change_logging(self, idx: int):
        levels = ["off", "low", "medium", "high"]
        level = levels[idx]
        self.module.request_command.emit(
            FirewallBackend.cmd_set_logging(level),
            True,
            f"Set Firewall Logging to {level.upper()}",
            lambda ok: self.load_status()
        )

    def action_reload(self):
        self.module.request_command.emit(
            FirewallBackend.cmd_reload(),
            True,
            "Reload Firewall Rules",
            lambda ok: self.load_status()
        )

    def action_reset(self):
        reply = QMessageBox.question(
            self,
            "Confirm Firewall Reset",
            "Are you sure you want to reset all UFW firewall rules to factory defaults?\n\nThis will remove all custom rules.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.module.request_command.emit(
                FirewallBackend.cmd_reset(),
                True,
                "Reset Firewall Rules to Defaults",
                lambda ok: self.load_status()
            )

    def action_delete_rule(self, rule_num: int, rule_desc: str):
        reply = QMessageBox.question(
            self,
            "Delete Firewall Rule",
            f"Are you sure you want to delete rule {rule_desc}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.module.request_command.emit(
                FirewallBackend.cmd_delete_rule(rule_num),
                True,
                f"Delete Rule #{rule_num}",
                lambda ok: self.load_status()
            )

    def open_add_rule_dialog(self):
        apps = self.status.available_apps if self.status else []
        dialog = AddRuleDialog(available_apps=apps, parent=self)
        if dialog.exec() == AddRuleDialog.DialogCode.Accepted:
            cmd = dialog.get_command()
            self.module.request_command.emit(
                cmd,
                True,
                "Add Firewall Rule",
                lambda ok: self.load_status()
            )


class FirewallModule(BaseModule):
    """Firewall and Network Security Module for AlphaOS."""

    @property
    def module_id(self) -> str:
        return "firewall"

    @property
    def title(self) -> str:
        return "Firewall (UFW)"

    @property
    def icon_name(self) -> str:
        return "shield-lock"

    @property
    def order(self) -> int:
        return 45

    def create_widget(self) -> QWidget:
        return FirewallWidget(self)

    def refresh(self):
        if self._widget and isinstance(self._widget, FirewallWidget):
            self._widget.load_status()
