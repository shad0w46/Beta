"""Firewall (UFW / netfilter) Management Module with non-blocking GUI."""

from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QComboBox, QMessageBox, QProgressBar, QTabWidget,
    QCheckBox, QScrollArea, QGroupBox
)
from PyQt6.QtCore import Qt, QTimer

from beta_assistant.core.module_base import BaseModule
from beta_assistant.core.async_worker import AsyncRunner, WorkerThread
from beta_assistant.modules.firewall.firewall_backend import (
    FirewallBackend, FirewallStatus, FirewallRule, ListeningSocket, ApplicationProfile
)
from beta_assistant.modules.firewall.add_rule_dialog import AddRuleDialog
from beta_assistant.ui.components.badges import StatusBadge


class FirewallWidget(QWidget):
    """Main responsive GUI for inspecting and configuring system firewall rules."""

    def __init__(self, module: 'FirewallModule'):
        super().__init__()
        self.module = module
        self.status: Optional[FirewallStatus] = None
        self.sockets: List[ListeningSocket] = []
        self.app_profiles: List[ApplicationProfile] = []
        self.worker: Optional[WorkerThread] = None
        self.worker_sockets: Optional[WorkerThread] = None

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

        hero_layout.addLayout(ctrl_row)
        main_layout.addWidget(self.hero_card)

        # Subtle progress indicator
        self.loading_bar = QProgressBar()
        self.loading_bar.setFixedHeight(2)
        self.loading_bar.setRange(0, 0)
        self.loading_bar.setTextVisible(False)
        self.loading_bar.hide()
        main_layout.addWidget(self.loading_bar)

        # 2. Main Tab Widget for Categorized Firewall Management
        self.tabs = QTabWidget()
        self.tab_rules = QWidget()
        self.tab_sockets = QWidget()
        self.tab_apps = QWidget()
        self.tab_settings = QWidget()

        self.setup_rules_tab()
        self.setup_sockets_tab()
        self.setup_apps_tab()
        self.setup_settings_tab()

        self.tabs.addTab(self.tab_rules, "📋 Active Rules")
        self.tabs.addTab(self.tab_sockets, "🔌 Listening Ports && Sockets")
        self.tabs.addTab(self.tab_apps, "📱 Application Profiles")
        self.tabs.addTab(self.tab_settings, "⚙️ Advanced Settings")
        self.tabs.currentChanged.connect(self.on_tab_changed)

        main_layout.addWidget(self.tabs)

    # -------------------------------------------------------------
    # Tab 1: Active Rules
    # -------------------------------------------------------------
    def setup_rules_tab(self):
        t_layout = QVBoxLayout(self.tab_rules)
        t_layout.setContentsMargins(12, 12, 12, 12)
        t_layout.setSpacing(10)

        # Rules Filter Bar
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

        t_layout.addLayout(rules_bar)

        self.lbl_rule_count = QLabel("Active Rules (0)")
        self.lbl_rule_count.setStyleSheet("color: #8b949e; font-size: 12px; font-weight: 600;")
        t_layout.addWidget(self.lbl_rule_count)

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
        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        t_layout.addWidget(self.table)

    # -------------------------------------------------------------
    # Tab 2: Listening Ports & Sockets
    # -------------------------------------------------------------
    def setup_sockets_tab(self):
        s_layout = QVBoxLayout(self.tab_sockets)
        s_layout.setContentsMargins(12, 12, 12, 12)
        s_layout.setSpacing(10)

        top_s_bar = QHBoxLayout()
        top_s_bar.setSpacing(10)

        self.input_socket_search = QLineEdit()
        self.input_socket_search.setPlaceholderText("Filter open ports by process name, port, or address...")
        self.input_socket_search.setFixedHeight(36)
        self.input_socket_search.setClearButtonEnabled(True)
        self.input_socket_search.textChanged.connect(self.populate_sockets_table)
        top_s_bar.addWidget(self.input_socket_search, stretch=2)

        self.chk_external_only = QCheckBox("External Only (Hide 127.0.0.1 / ::1)")
        self.chk_external_only.setChecked(False)
        self.chk_external_only.toggled.connect(self.populate_sockets_table)
        top_s_bar.addWidget(self.chk_external_only)

        btn_refresh_sock = QPushButton("⟳ Scan Sockets")
        btn_refresh_sock.setFixedHeight(36)
        btn_refresh_sock.clicked.connect(self.load_listening_sockets)
        top_s_bar.addWidget(btn_refresh_sock)

        s_layout.addLayout(top_s_bar)

        self.lbl_socket_count = QLabel("Listening Sockets (0 detected)")
        self.lbl_socket_count.setStyleSheet("color: #8b949e; font-size: 12px; font-weight: 600;")
        s_layout.addWidget(self.lbl_socket_count)

        self.table_sockets = QTableWidget()
        self.table_sockets.setColumnCount(6)
        self.table_sockets.setHorizontalHeaderLabels([
            "Port", "Proto", "Process / Daemon", "PID", "Bound Address", "Quick Firewall Action"
        ])
        self.table_sockets.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_sockets.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table_sockets.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table_sockets.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table_sockets.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table_sockets.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table_sockets.setAlternatingRowColors(True)
        self.table_sockets.verticalHeader().setVisible(False)
        self.table_sockets.verticalHeader().setDefaultSectionSize(38)
        self.table_sockets.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        s_layout.addWidget(self.table_sockets)

    # -------------------------------------------------------------
    # Tab 3: Application Profiles
    # -------------------------------------------------------------
    def setup_apps_tab(self):
        a_layout = QVBoxLayout(self.tab_apps)
        a_layout.setContentsMargins(12, 12, 12, 12)
        a_layout.setSpacing(10)

        top_a_bar = QHBoxLayout()
        top_a_bar.setSpacing(10)

        self.input_app_search = QLineEdit()
        self.input_app_search.setPlaceholderText("Search UFW application profiles (e.g. OpenSSH, Nginx, Samba)...")
        self.input_app_search.setFixedHeight(36)
        self.input_app_search.setClearButtonEnabled(True)
        self.input_app_search.textChanged.connect(self.populate_apps_table)
        top_a_bar.addWidget(self.input_app_search, stretch=2)

        btn_refresh_apps = QPushButton("⟳ Reload Profiles")
        btn_refresh_apps.setFixedHeight(36)
        btn_refresh_apps.clicked.connect(self.load_app_profiles)
        top_a_bar.addWidget(btn_refresh_apps)

        a_layout.addLayout(top_a_bar)

        self.lbl_app_count = QLabel("Registered Profiles (0)")
        self.lbl_app_count.setStyleSheet("color: #8b949e; font-size: 12px; font-weight: 600;")
        a_layout.addWidget(self.lbl_app_count)

        self.table_apps = QTableWidget()
        self.table_apps.setColumnCount(4)
        self.table_apps.setHorizontalHeaderLabels([
            "Application", "Title / Summary", "Ports", "Quick Rule Action"
        ])
        self.table_apps.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_apps.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_apps.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table_apps.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table_apps.setAlternatingRowColors(True)
        self.table_apps.verticalHeader().setVisible(False)
        self.table_apps.verticalHeader().setDefaultSectionSize(38)
        self.table_apps.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        a_layout.addWidget(self.table_apps)

    # -------------------------------------------------------------
    # Tab 4: Advanced Security Settings
    # -------------------------------------------------------------
    def setup_settings_tab(self):
        scroll = QScrollArea(self.tab_settings)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # 1. IPv6 Traffic Filtering Card
        card_ipv6 = QFrame()
        card_ipv6.setProperty("class", "card")
        c_ip6_layout = QVBoxLayout(card_ipv6)
        c_ip6_layout.setContentsMargins(16, 14, 16, 14)
        c_ip6_layout.setSpacing(8)

        row_ip6 = QHBoxLayout()
        v_ip6 = QVBoxLayout()
        lbl_ip6_t = QLabel("IPv6 Network Traffic Filtering")
        lbl_ip6_t.setStyleSheet("font-size: 14px; font-weight: 700; color: #58a6ff;")
        lbl_ip6_d = QLabel("When enabled, UFW rules apply to IPv6 and IPv4 simultaneously. When disabled, IPv6 is unfiltered or dropped.")
        lbl_ip6_d.setStyleSheet("color: #8b949e; font-size: 12px;")
        v_ip6.addWidget(lbl_ip6_t)
        v_ip6.addWidget(lbl_ip6_d)
        row_ip6.addLayout(v_ip6)
        row_ip6.addStretch()

        self.badge_ipv6 = StatusBadge("ACTIVE", "active")
        row_ip6.addWidget(self.badge_ipv6)
        self.btn_toggle_ipv6 = QPushButton("Toggle IPv6")
        self.btn_toggle_ipv6.setFixedHeight(32)
        self.btn_toggle_ipv6.clicked.connect(self.action_toggle_ipv6)
        row_ip6.addWidget(self.btn_toggle_ipv6)
        c_ip6_layout.addLayout(row_ip6)
        layout.addWidget(card_ipv6)

        # 2. ICMP / Ping Stealth Mode Card
        card_icmp = QFrame()
        card_icmp.setProperty("class", "card")
        c_icmp_layout = QVBoxLayout(card_icmp)
        c_icmp_layout.setContentsMargins(16, 14, 16, 14)
        c_icmp_layout.setSpacing(8)

        row_icmp = QHBoxLayout()
        v_icmp = QVBoxLayout()
        lbl_icmp_t = QLabel("ICMP Ping Stealth Mode")
        lbl_icmp_t.setStyleSheet("font-size: 14px; font-weight: 700; color: #58a6ff;")
        lbl_icmp_d = QLabel("Stealth mode drops incoming ICMP echo requests, hiding the AlphaOS machine from network sweeps and discovery.")
        lbl_icmp_d.setStyleSheet("color: #8b949e; font-size: 12px;")
        v_icmp.addWidget(lbl_icmp_t)
        v_icmp.addWidget(lbl_icmp_d)
        row_icmp.addLayout(v_icmp)
        row_icmp.addStretch()

        self.badge_ping = StatusBadge("RESPONSIVE", "active")
        row_icmp.addWidget(self.badge_ping)
        self.btn_toggle_ping = QPushButton("Enable Stealth Mode")
        self.btn_toggle_ping.setFixedHeight(32)
        self.btn_toggle_ping.clicked.connect(self.action_toggle_ping)
        row_icmp.addWidget(self.btn_toggle_ping)
        c_icmp_layout.addLayout(row_icmp)
        layout.addWidget(card_icmp)

        # 3. Routed / Forwarded Traffic Card
        card_routed = QFrame()
        card_routed.setProperty("class", "card")
        c_routed_layout = QVBoxLayout(card_routed)
        c_routed_layout.setContentsMargins(16, 14, 16, 14)
        c_routed_layout.setSpacing(8)

        row_routed = QHBoxLayout()
        v_routed = QVBoxLayout()
        lbl_routed_t = QLabel("Routed / Forwarded Traffic Policy")
        lbl_routed_t.setStyleSheet("font-size: 14px; font-weight: 700; color: #58a6ff;")
        lbl_routed_d = QLabel("Controls packet forwarding across network adapters (useful for VPN gateways, Docker bridges, or VMs).")
        lbl_routed_d.setStyleSheet("color: #8b949e; font-size: 12px;")
        v_routed.addWidget(lbl_routed_t)
        v_routed.addWidget(lbl_routed_d)
        row_routed.addLayout(v_routed)
        row_routed.addStretch()

        self.combo_routed = QComboBox()
        self.combo_routed.addItems(["Disabled (Deny Default)", "Allow Forwarding", "Reject Forwarding"])
        self.combo_routed.setFixedHeight(32)
        self.combo_routed.activated.connect(self.action_change_routed)
        row_routed.addWidget(self.combo_routed)
        c_routed_layout.addLayout(row_routed)
        layout.addWidget(card_routed)

        # 4. Disaster Recovery / Reset Card
        card_reset = QFrame()
        card_reset.setProperty("class", "card")
        c_reset_layout = QVBoxLayout(card_reset)
        c_reset_layout.setContentsMargins(16, 14, 16, 14)
        c_reset_layout.setSpacing(8)

        row_rst = QHBoxLayout()
        v_rst = QVBoxLayout()
        lbl_rst_t = QLabel("Disaster Recovery & Factory Reset")
        lbl_rst_t.setStyleSheet("font-size: 14px; font-weight: 700; color: #f85149;")
        lbl_rst_d = QLabel("Completely erase all custom rules and reset the Linux firewall to initial AlphaOS system defaults.")
        lbl_rst_d.setStyleSheet("color: #8b949e; font-size: 12px;")
        v_rst.addWidget(lbl_rst_t)
        v_rst.addWidget(lbl_rst_d)
        row_rst.addLayout(v_rst)
        row_rst.addStretch()

        btn_reset_all = QPushButton("⚠ Reset Firewall Rules")
        btn_reset_all.setFixedHeight(32)
        btn_reset_all.setProperty("class", "btn-danger")
        btn_reset_all.clicked.connect(self.action_reset)
        row_rst.addWidget(btn_reset_all)
        c_reset_layout.addLayout(row_rst)
        layout.addWidget(card_reset)

        layout.addStretch()
        scroll.setWidget(container)

        t_layout = QVBoxLayout(self.tab_settings)
        t_layout.setContentsMargins(0, 0, 0, 0)
        t_layout.addWidget(scroll)

    # -------------------------------------------------------------
    # Data Loading & Rendering
    # -------------------------------------------------------------
    def on_tab_changed(self, idx: int):
        if idx == 1 and not self.sockets:
            self.load_listening_sockets()
        elif idx == 2 and not self.app_profiles:
            self.load_app_profiles()

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

    def load_listening_sockets(self):
        """Scan active TCP/UDP ports via ss."""
        self.loading_bar.show()

        def on_done(socks: List[ListeningSocket]):
            self.sockets = socks
            self.populate_sockets_table()

        self.worker_sockets = AsyncRunner.run(
            func=FirewallBackend.get_listening_sockets,
            on_success=on_done,
            on_finish=lambda: self.loading_bar.hide()
        )

    def load_app_profiles(self):
        """Fetch details for all available application profiles."""
        if not self.status:
            return

        self.loading_bar.show()

        def fetch_profiles():
            profiles = []
            for app_name in self.status.available_apps:
                prof = FirewallBackend.get_app_profile_details(app_name)
                profiles.append(prof)
            return profiles

        def on_done(profs: List[ApplicationProfile]):
            self.app_profiles = profs
            self.populate_apps_table()

        AsyncRunner.run(
            func=fetch_profiles,
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

        self.btn_toggle_power.style().unpolish(self.btn_toggle_power)
        self.btn_toggle_power.style().polish(self.btn_toggle_power)

        # Policies
        self.combo_incoming.blockSignals(True)
        self.combo_outgoing.blockSignals(True)
        self.combo_logging.blockSignals(True)
        self.combo_routed.blockSignals(True)

        inc = self.status.default_incoming.lower()
        if "deny" in inc: self.combo_incoming.setCurrentIndex(0)
        elif "allow" in inc: self.combo_incoming.setCurrentIndex(1)
        elif "reject" in inc: self.combo_incoming.setCurrentIndex(2)

        out = self.status.default_outgoing.lower()
        if "allow" in out: self.combo_outgoing.setCurrentIndex(0)
        elif "deny" in out: self.combo_outgoing.setCurrentIndex(1)
        elif "reject" in out: self.combo_outgoing.setCurrentIndex(2)

        log = self.status.logging.lower()
        if "off" in log: self.combo_logging.setCurrentIndex(0)
        elif "medium" in log: self.combo_logging.setCurrentIndex(2)
        elif "high" in log: self.combo_logging.setCurrentIndex(3)
        else: self.combo_logging.setCurrentIndex(1)

        routed = self.status.default_routed.lower()
        if "allow" in routed: self.combo_routed.setCurrentIndex(1)
        elif "reject" in routed: self.combo_routed.setCurrentIndex(2)
        else: self.combo_routed.setCurrentIndex(0)

        self.combo_incoming.blockSignals(False)
        self.combo_outgoing.blockSignals(False)
        self.combo_logging.blockSignals(False)
        self.combo_routed.blockSignals(False)

        # Advanced Settings Badges
        if self.status.ipv6_enabled:
            self.badge_ipv6.setStatus("ENABLED (V6 FILTERED)", "active")
            self.btn_toggle_ipv6.setText("Disable IPv6 Filtering")
        else:
            self.badge_ipv6.setStatus("DISABLED (V4 ONLY)", "inactive")
            self.btn_toggle_ipv6.setText("Enable IPv6 Filtering")

        if self.status.ping_allowed:
            self.badge_ping.setStatus("PING RESPONSIVE", "active")
            self.btn_toggle_ping.setText("Enable Stealth Mode")
            self.btn_toggle_ping.setProperty("class", "")
        else:
            self.badge_ping.setStatus("STEALTH (PING DROPPED)", "inactive")
            self.btn_toggle_ping.setText("Disable Stealth Mode")
            self.btn_toggle_ping.setProperty("class", "btn-primary")

        self.btn_toggle_ping.style().unpolish(self.btn_toggle_ping)
        self.btn_toggle_ping.style().polish(self.btn_toggle_ping)

        self.populate_rules_table()

    # -------------------------------------------------------------
    # Populate Tables
    # -------------------------------------------------------------
    def populate_rules_table(self):
        if not self.status:
            return

        query = self.input_search.text().strip().lower()
        act_filter = self.combo_filter_action.currentIndex()

        filtered: List[FirewallRule] = []
        for r in self.status.rules:
            if act_filter == 1 and r.action_type != "allow":
                continue
            elif act_filter == 2 and r.action_type not in ("deny", "reject"):
                continue

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
            it_num = QTableWidgetItem(f"[{r.number}]")
            it_num.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, it_num)

            badge = StatusBadge(r.action.upper(), "active" if r.action_type == "allow" else "failed")
            self.table.setCellWidget(row, 1, badge)

            it_dir = QTableWidgetItem(r.direction)
            it_dir.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, it_dir)

            it_to = QTableWidgetItem(r.to_destination)
            self.table.setItem(row, 3, it_to)

            it_from = QTableWidgetItem(r.from_source)
            self.table.setItem(row, 4, it_from)

            it_cmt = QTableWidgetItem(r.comment)
            it_cmt.setForeground(Qt.GlobalColor.gray)
            self.table.setItem(row, 5, it_cmt)

            btn_del = QPushButton("Delete")
            btn_del.setFixedHeight(26)
            btn_del.setStyleSheet("font-size: 11px; padding: 2px 8px; color: #f85149;")
            num = r.number
            rule_desc = f"#{r.number} ({r.action} {r.to_destination})"
            btn_del.clicked.connect(lambda checked, n=num, d=rule_desc: self.action_delete_rule(n, d))
            self.table.setCellWidget(row, 6, btn_del)

    def populate_sockets_table(self):
        query = self.input_socket_search.text().strip().lower()
        ext_only = self.chk_external_only.isChecked()

        filtered: List[ListeningSocket] = []
        for s in self.sockets:
            if ext_only and s.is_loopback_only:
                continue

            if query:
                match = (
                    query in str(s.port) or
                    query in s.process.lower() or
                    query in s.proto.lower() or
                    query in s.local_ip.lower()
                )
                if not match:
                    continue

            filtered.append(s)

        ext_count = sum(1 for s in self.sockets if not s.is_loopback_only)
        self.lbl_socket_count.setText(
            f"Listening Sockets ({len(self.sockets)} total, {ext_count} reachable externally, {len(filtered)} shown)"
        )
        self.table_sockets.setRowCount(len(filtered))

        for row, s in enumerate(filtered):
            it_port = QTableWidgetItem(str(s.port))
            it_port.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_sockets.setItem(row, 0, it_port)

            badge_proto = StatusBadge(s.proto, "active" if s.proto == "TCP" else "installed")
            self.table_sockets.setCellWidget(row, 1, badge_proto)

            it_proc = QTableWidgetItem(s.process)
            f_proc = it_proc.font()
            f_proc.setBold(True)
            it_proc.setFont(f_proc)
            self.table_sockets.setItem(row, 2, it_proc)

            it_pid = QTableWidgetItem(str(s.pid) if s.pid else "-")
            it_pid.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_sockets.setItem(row, 3, it_pid)

            addr_str = f"{s.local_ip} (Local Only)" if s.is_loopback_only else f"{s.local_ip} (External)"
            it_addr = QTableWidgetItem(addr_str)
            if not s.is_loopback_only:
                it_addr.setForeground(Qt.GlobalColor.cyan)
            self.table_sockets.setItem(row, 4, it_addr)

            # Quick Allow / Deny buttons
            btn_box = QWidget()
            box_ly = QHBoxLayout(btn_box)
            box_ly.setContentsMargins(4, 2, 4, 2)
            box_ly.setSpacing(6)

            btn_allow = QPushButton("+ Allow")
            btn_allow.setFixedHeight(24)
            btn_allow.setStyleSheet("font-size: 11px; padding: 1px 6px; color: #3fb950;")
            btn_allow.clicked.connect(lambda checked, sk=s: self.action_quick_rule(sk, "allow"))
            box_ly.addWidget(btn_allow)

            btn_deny = QPushButton("⛔ Deny")
            btn_deny.setFixedHeight(24)
            btn_deny.setStyleSheet("font-size: 11px; padding: 1px 6px; color: #f85149;")
            btn_deny.clicked.connect(lambda checked, sk=s: self.action_quick_rule(sk, "deny"))
            box_ly.addWidget(btn_deny)

            self.table_sockets.setCellWidget(row, 5, btn_box)

    def populate_apps_table(self):
        query = self.input_app_search.text().strip().lower()

        filtered: List[ApplicationProfile] = []
        for p in self.app_profiles:
            if query:
                match = (
                    query in p.name.lower() or
                    query in p.title.lower() or
                    query in p.description.lower() or
                    query in p.ports.lower()
                )
                if not match:
                    continue
            filtered.append(p)

        self.lbl_app_count.setText(f"Application Profiles ({len(self.app_profiles)} profiles available)")
        self.table_apps.setRowCount(len(filtered))

        for row, p in enumerate(filtered):
            it_name = QTableWidgetItem(p.name)
            f_name = it_name.font()
            f_name.setBold(True)
            it_name.setFont(f_name)
            it_name.setForeground(Qt.GlobalColor.cyan)
            self.table_apps.setItem(row, 0, it_name)

            desc = p.title if p.title != p.name else p.description
            it_desc = QTableWidgetItem(desc or "-")
            self.table_apps.setItem(row, 1, it_desc)

            it_ports = QTableWidgetItem(p.ports or "Dynamic")
            it_ports.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_apps.setItem(row, 2, it_ports)

            btn_box = QWidget()
            box_ly = QHBoxLayout(btn_box)
            box_ly.setContentsMargins(4, 2, 4, 2)
            box_ly.setSpacing(6)

            btn_allow = QPushButton("+ Allow App")
            btn_allow.setFixedHeight(24)
            btn_allow.setStyleSheet("font-size: 11px; padding: 1px 6px; color: #3fb950;")
            btn_allow.clicked.connect(lambda checked, aname=p.name: self.action_app_rule(aname, "allow"))
            box_ly.addWidget(btn_allow)

            btn_deny = QPushButton("⛔ Deny App")
            btn_deny.setFixedHeight(24)
            btn_deny.setStyleSheet("font-size: 11px; padding: 1px 6px; color: #f85149;")
            btn_deny.clicked.connect(lambda checked, aname=p.name: self.action_app_rule(aname, "deny"))
            box_ly.addWidget(btn_deny)

            self.table_apps.setCellWidget(row, 3, btn_box)

    # -------------------------------------------------------------
    # User Actions
    # -------------------------------------------------------------
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
        from beta_assistant.core.config import get_setting
        if get_setting("confirm_critical_actions", True):
            reply = QMessageBox.question(
                self,
                "Confirm Firewall Reset",
                "Are you sure you want to reset all UFW firewall rules to factory defaults?\n\nThis will remove all custom rules.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self.module.request_command.emit(
            FirewallBackend.cmd_reset(),
            True,
            "Reset Firewall Rules to Defaults",
            lambda ok: self.load_status()
        )

    def action_delete_rule(self, rule_num: int, rule_desc: str):
        from beta_assistant.core.config import get_setting
        if get_setting("confirm_critical_actions", True):
            reply = QMessageBox.question(
                self,
                "Delete Firewall Rule",
                f"Are you sure you want to delete rule {rule_desc}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

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

    def action_quick_rule(self, sock: ListeningSocket, action: str):
        proto_str = sock.proto.lower()
        cmd = FirewallBackend.cmd_add_rule(
            port_or_app=str(sock.port),
            action=action,
            protocol=proto_str,
            direction="in",
            comment=f"{action.capitalize()} {sock.process} on port {sock.port}"
        )
        self.module.request_command.emit(
            cmd,
            True,
            f"{action.upper()} Port {sock.port}/{proto_str.upper()} ({sock.process})",
            lambda ok: self.load_status()
        )

    def action_app_rule(self, app_name: str, action: str):
        cmd = [FirewallBackend.get_ufw_path(), action, app_name]
        self.module.request_command.emit(
            cmd,
            True,
            f"{action.upper()} Application Profile: {app_name}",
            lambda ok: self.load_status()
        )

    def action_toggle_ipv6(self):
        if not self.status:
            return
        new_state = not self.status.ipv6_enabled
        cmd = FirewallBackend.cmd_set_ipv6(new_state)
        self.module.request_command.emit(
            cmd,
            True,
            f"{'Enable' if new_state else 'Disable'} IPv6 Firewall Filtering",
            lambda ok: self.load_status()
        )

    def action_toggle_ping(self):
        if not self.status:
            return
        new_state = not self.status.ping_allowed
        cmd = FirewallBackend.cmd_set_ping(new_state)
        self.module.request_command.emit(
            cmd,
            True,
            f"{'Allow' if new_state else 'Drop (Stealth)'} ICMP Echo Requests",
            lambda ok: self.load_status()
        )

    def action_change_routed(self, idx: int):
        policies = ["deny", "allow", "reject"]
        policy = policies[idx]
        cmd = FirewallBackend.cmd_set_routed(policy)
        self.module.request_command.emit(
            cmd,
            True,
            f"Set Routed Traffic Policy to {policy.upper()}",
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
            if self._widget.tabs.currentIndex() == 1:
                self._widget.load_listening_sockets()
            elif self._widget.tabs.currentIndex() == 2:
                self._widget.load_app_profiles()
