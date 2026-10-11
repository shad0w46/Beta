"""Package and Update Manager module using APT backend."""

from typing import List, Optional, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QSplitter, QTextEdit, QComboBox, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer

from beta_assistant.core.module_base import BaseModule
from beta_assistant.modules.packages.apt_backend import AptBackend, AptPackageInfo
from beta_assistant.ui.components.badges import StatusBadge


class PackagesWidget(QWidget):
    """Main view for APT package searching, inspection, and operations."""

    def __init__(self, module: 'PackagesModule'):
        super().__init__()
        self.module = module
        self.backend = AptBackend()
        self.current_packages: List[AptPackageInfo] = []
        self.selected_pkg_name: Optional[str] = None

        self.init_ui()

        # Load initial upgradable packages or installed packages
        QTimer.singleShot(100, self.load_upgradable_packages)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # 1. Top Bar: Search and Global Actions
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        # Search Box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search packages in APT (e.g. nginx, python3, git, htop)...")
        self.search_input.setFixedHeight(36)
        self.search_input.returnPressed.connect(self.perform_search)
        top_bar.addWidget(self.search_input, stretch=3)

        self.search_btn = QPushButton("Search")
        self.search_btn.setProperty("class", "btn-accent")
        self.search_btn.setFixedHeight(36)
        self.search_btn.clicked.connect(self.perform_search)
        top_bar.addWidget(self.search_btn)

        # Filter View Combo
        self.view_filter = QComboBox()
        self.view_filter.addItems(["Upgradable Updates", "Installed Packages", "Search Repository"])
        self.view_filter.setFixedHeight(36)
        self.view_filter.currentIndexChanged.connect(self.on_filter_changed)
        top_bar.addWidget(self.view_filter)

        top_bar.addSpacing(10)

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

        # 2. Main Content Splitter: Table on Left, Details on Right
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(4)

        # Left: Packages Table
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        self.table_status = QLabel("Loading packages...")
        self.table_status.setStyleSheet("color: #8b949e; font-size: 12px;")
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
        self.details_panel.setMaximumWidth(450)

        details_layout = QVBoxLayout(self.details_panel)
        details_layout.setContentsMargins(14, 14, 14, 14)
        details_layout.setSpacing(12)

        # Detail Header
        self.detail_title = QLabel("Select a package")
        self.detail_title.setStyleSheet("font-size: 17px; font-weight: 700; color: #58a6ff;")
        details_layout.addWidget(self.detail_title)

        self.detail_badge = StatusBadge("None", "inactive")
        self.detail_badge.hide()
        details_layout.addWidget(self.detail_badge)

        # Metadata labels
        self.detail_meta = QLabel("")
        self.detail_meta.setStyleSheet("color: #8b949e; font-size: 12px;")
        self.detail_meta.setWordWrap(True)
        details_layout.addWidget(self.detail_meta)

        # Description text
        desc_label = QLabel("Description:")
        desc_label.setStyleSheet("color: #c9d1d9; font-weight: 600; font-size: 12px; margin-top: 6px;")
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

    def on_filter_changed(self, index: int):
        if index == 0:
            self.load_upgradable_packages()
        elif index == 1:
            self.load_installed_packages()
        elif index == 2:
            self.perform_search()

    def perform_search(self):
        query = self.search_input.text().strip()
        if not query:
            self.table_status.setText("Enter a keyword to search.")
            return

        self.table_status.setText(f"Searching APT repositories for '{query}'...")
        results = self.backend.search_packages(query, limit=100)
        self.populate_table(results, f"Found {len(results)} packages matching '{query}'")

    def load_upgradable_packages(self):
        self.table_status.setText("Scanning upgradable packages...")
        upgradable = self.backend.get_upgradable_packages()
        self.populate_table(upgradable, f"{len(upgradable)} packages can be upgraded.")
        self.module.badge_updated.emit("packages", str(len(upgradable)) if upgradable else "")

    def load_installed_packages(self):
        self.table_status.setText("Fetching installed packages...")
        installed = self.backend.get_installed_packages(limit=150)
        self.populate_table(installed, f"Showing {len(installed)} installed packages.")

    def populate_table(self, packages: List[AptPackageInfo], status_text: str):
        self.current_packages = packages
        self.table_status.setText(status_text)
        self.table.setRowCount(len(packages))

        for row, pkg in enumerate(packages):
            # Name
            item_name = QTableWidgetItem(pkg.name)
            item_name.setData(Qt.ItemDataRole.UserRole, pkg.name)
            self.table.setItem(row, 0, item_name)

            # Current version
            ver = pkg.version if pkg.version else ("Installed" if pkg.is_installed else "Not Installed")
            self.table.setItem(row, 1, QTableWidgetItem(ver))

            # Candidate version
            cand = pkg.candidate_version if pkg.candidate_version else "-"
            self.table.setItem(row, 2, QTableWidgetItem(cand))

            # Summary
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
        pkg_name = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.selected_pkg_name = pkg_name

        # Query full detail
        detail = self.backend.get_package_detail(pkg_name)
        if not detail:
            return

        self.detail_title.setText(pkg_name)
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

        # Update button states
        self.btn_install.setVisible(not is_inst)
        self.btn_upgrade_pkg.setVisible(is_upg)
        self.btn_reinstall.setVisible(is_inst)
        self.btn_remove.setVisible(is_inst)
        self.btn_purge.setVisible(is_inst)

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
        self.module.request_command.emit(
            AptBackend.cmd_update(),
            True,
            "Update APT Package Index",
            lambda ok: self.on_filter_changed(self.view_filter.currentIndex())
        )

    def action_upgrade_all(self):
        self.module.request_command.emit(
            AptBackend.cmd_upgrade(),
            True,
            "Upgrade System Packages",
            lambda ok: self.load_upgradable_packages()
        )

    def action_install_selected(self):
        if not self.selected_pkg_name:
            return
        self.module.request_command.emit(
            AptBackend.cmd_install(self.selected_pkg_name),
            True,
            f"Install {self.selected_pkg_name}",
            lambda ok: self.on_row_selected()
        )

    def action_upgrade_selected(self):
        if not self.selected_pkg_name:
            return
        self.module.request_command.emit(
            AptBackend.cmd_install(self.selected_pkg_name),
            True,
            f"Upgrade {self.selected_pkg_name}",
            lambda ok: self.on_row_selected()
        )

    def action_reinstall_selected(self):
        if not self.selected_pkg_name:
            return
        self.module.request_command.emit(
            AptBackend.cmd_reinstall(self.selected_pkg_name),
            True,
            f"Reinstall {self.selected_pkg_name}",
            lambda ok: self.on_row_selected()
        )

    def action_remove_selected(self):
        if not self.selected_pkg_name:
            return
        self.module.request_command.emit(
            AptBackend.cmd_remove(self.selected_pkg_name),
            True,
            f"Remove {self.selected_pkg_name}",
            lambda ok: self.on_row_selected()
        )

    def action_purge_selected(self):
        if not self.selected_pkg_name:
            return
        self.module.request_command.emit(
            AptBackend.cmd_purge(self.selected_pkg_name),
            True,
            f"Purge {self.selected_pkg_name}",
            lambda ok: self.on_row_selected()
        )


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
