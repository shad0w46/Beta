"""Boot diagnostics and system journal logs module."""

from typing import List, Dict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QTabWidget, QComboBox, QLineEdit, QPlainTextEdit, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer

from beta_assistant.core.module_base import BaseModule
from beta_assistant.core.async_worker import AsyncRunner
from beta_assistant.modules.logs.logs_backend import LogsBackend, BlameItem
from beta_assistant.ui.components.badges import StatusBadge


class LogsWidget(QWidget):
    """Main view for boot diagnostics and journal inspection."""

    def __init__(self, module: 'LogsModule'):
        super().__init__()
        self.module = module
        self.blame_items: List[BlameItem] = []

        self.init_ui()
        QTimer.singleShot(50, self.refresh_all)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # 1. Boot Summary Hero Card
        hero_card = QFrame()
        hero_card.setProperty("class", "card-elevated")
        hero_layout = QHBoxLayout(hero_card)
        hero_layout.setContentsMargins(18, 14, 18, 14)

        v_info = QVBoxLayout()
        title = QLabel("System Boot Diagnostics")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #58a6ff;")
        self.boot_total_lbl = QLabel("Total Boot Time: Analyzing...")
        self.boot_total_lbl.setStyleSheet("font-size: 14px; font-weight: 600; margin-top: 2px;")
        v_info.addWidget(title)
        v_info.addWidget(self.boot_total_lbl)
        hero_layout.addLayout(v_info)
        hero_layout.addStretch()

        self.boot_breakdown_lbl = QLabel("")
        self.boot_breakdown_lbl.setStyleSheet("color: #8b949e; font-size: 12px;")
        hero_layout.addWidget(self.boot_breakdown_lbl)

        btn_reanalyze = QPushButton("⟳ Re-analyze Boot")
        btn_reanalyze.clicked.connect(self.refresh_boot_data)
        hero_layout.addWidget(btn_reanalyze)

        main_layout.addWidget(hero_card)

        # 2. Tabs: Boot Blame vs System Journal
        self.tabs = QTabWidget()

        # Tab A: Boot Blame (Slow Services)
        tab_blame = QWidget()
        blame_layout = QVBoxLayout(tab_blame)
        blame_layout.setContentsMargins(10, 12, 10, 10)
        blame_layout.setSpacing(8)

        lbl_blame_hint = QLabel("Services ranked by startup time impact during system boot (systemd-analyze blame):")
        lbl_blame_hint.setStyleSheet("color: #8b949e; font-size: 12px;")
        blame_layout.addWidget(lbl_blame_hint)

        self.blame_table = QTableWidget()
        self.blame_table.setColumnCount(3)
        self.blame_table.setHorizontalHeaderLabels(["Service Unit", "Startup Duration", "Impact Level"])
        self.blame_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.blame_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.blame_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.blame_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.blame_table.verticalHeader().setVisible(False)
        blame_layout.addWidget(self.blame_table)

        self.tabs.addTab(tab_blame, "Boot Blame (Slow Services)")

        # Tab B: Journal Log Inspector
        tab_journal = QWidget()
        journal_layout = QVBoxLayout(tab_journal)
        journal_layout.setContentsMargins(10, 12, 10, 10)
        journal_layout.setSpacing(8)

        # Controls bar
        j_ctrl = QHBoxLayout()
        j_ctrl.addWidget(QLabel("Min Severity:"))
        self.combo_prio = QComboBox()
        self.combo_prio.addItems(["warning", "err", "crit", "alert", "emerg", "notice", "info"])
        self.combo_prio.setCurrentText("warning")
        self.combo_prio.currentIndexChanged.connect(self.refresh_journal_logs)
        j_ctrl.addWidget(self.combo_prio)

        self.input_search_journal = QLineEdit()
        self.input_search_journal.setPlaceholderText("Filter logs by text pattern...")
        self.input_search_journal.setClearButtonEnabled(True)
        self.input_search_journal.returnPressed.connect(self.refresh_journal_logs)
        j_ctrl.addWidget(self.input_search_journal, stretch=1)

        btn_fetch_log = QPushButton("Search Logs")
        btn_fetch_log.clicked.connect(self.refresh_journal_logs)
        j_ctrl.addWidget(btn_fetch_log)

        journal_layout.addLayout(j_ctrl)

        self.journal_console = QPlainTextEdit()
        self.journal_console.setReadOnly(True)
        self.journal_console.setStyleSheet("font-family: monospace; font-size: 11px; background-color: #05070a; color: #58a6ff;")
        journal_layout.addWidget(self.journal_console)

        self.tabs.addTab(tab_journal, "System Journal Inspector")

        main_layout.addWidget(self.tabs)

    def refresh_all(self):
        self.refresh_boot_data()
        self.refresh_journal_logs()

    def refresh_boot_data(self):
        AsyncRunner.run(
            func=LogsBackend.get_boot_times,
            on_success=self.render_boot_times
        )
        AsyncRunner.run(
            func=LogsBackend.get_boot_blame,
            on_success=self.render_boot_blame,
            limit=50
        )

    def render_boot_times(self, data: Dict[str, str]):
        self.boot_total_lbl.setText(f"Total Boot Time: <b>{data.get('total', 'N/A')}</b>")
        breakdown = (
            f"Firmware: <b>{data.get('firmware', 'N/A')}</b> • "
            f"Loader: <b>{data.get('loader', 'N/A')}</b> • "
            f"Kernel: <b>{data.get('kernel', 'N/A')}</b> • "
            f"Userspace: <b>{data.get('userspace', 'N/A')}</b>"
        )
        self.boot_breakdown_lbl.setText(breakdown)

    def render_boot_blame(self, items: List[BlameItem]):
        self.blame_items = items
        self.blame_table.setRowCount(len(items))

        for row, item in enumerate(items):
            item_svc = QTableWidgetItem(item.service)
            self.blame_table.setItem(row, 0, item_svc)

            item_dur = QTableWidgetItem(item.duration_str)
            item_dur.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.blame_table.setItem(row, 1, item_dur)

            # Impact badge
            if item.impact_level == "high":
                badge_text = "High Impact (> 2s)"
                st = "failed"
            elif item.impact_level == "medium":
                badge_text = "Moderate"
                st = "upgradable"
            else:
                badge_text = "Fast (< 500ms)"
                st = "active"

            item_impact = QTableWidgetItem(badge_text)
            item_impact.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.blame_table.setItem(row, 2, item_impact)

    def refresh_journal_logs(self):
        prio = self.combo_prio.currentText()
        pattern = self.input_search_journal.text().strip()
        self.journal_console.setPlainText("Querying journalctl...")

        def on_done(text):
            self.journal_console.setPlainText(text)
            self.journal_console.verticalScrollBar().setValue(
                self.journal_console.verticalScrollBar().maximum()
            )

        AsyncRunner.run(
            func=LogsBackend.query_journal,
            on_success=on_done,
            priority=prio,
            lines=100,
            query=pattern
        )


class LogsModule(BaseModule):
    """Boot Diagnostics and System Journal Module."""

    @property
    def module_id(self) -> str:
        return "logs"

    @property
    def title(self) -> str:
        return "Boot & Logs"

    @property
    def icon_name(self) -> str:
        return "text-box-search"

    @property
    def order(self) -> int:
        return 45

    def create_widget(self) -> QWidget:
        return LogsWidget(self)

    def refresh(self):
        if self._widget and isinstance(self._widget, LogsWidget):
            self._widget.refresh_all()
