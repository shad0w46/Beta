"""Service and Daemon Management module for systemd units."""

import tempfile
from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QSplitter, QComboBox, QTextEdit, QDialog
)
from PyQt6.QtCore import Qt, QTimer

from beta_assistant.core.module_base import BaseModule
from beta_assistant.modules.services.service_backend import ServiceBackend, ServiceInfo
from beta_assistant.modules.services.create_service_dialog import CreateServiceDialog
from beta_assistant.ui.components.badges import StatusBadge


class ServicesWidget(QWidget):
    """Main view for managing systemd services and daemons."""

    def __init__(self, module: 'ServicesModule'):
        super().__init__()
        self.module = module
        self.all_services: List[ServiceInfo] = []
        self.filtered_services: List[ServiceInfo] = []
        self.selected_service: Optional[ServiceInfo] = None

        self.init_ui()
        QTimer.singleShot(100, self.load_services)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # 1. Top Bar: Search, Category Filters, and Create Action
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        # Search filter
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter services by name or description...")
        self.search_input.setFixedHeight(36)
        self.search_input.textChanged.connect(self.apply_filter)
        top_bar.addWidget(self.search_input, stretch=2)

        # Status Filter
        self.combo_status = QComboBox()
        self.combo_status.addItems([
            "All Services",
            "Running Services",
            "Inactive Services",
            "Failed Services"
        ])
        self.combo_status.setFixedHeight(36)
        self.combo_status.currentIndexChanged.connect(self.apply_filter)
        top_bar.addWidget(self.combo_status)

        # Refresh
        btn_refresh = QPushButton("Refresh")
        btn_refresh.setFixedHeight(36)
        btn_refresh.clicked.connect(self.load_services)
        top_bar.addWidget(btn_refresh)

        # Create Custom Daemon / Service
        btn_create = QPushButton("+ Create Custom Service / Daemon")
        btn_create.setProperty("class", "btn-primary")
        btn_create.setFixedHeight(36)
        btn_create.clicked.connect(self.open_create_dialog)
        top_bar.addWidget(btn_create)

        main_layout.addLayout(top_bar)

        # 2. Splitter: Services Table on Left, Details & Logs on Right
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(4)

        # Left: Table
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        self.status_label = QLabel("Loading system services...")
        self.status_label.setStyleSheet("color: #8b949e; font-size: 12px;")
        left_layout.addWidget(self.status_label)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Unit Name", "Status", "Sub-State", "Description"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 240)
        self.table.setColumnWidth(1, 90)
        self.table.setColumnWidth(2, 90)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.itemSelectionChanged.connect(self.on_service_selected)
        left_layout.addWidget(self.table)

        splitter.addWidget(left_frame)

        # Right: Details & Log Inspector
        self.details_panel = QFrame()
        self.details_panel.setProperty("class", "card")
        self.details_panel.setMinimumWidth(340)
        self.details_panel.setMaximumWidth(460)

        details_layout = QVBoxLayout(self.details_panel)
        details_layout.setContentsMargins(14, 14, 14, 14)
        details_layout.setSpacing(10)

        self.detail_unit_name = QLabel("Select a service")
        self.detail_unit_name.setStyleSheet("font-size: 17px; font-weight: 700; color: #58a6ff;")
        details_layout.addWidget(self.detail_unit_name)

        self.detail_badge = StatusBadge("None", "inactive")
        self.detail_badge.hide()
        details_layout.addWidget(self.detail_badge)

        self.detail_meta = QLabel("")
        self.detail_meta.setStyleSheet("color: #c9d1d9; font-size: 12px; line-height: 1.5;")
        self.detail_meta.setWordWrap(True)
        details_layout.addWidget(self.detail_meta)

        # Action Buttons Grid
        self.actions_box = QVBoxLayout()
        self.actions_box.setSpacing(6)

        h_ctrl1 = QHBoxLayout()
        self.btn_start = QPushButton("▶ Start")
        self.btn_start.setProperty("class", "btn-primary")
        self.btn_start.clicked.connect(self.action_start)

        self.btn_stop = QPushButton("⏹ Stop")
        self.btn_stop.setProperty("class", "btn-danger")
        self.btn_stop.clicked.connect(self.action_stop)

        self.btn_restart = QPushButton("🔄 Restart")
        self.btn_restart.setProperty("class", "btn-accent")
        self.btn_restart.clicked.connect(self.action_restart)

        h_ctrl1.addWidget(self.btn_start)
        h_ctrl1.addWidget(self.btn_stop)
        h_ctrl1.addWidget(self.btn_restart)
        self.actions_box.addLayout(h_ctrl1)

        h_ctrl2 = QHBoxLayout()
        self.btn_enable = QPushButton("Enable on Boot")
        self.btn_enable.clicked.connect(self.action_enable)

        self.btn_disable = QPushButton("Disable Boot")
        self.btn_disable.clicked.connect(self.action_disable)

        h_ctrl2.addWidget(self.btn_enable)
        h_ctrl2.addWidget(self.btn_disable)
        self.actions_box.addLayout(h_ctrl2)

        details_layout.addLayout(self.actions_box)

        # Log viewer section
        log_header = QHBoxLayout()
        lbl_logs = QLabel("Journalctl Logs (Latest 50 lines):")
        lbl_logs.setStyleSheet("color: #8b949e; font-size: 11px; font-weight: 600;")
        btn_refresh_log = QPushButton("Reload Logs")
        btn_refresh_log.setFixedHeight(26)
        btn_refresh_log.clicked.connect(self.refresh_logs)

        log_header.addWidget(lbl_logs)
        log_header.addStretch()
        log_header.addWidget(btn_refresh_log)
        details_layout.addLayout(log_header)

        self.log_viewer = QTextEdit()
        self.log_viewer.setReadOnly(True)
        self.log_viewer.setStyleSheet("""
            QTextEdit {
                background-color: #05070a;
                color: #e6edf3;
                font-family: monospace;
                font-size: 11px;
                border: 1px solid #30363d;
            }
        """)
        details_layout.addWidget(self.log_viewer)

        self.reset_details_panel()

        splitter.addWidget(self.details_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

    def load_services(self):
        self.status_label.setText("Querying systemd units...")
        self.all_services = ServiceBackend.get_all_services()

        # Update badge in sidebar if failed units exist
        failed_count = sum(1 for s in self.all_services if s.is_failed)
        self.module.badge_updated.emit("services", f"!{failed_count}" if failed_count > 0 else "")

        self.apply_filter()

    def apply_filter(self):
        query = self.search_input.text().strip().lower()
        st_idx = self.combo_status.currentIndex()

        filtered = []
        for s in self.all_services:
            if st_idx == 1 and not s.is_active:
                continue
            elif st_idx == 2 and s.is_active:
                continue
            elif st_idx == 3 and not s.is_failed:
                continue

            if query:
                match = (
                    query in s.name.lower() or
                    query in s.description.lower() or
                    query in s.sub_state.lower()
                )
                if not match:
                    continue

            filtered.append(s)

        self.filtered_services = filtered
        self.populate_table()

    def populate_table(self):
        self.status_label.setText(f"Showing {len(self.filtered_services)} services.")
        self.table.setRowCount(len(self.filtered_services))

        for row, s in enumerate(self.filtered_services):
            # Unit Name
            item_name = QTableWidgetItem(s.name)
            item_name.setData(Qt.ItemDataRole.UserRole, s.name)
            self.table.setItem(row, 0, item_name)

            # Status
            item_status = QTableWidgetItem(s.status_display)
            self.table.setItem(row, 1, item_status)

            # Sub-state
            item_sub = QTableWidgetItem(s.sub_state)
            self.table.setItem(row, 2, item_sub)

            # Description
            item_desc = QTableWidgetItem(s.description)
            self.table.setItem(row, 3, item_desc)

        if self.filtered_services:
            self.table.selectRow(0)
        else:
            self.reset_details_panel()

    def on_service_selected(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            self.reset_details_panel()
            return

        row = selected_rows[0].row()
        unit_name = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        for s in self.filtered_services:
            if s.name == unit_name:
                self.selected_service = s
                break
        else:
            return

        s = self.selected_service
        self.detail_unit_name.setText(s.name)

        if s.is_failed:
            self.detail_badge.setStatus("Failed", "failed")
        elif s.is_active:
            self.detail_badge.setStatus(f"Running ({s.sub_state})", "running")
        else:
            self.detail_badge.setStatus("Inactive", "inactive")
        self.detail_badge.show()

        # Query live properties
        props = ServiceBackend.get_service_details(s.name)
        meta = [
            f"<b>Description:</b> {s.description or 'No description'}",
            f"<b>Main PID:</b> {props.get('MainPID', '0')}",
            f"<b>Load State:</b> {s.load_state}",
            f"<b>Active State:</b> {props.get('ActiveState', 'unknown')} ({props.get('SubState', 'unknown')})",
            f"<b>Unit Path:</b> {props.get('FragmentPath', 'N/A')}"
        ]
        self.detail_meta.setText("<br>".join(meta))

        # Show action buttons
        self.btn_start.setEnabled(not s.is_active)
        self.btn_stop.setEnabled(s.is_active)
        self.btn_restart.setEnabled(True)
        self.btn_enable.show()
        self.btn_disable.show()

        # Refresh logs
        self.refresh_logs()

    def refresh_logs(self):
        if not self.selected_service:
            self.log_viewer.clear()
            return
        logs = ServiceBackend.get_service_logs(self.selected_service.name, lines=60)
        self.log_viewer.setPlainText(logs)
        self.log_viewer.verticalScrollBar().setValue(
            self.log_viewer.verticalScrollBar().maximum()
        )

    def reset_details_panel(self):
        self.detail_unit_name.setText("Select a service")
        self.detail_badge.hide()
        self.detail_meta.setText("Select any systemd service from the list to view runtime details and control execution.")
        self.log_viewer.clear()
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self.btn_restart.setEnabled(False)
        self.btn_enable.hide()
        self.btn_disable.hide()
        self.selected_service = None

    def open_create_dialog(self):
        dialog = CreateServiceDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_service_data()
            unit_name = data["name"]
            unit_content = data["unit_content"]
            target_path = f"/etc/systemd/system/{unit_name}"

            # Write unit file to temporary file first, then install to /etc/systemd/system/
            with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
                tmp.write(unit_content)
                tmp_path = tmp.name

            # Chain execution: cp -> systemctl daemon-reload -> (optional enable/start)
            install_cmd = ["install", "-m", "644", tmp_path, target_path]

            def after_install(ok: bool):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

                if ok:
                    # Reload daemon
                    self.module.request_command.emit(
                        ServiceBackend.cmd_daemon_reload(),
                        True,
                        "Systemd Daemon Reload",
                        lambda r_ok: self._after_daemon_reload(unit_name, data["enable"], data["start"])
                    )

            self.module.request_command.emit(
                install_cmd,
                True,
                f"Install Unit File '{unit_name}'",
                after_install
            )

    def _after_daemon_reload(self, unit_name: str, enable: bool, start: bool):
        if enable:
            self.module.request_command.emit(
                ServiceBackend.cmd_enable(unit_name),
                True,
                f"Enable '{unit_name}' at boot",
                lambda e_ok: self._after_enable(unit_name, start)
            )
        elif start:
            self._after_enable(unit_name, start)
        else:
            self.load_services()

    def _after_enable(self, unit_name: str, start: bool):
        if start:
            self.module.request_command.emit(
                ServiceBackend.cmd_start(unit_name),
                True,
                f"Start '{unit_name}'",
                lambda s_ok: self.load_services()
            )
        else:
            self.load_services()

    def action_start(self):
        if not self.selected_service:
            return
        self.module.request_command.emit(
            ServiceBackend.cmd_start(self.selected_service.name),
            True,
            f"Start {self.selected_service.name}",
            lambda ok: self.load_services()
        )

    def action_stop(self):
        if not self.selected_service:
            return
        self.module.request_command.emit(
            ServiceBackend.cmd_stop(self.selected_service.name),
            True,
            f"Stop {self.selected_service.name}",
            lambda ok: self.load_services()
        )

    def action_restart(self):
        if not self.selected_service:
            return
        self.module.request_command.emit(
            ServiceBackend.cmd_restart(self.selected_service.name),
            True,
            f"Restart {self.selected_service.name}",
            lambda ok: self.load_services()
        )

    def action_enable(self):
        if not self.selected_service:
            return
        self.module.request_command.emit(
            ServiceBackend.cmd_enable(self.selected_service.name),
            True,
            f"Enable {self.selected_service.name}",
            lambda ok: self.load_services()
        )

    def action_disable(self):
        if not self.selected_service:
            return
        self.module.request_command.emit(
            ServiceBackend.cmd_disable(self.selected_service.name),
            True,
            f"Disable {self.selected_service.name}",
            lambda ok: self.load_services()
        )


class ServicesModule(BaseModule):
    """Services and Daemons Management Module."""

    @property
    def module_id(self) -> str:
        return "services"

    @property
    def title(self) -> str:
        return "Services & Daemons"

    @property
    def icon_name(self) -> str:
        return "cog-transfer"

    @property
    def order(self) -> int:
        return 40

    def create_widget(self) -> QWidget:
        return ServicesWidget(self)

    def refresh(self):
        if self._widget and isinstance(self._widget, ServicesWidget):
            self._widget.load_services()
