"""User and Daemon Account Management module with async loading and live filtering."""

from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QSplitter, QComboBox, QMessageBox, QDialog,
    QCheckBox, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer

from beta_assistant.core.module_base import BaseModule
from beta_assistant.core.async_worker import AsyncRunner, WorkerThread
from beta_assistant.modules.users.user_backend import UserBackend, UserInfo
from beta_assistant.modules.users.create_user_dialog import CreateUserDialog
from beta_assistant.ui.components.badges import StatusBadge


class UsersWidget(QWidget):
    """Main view for User, Daemon, and No-Login accounts with responsive UI."""

    def __init__(self, module: 'UsersModule'):
        super().__init__()
        self.module = module
        self.all_users: List[UserInfo] = []
        self.filtered_users: List[UserInfo] = []
        self.selected_user: Optional[UserInfo] = None
        self.load_worker: Optional[WorkerThread] = None

        self.init_ui()
        QTimer.singleShot(50, self.load_users)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(10)

        # 1. Top Bar: Search, Category Filters, and Create Action
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        # Search filter
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter users live by name, UID, or shell...")
        self.search_input.setFixedHeight(36)
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.apply_filter)
        top_bar.addWidget(self.search_input, stretch=2)

        # Category Filter
        self.combo_type = QComboBox()
        self.combo_type.addItems([
            "All Accounts",
            "Standard / Human Users",
            "System & Daemon Accounts",
            "No-Login Accounts"
        ])
        self.combo_type.setFixedHeight(36)
        self.combo_type.currentIndexChanged.connect(self.apply_filter)
        top_bar.addWidget(self.combo_type)

        # Refresh
        btn_refresh = QPushButton("Refresh")
        btn_refresh.setFixedHeight(36)
        btn_refresh.clicked.connect(self.load_users)
        top_bar.addWidget(btn_refresh)

        # Create New User / Daemon
        btn_create = QPushButton("+ Create User / Daemon")
        btn_create.setProperty("class", "btn-primary")
        btn_create.setFixedHeight(36)
        btn_create.clicked.connect(self.open_create_dialog)
        top_bar.addWidget(btn_create)

        main_layout.addLayout(top_bar)

        # Subtle Loading Progress Indicator
        self.loading_bar = QProgressBar()
        self.loading_bar.setFixedHeight(2)
        self.loading_bar.setRange(0, 0)
        self.loading_bar.setTextVisible(False)
        self.loading_bar.hide()
        main_layout.addWidget(self.loading_bar)

        # 2. Splitter: Users Table on Left, Details & Actions on Right
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(5)

        # Left: Table
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #8b949e; font-size: 12px; font-weight: 500;")
        left_layout.addWidget(self.status_label)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Username", "Account Type", "UID", "Shell", "Home Directory"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 130)
        self.table.setColumnWidth(1, 190)
        self.table.setColumnWidth(2, 60)
        self.table.setColumnWidth(3, 140)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.itemSelectionChanged.connect(self.on_user_selected)
        left_layout.addWidget(self.table)

        splitter.addWidget(left_frame)

        # Right: Details & Operations Panel
        self.details_panel = QFrame()
        self.details_panel.setProperty("class", "card")
        self.details_panel.setMinimumWidth(320)
        self.details_panel.setMaximumWidth(440)

        details_layout = QVBoxLayout(self.details_panel)
        details_layout.setContentsMargins(14, 14, 14, 14)
        details_layout.setSpacing(10)

        self.detail_user_name = QLabel("Select an account")
        self.detail_user_name.setStyleSheet("font-size: 18px; font-weight: 700; color: #58a6ff;")
        details_layout.addWidget(self.detail_user_name)

        self.detail_badge = StatusBadge("None", "inactive")
        self.detail_badge.hide()
        details_layout.addWidget(self.detail_badge)

        self.detail_meta = QLabel("")
        self.detail_meta.setStyleSheet("color: #c9d1d9; font-size: 12px; line-height: 1.5;")
        self.detail_meta.setWordWrap(True)
        details_layout.addWidget(self.detail_meta)

        self.lbl_groups = QLabel("Groups: -")
        self.lbl_groups.setStyleSheet("color: #8b949e; font-size: 12px;")
        self.lbl_groups.setWordWrap(True)
        details_layout.addWidget(self.lbl_groups)

        details_layout.addStretch()

        # Actions Box
        self.actions_box = QVBoxLayout()
        self.actions_box.setSpacing(8)

        self.btn_edit_groups = QPushButton("Edit Supplementary Groups")
        self.btn_edit_groups.clicked.connect(self.action_edit_groups)
        self.actions_box.addWidget(self.btn_edit_groups)

        self.btn_change_shell = QPushButton("Change Shell")
        self.btn_change_shell.clicked.connect(self.action_change_shell)
        self.actions_box.addWidget(self.btn_change_shell)

        self.btn_lock = QPushButton("Lock Account")
        self.btn_lock.clicked.connect(self.action_lock_account)
        self.actions_box.addWidget(self.btn_lock)

        self.btn_unlock = QPushButton("Unlock Account")
        self.btn_unlock.clicked.connect(self.action_unlock_account)
        self.actions_box.addWidget(self.btn_unlock)

        self.btn_delete = QPushButton("Delete User Account")
        self.btn_delete.setProperty("class", "btn-danger")
        self.btn_delete.clicked.connect(self.action_delete_account)
        self.actions_box.addWidget(self.btn_delete)

        details_layout.addLayout(self.actions_box)
        self.reset_details_panel()

        splitter.addWidget(self.details_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

    def load_users(self):
        if self.load_worker and self.load_worker.isRunning():
            self.load_worker.cancel()

        self.loading_bar.show()
        self.status_label.setText("Reading user database...")

        def on_done(users):
            self.all_users = users
            self.apply_filter()

        self.load_worker = AsyncRunner.run(
            func=UserBackend.get_all_users,
            on_success=on_done,
            on_finish=lambda: self.loading_bar.hide()
        )

    def apply_filter(self):
        query = self.search_input.text().strip().lower()
        type_idx = self.combo_type.currentIndex()

        filtered = []
        for u in self.all_users:
            if type_idx == 1 and not u.is_standard:
                continue
            elif type_idx == 2 and not u.is_system:
                continue
            elif type_idx == 3 and not u.is_nologin:
                continue

            if query:
                match = (
                    query in u.username.lower() or
                    query in u.comment.lower() or
                    query in u.shell.lower() or
                    query in str(u.uid)
                )
                if not match:
                    continue

            filtered.append(u)

        self.filtered_users = filtered
        self.populate_table()

    def populate_table(self):
        self.status_label.setText(f"Showing {len(self.filtered_users)} accounts.")
        self.table.setRowCount(len(self.filtered_users))

        for row, u in enumerate(self.filtered_users):
            item_name = QTableWidgetItem(u.username)
            item_name.setData(Qt.ItemDataRole.UserRole, u.username)
            self.table.setItem(row, 0, item_name)

            type_text = u.account_type_display
            item_type = QTableWidgetItem(type_text)
            self.table.setItem(row, 1, item_type)

            item_uid = QTableWidgetItem(str(u.uid))
            self.table.setItem(row, 2, item_uid)

            item_shell = QTableWidgetItem(u.shell)
            self.table.setItem(row, 3, item_shell)

            item_home = QTableWidgetItem(u.home_dir)
            self.table.setItem(row, 4, item_home)

        if self.filtered_users:
            self.table.selectRow(0)
        else:
            self.reset_details_panel()

    def on_user_selected(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            self.reset_details_panel()
            return

        row = selected_rows[0].row()
        item = self.table.item(row, 0)
        if not item:
            return
        username = item.data(Qt.ItemDataRole.UserRole)
        for u in self.filtered_users:
            if u.username == username:
                self.selected_user = u
                break
        else:
            return

        u = self.selected_user
        self.detail_user_name.setText(u.username)

        if u.is_standard:
            self.detail_badge.setStatus("Standard User", "standard")
        elif u.is_nologin:
            self.detail_badge.setStatus("No-Login Account", "nologin")
        elif u.is_system:
            self.detail_badge.setStatus("System Daemon", "daemon")
        else:
            self.detail_badge.setStatus("Custom", "inactive")
        self.detail_badge.show()

        meta = [
            f"<b>Full Name / Comment:</b> {u.comment or 'None'}",
            f"<b>UID / GID:</b> {u.uid} / {u.gid}",
            f"<b>Home:</b> {u.home_dir}",
            f"<b>Shell:</b> {u.shell}"
        ]
        self.detail_meta.setText("<br>".join(meta))
        self.lbl_groups.setText(f"<b>Groups:</b> {', '.join(u.groups) if u.groups else 'None'}")

        self.btn_edit_groups.show()
        self.btn_change_shell.show()
        self.btn_lock.show()
        self.btn_unlock.show()
        self.btn_delete.setVisible(u.username != "root")

    def reset_details_panel(self):
        self.detail_user_name.setText("Select an account")
        self.detail_badge.hide()
        self.detail_meta.setText("Select an account to view and manage permissions, shell, and groups.")
        self.lbl_groups.setText("")
        self.btn_edit_groups.hide()
        self.btn_change_shell.hide()
        self.btn_lock.hide()
        self.btn_unlock.hide()
        self.btn_delete.hide()
        self.selected_user = None

    def open_create_dialog(self):
        dialog = CreateUserDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_creation_data()
            cmd = UserBackend.cmd_create_user(
                username=data["username"],
                comment=data["comment"],
                shell=data["shell"],
                home_dir=data["home"],
                create_home=data["create_home"],
                is_system=data["is_system"],
                groups=data["groups"]
            )

            def after_create(success: bool):
                if success and data.get("password"):
                    self.module.request_command.emit(
                        UserBackend.cmd_set_password(data["username"], data["password"]),
                        True,
                        f"Set Password for {data['username']}",
                        lambda ok: self.load_users()
                    )
                else:
                    self.load_users()

            self.module.request_command.emit(
                cmd,
                True,
                f"Create User '{data['username']}'",
                after_create
            )

    def action_lock_account(self):
        if not self.selected_user:
            return
        self.module.request_command.emit(
            UserBackend.cmd_lock_user(self.selected_user.username),
            True,
            f"Lock Account '{self.selected_user.username}'",
            lambda ok: self.load_users()
        )

    def action_unlock_account(self):
        if not self.selected_user:
            return
        self.module.request_command.emit(
            UserBackend.cmd_unlock_user(self.selected_user.username),
            True,
            f"Unlock Account '{self.selected_user.username}'",
            lambda ok: self.load_users()
        )

    def action_delete_account(self):
        if not self.selected_user:
            return
        uname = self.selected_user.username
        reply = QMessageBox.question(
            self,
            "Confirm Account Deletion",
            f"Are you sure you want to delete user account '{uname}'?\n\nDo you also want to remove their home directory ({self.selected_user.home_dir})?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
        )

        if reply == QMessageBox.StandardButton.Cancel:
            return

        remove_home = (reply == QMessageBox.StandardButton.Yes)
        self.module.request_command.emit(
            UserBackend.cmd_delete_user(uname, remove_home=remove_home),
            True,
            f"Delete User '{uname}'",
            lambda ok: self.load_users()
        )

    def action_change_shell(self):
        if not self.selected_user:
            return
        shells = UserBackend.get_available_shells()
        curr = self.selected_user.shell

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Change Shell for {self.selected_user.username}")
        dialog.setFixedWidth(360)
        ly = QVBoxLayout(dialog)
        ly.addWidget(QLabel("Select New Shell:"))
        cb = QComboBox()
        cb.addItems(shells)
        if curr in shells:
            cb.setCurrentText(curr)
        ly.addWidget(cb)

        h_btn = QHBoxLayout()
        h_btn.addStretch()
        b_canc = QPushButton("Cancel")
        b_canc.clicked.connect(dialog.reject)
        b_ok = QPushButton("Apply Shell")
        b_ok.setProperty("class", "btn-primary")
        b_ok.clicked.connect(dialog.accept)
        h_btn.addWidget(b_canc)
        h_btn.addWidget(b_ok)
        ly.addLayout(h_btn)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_shell = cb.currentText()
            self.module.request_command.emit(
                UserBackend.cmd_change_shell(self.selected_user.username, new_shell),
                True,
                f"Change Shell to {new_shell}",
                lambda ok: self.load_users()
            )

    def action_edit_groups(self):
        if not self.selected_user:
            return
        all_grps = UserBackend.get_all_groups()
        curr_grps = set(self.selected_user.groups)

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Groups: {self.selected_user.username}")
        dialog.setFixedWidth(400)
        ly = QVBoxLayout(dialog)
        ly.addWidget(QLabel("Select supplementary groups:"))

        scroll = QFrame()
        scroll_ly = QVBoxLayout(scroll)
        cbs = {}
        for g in all_grps[:30]:
            chk = QCheckBox(g)
            chk.setChecked(g in curr_grps)
            cbs[g] = chk
            scroll_ly.addWidget(chk)
        ly.addWidget(scroll)

        h_btn = QHBoxLayout()
        h_btn.addStretch()
        b_canc = QPushButton("Cancel")
        b_canc.clicked.connect(dialog.reject)
        b_ok = QPushButton("Save Groups")
        b_ok.setProperty("class", "btn-primary")
        b_ok.clicked.connect(dialog.accept)
        h_btn.addWidget(b_canc)
        h_btn.addWidget(b_ok)
        ly.addLayout(h_btn)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_grps = [g for g, c in cbs.items() if c.isChecked()]
            self.module.request_command.emit(
                UserBackend.cmd_modify_groups(self.selected_user.username, selected_grps),
                True,
                f"Update Groups for {self.selected_user.username}",
                lambda ok: self.load_users()
            )


    def cleanup(self):
        if self.load_worker and self.load_worker.isRunning():
            self.load_worker.cancel()
            self.load_worker.wait(500)


class UsersModule(BaseModule):
    """User and Daemon Accounts Management Module."""

    @property
    def module_id(self) -> str:
        return "users"

    @property
    def title(self) -> str:
        return "User & Daemons"

    @property
    def icon_name(self) -> str:
        return "account-group"

    @property
    def order(self) -> int:
        return 30

    def create_widget(self) -> QWidget:
        return UsersWidget(self)

    def refresh(self):
        if self._widget and isinstance(self._widget, UsersWidget):
            self._widget.load_users()

    def cleanup(self):
        if self._widget and hasattr(self._widget, "cleanup"):
            self._widget.cleanup()
