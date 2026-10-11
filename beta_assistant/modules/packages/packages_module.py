"""Package and Update Manager module using non-blocking async APT backend."""

from typing import List, Optional, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QSplitter, QTextEdit, QComboBox, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer

from beta_assistant.core.module_base import BaseModule
from beta_assistant.core.async_worker import AsyncRunner, WorkerThread
from beta_assistant.modules.packages.apt_backend import AptBackend, AptPackageInfo
from beta_assistant.ui.components.badges import StatusBadge


class PackagesWidget(QWidget):
    """Asynchronous, ultra-responsive view for APT package operations."""

    def __init__(self, module: 'PackagesModule'):
        super().__init__()
        self.module = module
        self.backend = AptBackend()
        self.current_packages: List[AptPackageInfo] = []
        self.selected_pkg_name: Optional[str] = None

        self.current_worker: Optional[WorkerThread] = None
        self.detail_worker: Optional[WorkerThread] = None

        # Debounce timer for live search
        self.search_debounce = QTimer(self)
        self.search_debounce.setSingleShot(True)
        self.search_debounce.setInterval(320) # 320ms debounce
        self.search_debounce.timeout.connect(self._execute_debounced_search)

        self.init_ui()

        # Load initial upgradable packages in background
        QTimer.singleShot(50, self.load_upgradable_packages)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(10)

        # 1. Top Bar: Search and Global Actions
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        # Search Box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search APT packages (live filter as you type: nginx, htop, git)...")
        self.search_input.setFixedHeight(36)
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.on_search_text_changed)
        self.search_input.returnPressed.connect(self._execute_debounced_search)
        top_bar.addWidget(self.search_input, stretch=3)

        self.search_btn = QPushButton("Search")
        self.search_btn.setProperty("class", "btn-accent")
        self.search_btn.setFixedHeight(36)
        self.search_btn.clicked.connect(self._execute_debounced_search)
        top_bar.addWidget(self.search_btn)

        # Filter View Combo
        self.view_filter = QComboBox()
        self.view_filter.addItems(["Upgradable Updates", "Installed Packages", "Search Repository"])
        self.view_filter.setFixedHeight(36)
        self.view_filter.currentIndexChanged.connect(self.on_filter_changed)
        top_bar.addWidget(self.view_filter)

        top_bar.addSpacing(6)

        # Global System Update Actions
        btn_update_cache = QPushButton("Update Index")
        btn_update_cache.setFixedHeight(36)
        btn_update_cache.clicked.connect(self.action_update_index)
        top_bar.addWidget(btn_update_cache)

        self.btn_upgrade_all = QPushButton("Upgrade All")
        self.btn_upgrade_all.setProperty("class", "btn-primary")
        self.btn_upgrade_all.setFixedHeight(36)
        self.btn_upgrade_all.clicked.connect(self.action_upgrade_all)
        top_bar.addWidget(self.btn_upgrade_all)

        main_layout.addLayout(top_bar)

        # Loading Progress Bar (subtle indeterminate bar below search)
        self.loading_bar = QProgressBar()
        self.loading_bar.setFixedHeight(2)
        self.loading_bar.setRange(0, 0)
        self.loading_bar.setTextVisible(False)
        self.loading_bar.hide()
        main_layout.addWidget(self.loading_bar)

        # 2. Main Content Splitter: Table on Left, Details on Right
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(5)

        # Left: Packages Table
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        self.table_status = QLabel("Ready")
        self.table_status.setStyleSheet("color: #8b949e; font-size: 12px; font-weight: 500;")
        left_layout.addWidget(self.table_status)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Package Name", "Current Version", "Latest Candidate", "Summary"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 180)
        self.table.setColumnWidth(1, 140)
        self.table.setColumnWidth(2, 140)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.itemSelectionChanged.connect(self.on_row_selected)
        left_layout.addWidget(self.table)

        splitter.addWidget(left_frame)

        # Right: Package Details & Actions Panel
        self.details_panel = QFrame()
        self.details_panel.setProperty("class", "card")
        self.details_panel.setMinimumWidth(320)
        self.details_panel.setMaximumWidth(460)

        details_layout = QVBoxLayout(self.details_panel)
        details_layout.setContentsMargins(14, 14, 14, 14)
        details_layout.setSpacing(10)

        # Detail Header
        self.detail_title = QLabel("Select a package")
        self.detail_title.setStyleSheet("font-size: 17px; font-weight: 700; color: #58a6ff;")
        details_layout.addWidget(self.detail_title)

        self.detail_badge = StatusBadge("None", "inactive")
        self.detail_badge.hide()
        details_layout.addWidget(self.detail_badge)

        # Metadata labels
        self.detail_meta = QLabel("")
        self.detail_meta.setStyleSheet("color: #8b949e; font-size: 12px; line-height: 1.4;")
        self.detail_meta.setWordWrap(True)
        details_layout.addWidget(self.detail_meta)

        # Description text
        desc_label = QLabel("Description:")
        desc_label.setStyleSheet("color: #c9d1d9; font-weight: 600; font-size: 12px; margin-top: 4px;")
        details_layout.addWidget(desc_label)

        self.detail_desc = QTextEdit()
        self.detail_desc.setReadOnly(True)
        self.detail_desc.setStyleSheet("background-color: #0d1117; font-size: 12px;")
        details_layout.addWidget(self.detail_desc)

        # Actions buttons
        self.actions_box = QVBoxLayout()
        self.actions_box.setSpacing(8)

        self.btn_install = QPushButton("Install Package")
        self.btn_install.setProperty("class", "btn-primary")
        self.btn_install.clicked.connect(self.action_install_selected)
        self.actions_box.addWidget(self.btn_install)

        self.btn_upgrade_pkg = QPushButton("Upgrade to Candidate")
        self.btn_upgrade_pkg.setProperty("class", "btn-primary")
        self.btn_upgrade_pkg.clicked.connect(self.action_upgrade_selected)
        self.actions_box.addWidget(self.btn_upgrade_pkg)

        self.btn_reinstall = QPushButton("Reinstall Package")
        self.btn_reinstall.clicked.connect(self.action_reinstall_selected)
        self.actions_box.addWidget(self.btn_reinstall)

        self.btn_remove = QPushButton("Remove Package")
        self.btn_remove.clicked.connect(self.action_remove_selected)
        self.actions_box.addWidget(self.btn_remove)

        self.btn_purge = QPushButton("Purge (Remove Configs)")
        self.btn_purge.setProperty("class", "btn-danger")
        self.btn_purge.clicked.connect(self.action_purge_selected)
        self.actions_box.addWidget(self.btn_purge)

        details_layout.addLayout(self.actions_box)
        self.reset_details_panel()

        splitter.addWidget(self.details_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

    # Search Debounce & Async Execution
    def on_search_text_changed(self, text: str):
        query = text.strip()
        if not query:
            if self.view_filter.currentIndex() == 2:
                self.table.setRowCount(0)
                self.table_status.setText("Type a package name to search.")
            return

        # Automatically switch to Search Repository view if user types in search box
        if self.view_filter.currentIndex() != 2:
            self.view_filter.blockSignals(True)
            self.view_filter.setCurrentIndex(2)
            self.view_filter.blockSignals(False)

        # Start debounce timer
        self.loading_bar.show()
        self.table_status.setText("Searching...")
        self.search_debounce.start()

    def _execute_debounced_search(self):
        query = self.search_input.text().strip()
        if not query:
            self.loading_bar.hide()
            return

        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.cancel()

        self.loading_bar.show()
        self.table_status.setText(f"Searching APT repositories for '{query}'...")

        self.current_worker = AsyncRunner.run(
            func=self.backend.search_packages,
            on_success=lambda res: self.populate_table(res, f"Found {len(res)} packages matching '{query}'"),
            on_finish=lambda: self.loading_bar.hide(),
            query=query,
            limit=100
        )

    def on_filter_changed(self, index: int):
        if index == 0:
            self.load_upgradable_packages()
        elif index == 1:
            self.load_installed_packages()
        elif index == 2:
            self._execute_debounced_search()

    def load_upgradable_packages(self):
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.cancel()

        self.loading_bar.show()
        self.table_status.setText("Scanning upgradable packages in background...")

        def on_done(res):
            self.populate_table(res, f"{len(res)} packages can be upgraded.")
            self.module.badge_updated.emit("packages", str(len(res)) if res else "")

        self.current_worker = AsyncRunner.run(
            func=self.backend.get_upgradable_packages,
            on_success=on_done,
            on_finish=lambda: self.loading_bar.hide()
        )

    def load_installed_packages(self):
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.cancel()

        self.loading_bar.show()
        self.table_status.setText("Fetching installed packages...")

        self.current_worker = AsyncRunner.run(
            func=self.backend.get_installed_packages,
            on_success=lambda res: self.populate_table(res, f"Showing {len(res)} installed packages."),
            on_finish=lambda: self.loading_bar.hide(),
            limit=150
        )

    def populate_table(self, packages: List[AptPackageInfo], status_text: str):
        self.current_packages = packages
        self.table_status.setText(status_text)
        self.table.setRowCount(len(packages))

        for row, pkg in enumerate(packages):
            item_name = QTableWidgetItem(pkg.name)
            item_name.setData(Qt.ItemDataRole.UserRole, pkg.name)
            self.table.setItem(row, 0, item_name)

            ver = pkg.version if pkg.version else ("Installed" if pkg.is_installed else "Not Installed")
            self.table.setItem(row, 1, QTableWidgetItem(ver))

            cand = pkg.candidate_version if pkg.candidate_version else "-"
            self.table.setItem(row, 2, QTableWidgetItem(cand))

            self.table.setItem(row, 3, QTableWidgetItem(pkg.summary))

        if packages:
            self.table.selectRow(0)
        else:
            self.reset_details_panel()

    def on_row_selected(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            self.reset_details_panel()
            return

        row = selected_rows[0].row()
        item = self.table.item(row, 0)
        if not item:
            return
        pkg_name = item.data(Qt.ItemDataRole.UserRole)
        self.selected_pkg_name = pkg_name

        self.detail_title.setText(pkg_name)
        self.detail_meta.setText("Loading package details...")

        # Cancel previous detail worker if pending
        if self.detail_worker and self.detail_worker.isRunning():
            self.detail_worker.cancel()

        def apply_detail(detail):
            if not detail or detail.get("name") != self.selected_pkg_name:
                return

            is_inst = detail.get("installed", False)
            is_upg = detail.get("upgradable", False)

            if is_upg:
                self.detail_badge.setStatus("Update Available", "upgradable")
            elif is_inst:
                self.detail_badge.setStatus("Installed", "installed")
            else:
                self.detail_badge.setStatus("Available in Repo", "inactive")
            self.detail_badge.show()

            meta_lines = [
                f"<b>Current:</b> {detail.get('version', 'None')}",
                f"<b>Candidate:</b> {detail.get('candidate', 'None')}",
                f"<b>Section:</b> {detail.get('section', 'General')}",
                f"<b>Homepage:</b> {detail.get('homepage', 'N/A')}"
            ]
            self.detail_meta.setText("<br>".join(meta_lines))
            self.detail_desc.setPlainText(detail.get("description", detail.get("summary", "No description available.")))

            self.btn_install.setVisible(not is_inst)
            self.btn_upgrade_pkg.setVisible(is_upg)
            self.btn_reinstall.setVisible(is_inst)
            self.btn_remove.setVisible(is_inst)
            self.btn_purge.setVisible(is_inst)

        self.detail_worker = AsyncRunner.run(
            func=self.backend.get_package_detail,
            on_success=apply_detail,
            package_name=pkg_name
        )

    def reset_details_panel(self):
        self.detail_title.setText("Select a package")
        self.detail_badge.hide()
        self.detail_meta.setText("Select any package from the list to view its dependencies, details, and actions.")
        self.detail_desc.clear()
        self.btn_install.hide()
        self.btn_upgrade_pkg.hide()
        self.btn_reinstall.hide()
        self.btn_remove.hide()
        self.btn_purge.hide()
        self.selected_pkg_name = None

    # Actions
    def action_update_index(self):
        def on_done(ok):
            self.backend.invalidate_cache()
            self.on_filter_changed(self.view_filter.currentIndex())

        self.module.request_command.emit(
            AptBackend.cmd_update(),
            True,
            "Update APT Package Index",
            on_done
        )

    def action_upgrade_all(self):
        def on_done(ok):
            self.backend.invalidate_cache()
            self.load_upgradable_packages()

        self.module.request_command.emit(
            AptBackend.cmd_upgrade(),
            True,
            "Upgrade System Packages",
            on_done
        )

    def action_install_selected(self):
        if not self.selected_pkg_name:
            return

        def on_done(ok):
            self.backend.invalidate_cache()
            self.on_row_selected()

        self.module.request_command.emit(
            AptBackend.cmd_install(self.selected_pkg_name),
            True,
            f"Install {self.selected_pkg_name}",
            on_done
        )

    def action_upgrade_selected(self):
        if not self.selected_pkg_name:
            return

        def on_done(ok):
            self.backend.invalidate_cache()
            self.on_row_selected()

        self.module.request_command.emit(
            AptBackend.cmd_install(self.selected_pkg_name),
            True,
            f"Upgrade {self.selected_pkg_name}",
            on_done
        )

    def action_reinstall_selected(self):
        if not self.selected_pkg_name:
            return

        def on_done(ok):
            self.backend.invalidate_cache()
            self.on_row_selected()

        self.module.request_command.emit(
            AptBackend.cmd_reinstall(self.selected_pkg_name),
            True,
            f"Reinstall {self.selected_pkg_name}",
            on_done
        )

    def action_remove_selected(self):
        if not self.selected_pkg_name:
            return

        def on_done(ok):
            self.backend.invalidate_cache()
            self.on_row_selected()

        self.module.request_command.emit(
            AptBackend.cmd_remove(self.selected_pkg_name),
            True,
            f"Remove {self.selected_pkg_name}",
            on_done
        )

    def action_purge_selected(self):
        if not self.selected_pkg_name:
            return

        def on_done(ok):
            self.backend.invalidate_cache()
            self.on_row_selected()

        self.module.request_command.emit(
            AptBackend.cmd_purge(self.selected_pkg_name),
            True,
            f"Purge {self.selected_pkg_name}",
            on_done
        )


    def cleanup(self):
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.cancel()
            self.current_worker.wait(500)
        if self.detail_worker and self.detail_worker.isRunning():
            self.detail_worker.cancel()
            self.detail_worker.wait(500)


class PackagesModule(BaseModule):
    """Packages and System Update Module."""

    @property
    def module_id(self) -> str:
        return "packages"

    @property
    def title(self) -> str:
        return "Packages & Updates"

    @property
    def icon_name(self) -> str:
        return "package-variant"

    @property
    def order(self) -> int:
        return 20

    def create_widget(self) -> QWidget:
        return PackagesWidget(self)

    def refresh(self):
        if self._widget and isinstance(self._widget, PackagesWidget):
            self._widget.on_filter_changed(self._widget.view_filter.currentIndex())

    def cleanup(self):
        if self._widget and hasattr(self._widget, "cleanup"):
            self._widget.cleanup()
