"""Dashboard module providing non-blocking telemetry and quick actions."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer

from beta_assistant.core.module_base import BaseModule
from beta_assistant.core.async_worker import AsyncRunner
from beta_assistant.core.system_info import (
    get_os_release, get_uptime_str, get_system_metrics,
    get_failed_services, count_upgradable_packages
)
from beta_assistant.ui.components.stat_widget import MetricCard
from beta_assistant.ui.components.badges import StatusBadge


class DashboardWidget(QWidget):
    """Widget rendering the Assistant Dashboard view with responsive telemetry."""

    def __init__(self, module: 'DashboardModule'):
        super().__init__()
        self.module = module
        self.init_ui()

        # Telemetry timer for fast metrics (every 2.5 seconds, CPU/RAM/Disk only)
        self.metrics_timer = QTimer(self)
        self.metrics_timer.timeout.connect(self.refresh_metrics)
        self.metrics_timer.start(2500)

        # Alerts timer for background checks (every 45 seconds)
        self.alerts_timer = QTimer(self)
        self.alerts_timer.timeout.connect(self.refresh_alerts_async)
        self.alerts_timer.start(45000)

        # Trigger first alerts check asynchronously
        QTimer.singleShot(100, self.refresh_alerts_async)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # Scroll area for responsive scaling
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # 1. Hero Card
        hero_card = QFrame()
        hero_card.setProperty("class", "card-elevated")
        hero_layout = QHBoxLayout(hero_card)
        hero_layout.setContentsMargins(20, 18, 20, 18)

        left_hero = QVBoxLayout()
        os_info = get_os_release()
        os_name = os_info.get("PRETTY_NAME", "AlphaOS")

        title = QLabel("AlphaOS Assistant")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #58a6ff;")
        subtitle = QLabel(f"Running {os_name} • Kernel {os_info.get('VERSION_CODENAME', 'Linux')}")
        subtitle.setStyleSheet("color: #8b949e; font-size: 13px; margin-top: 2px;")

        left_hero.addWidget(title)
        left_hero.addWidget(subtitle)
        hero_layout.addLayout(left_hero)
        hero_layout.addStretch()

        self.uptime_label = QLabel(f"Uptime: {get_uptime_str()}")
        self.uptime_label.setStyleSheet("color: #3fb950; font-weight: 600; font-size: 13px;")
        hero_layout.addWidget(self.uptime_label)

        layout.addWidget(hero_card)

        # 2. Metric Cards (CPU, RAM, Disk)
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(14)

        self.cpu_card = MetricCard("CPU Usage", "%")
        self.ram_card = MetricCard("Memory Usage", "%")
        self.disk_card = MetricCard("System Root Storage", "%")

        metrics_layout.addWidget(self.cpu_card)
        metrics_layout.addWidget(self.ram_card)
        metrics_layout.addWidget(self.disk_card)
        layout.addLayout(metrics_layout)

        # 3. Dynamic Alert Cards
        self.alerts_frame = QFrame()
        self.alerts_layout = QVBoxLayout(self.alerts_frame)
        self.alerts_layout.setContentsMargins(0, 0, 0, 0)
        self.alerts_layout.setSpacing(10)
        layout.addWidget(self.alerts_frame)

        # 4. Quick Actions Section
        actions_header = QLabel("Quick Management Tasks")
        actions_header.setStyleSheet("font-size: 15px; font-weight: 700; margin-top: 10px;")
        layout.addWidget(actions_header)

        grid = QGridLayout()
        grid.setSpacing(12)

        btn_update = QPushButton("⚡ Check APT Updates")
        btn_update.setFixedHeight(44)
        btn_update.clicked.connect(self.action_apt_update)

        btn_upgrade = QPushButton("🚀 Run System Upgrade")
        btn_upgrade.setProperty("class", "btn-primary")
        btn_upgrade.setFixedHeight(44)
        btn_upgrade.clicked.connect(self.action_apt_upgrade)

        btn_clean = QPushButton("🧹 Clean APT Cache")
        btn_clean.setFixedHeight(44)
        btn_clean.clicked.connect(self.action_apt_clean)

        btn_autoremove = QPushButton("🗑️ Autoremove Unused Packages")
        btn_autoremove.setFixedHeight(44)
        btn_autoremove.clicked.connect(self.action_apt_autoremove)

        btn_new_user = QPushButton("👤 Add User / Daemon Account")
        btn_new_user.setFixedHeight(44)
        btn_new_user.clicked.connect(self.action_goto_users)

        btn_new_service = QPushButton("⚙️ Create Custom Daemon / Service")
        btn_new_service.setFixedHeight(44)
        btn_new_service.clicked.connect(self.action_goto_services)

        grid.addWidget(btn_update, 0, 0)
        grid.addWidget(btn_upgrade, 0, 1)
        grid.addWidget(btn_clean, 0, 2)
        grid.addWidget(btn_autoremove, 1, 0)
        grid.addWidget(btn_new_user, 1, 1)
        grid.addWidget(btn_new_service, 1, 2)
        layout.addLayout(grid)

        layout.addStretch()
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        self.refresh_metrics()

    def refresh_metrics(self):
        metrics = get_system_metrics()
        self.cpu_card.update_metric(
            metrics["cpu_percent"],
            f"{metrics['cpu_count']} Logical Cores"
        )
        self.ram_card.update_metric(
            metrics["mem_percent"],
            f"{metrics['mem_used_gb']} GB / {metrics['mem_total_gb']} GB used"
        )
        self.disk_card.update_metric(
            metrics["disk_percent"],
            f"{metrics['disk_used_gb']} GB / {metrics['disk_total_gb']} GB used"
        )
        self.uptime_label.setText(f"Uptime: {get_uptime_str()}")

    def refresh_alerts_async(self):
        """Asynchronously query updates and failed services in background."""
        def fetch_diagnostics():
            up_count = count_upgradable_packages()
            failed = get_failed_services()
            return {"upgradable": up_count, "failed": failed}

        def on_done(data):
            self.render_alerts(data["upgradable"], data["failed"])

        AsyncRunner.run(func=fetch_diagnostics, on_success=on_done)

    def render_alerts(self, up_count: int, failed: list):
        while self.alerts_layout.count():
            item = self.alerts_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if up_count > 0:
            self.module.badge_updated.emit("packages", str(up_count))
            up_card = QFrame()
            up_card.setStyleSheet("""
                QFrame {
                    background-color: rgba(210, 153, 34, 0.12);
                    border: 1px solid rgba(210, 153, 34, 0.4);
                    border-radius: 8px;
                    padding: 8px 12px;
                }
            """)
            h = QHBoxLayout(up_card)
            msg = QLabel(f"📦 <b>{up_count} package updates are available</b> for your system.")
            msg.setStyleSheet("color: #d29922; font-size: 13px;")
            h.addWidget(msg)
            h.addStretch()

            btn = QPushButton("Upgrade All Now")
            btn.setProperty("class", "btn-primary")
            btn.clicked.connect(self.action_apt_upgrade)
            h.addWidget(btn)
            self.alerts_layout.addWidget(up_card)
        else:
            self.module.badge_updated.emit("packages", "")

        if failed:
            self.module.badge_updated.emit("services", f"!{len(failed)}")
            fail_card = QFrame()
            fail_card.setStyleSheet("""
                QFrame {
                    background-color: rgba(248, 81, 73, 0.12);
                    border: 1px solid rgba(248, 81, 73, 0.4);
                    border-radius: 8px;
                    padding: 8px 12px;
                }
            """)
            h = QHBoxLayout(fail_card)
            msg = QLabel(f"⚠️ <b>{len(failed)} failed service detected:</b> {', '.join(failed[:3])}")
            msg.setStyleSheet("color: #f85149; font-size: 13px;")
            h.addWidget(msg)
            h.addStretch()

            btn = QPushButton("Inspect in Services")
            btn.setProperty("class", "btn-danger")
            btn.clicked.connect(self.action_goto_services)
            h.addWidget(btn)
            self.alerts_layout.addWidget(fail_card)
        else:
            self.module.badge_updated.emit("services", "")

    def action_apt_update(self):
        self.module.request_command.emit(
            ["apt-get", "update"],
            True,
            "APT Package Index Update",
            lambda ok: self.refresh_alerts_async()
        )

    def action_apt_upgrade(self):
        self.module.request_command.emit(
            ["apt-get", "upgrade", "-y"],
            True,
            "System Package Upgrade",
            lambda ok: self.refresh_alerts_async()
        )

    def action_apt_clean(self):
        self.module.request_command.emit(
            ["apt-get", "clean"],
            True,
            "Clean APT Cache",
            lambda ok: self.module.show_notification.emit("APT Clean", "Cache cleaned successfully.")
        )

    def action_apt_autoremove(self):
        self.module.request_command.emit(
            ["apt-get", "autoremove", "-y"],
            True,
            "Autoremove Unused Packages",
            lambda ok: self.refresh_alerts_async()
        )

    def action_goto_users(self):
        if "switch_tab" in self.module.app_context:
            self.module.app_context["switch_tab"]("users")

    def action_goto_services(self):
        if "switch_tab" in self.module.app_context:
            self.module.app_context["switch_tab"]("services")


class DashboardModule(BaseModule):
    """System Dashboard Module implementation."""

    @property
    def module_id(self) -> str:
        return "dashboard"

    @property
    def title(self) -> str:
        return "Overview"

    @property
    def icon_name(self) -> str:
        return "view-dashboard"

    @property
    def order(self) -> int:
        return 10

    def create_widget(self) -> QWidget:
        return DashboardWidget(self)

    def refresh(self):
        if self._widget and isinstance(self._widget, DashboardWidget):
            self._widget.refresh_metrics()
            self._widget.refresh_alerts_async()
