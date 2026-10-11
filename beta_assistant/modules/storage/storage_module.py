"""Storage analysis and system junk cleaner module."""

from typing import List, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QProgressBar, QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer

from beta_assistant.core.module_base import BaseModule
from beta_assistant.core.async_worker import AsyncRunner
from beta_assistant.modules.storage.storage_backend import StorageBackend, MountInfo


class StorageWidget(QWidget):
    """Main view for storage metrics and one-click system junk cleaning."""

    def __init__(self, module: 'StorageModule'):
        super().__init__()
        self.module = module
        self.init_ui()
        QTimer.singleShot(50, self.refresh_all)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(14)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # 1. Hero Cleaner Card
        cleaner_hero = QFrame()
        cleaner_hero.setProperty("class", "card-elevated")
        hero_layout = QHBoxLayout(cleaner_hero)
        hero_layout.setContentsMargins(20, 16, 20, 16)

        left_hero = QVBoxLayout()
        title = QLabel("System Junk Cleaner")
        title.setStyleSheet("font-size: 19px; font-weight: 800; color: #58a6ff;")
        self.junk_summary_lbl = QLabel("Scanning cleanable system caches...")
        self.junk_summary_lbl.setStyleSheet("color: #8b949e; font-size: 13px; margin-top: 2px;")
        left_hero.addWidget(title)
        left_hero.addWidget(self.junk_summary_lbl)
        hero_layout.addLayout(left_hero)
        hero_layout.addStretch()

        self.btn_clean_all = QPushButton("🚀 Clean All Junk")
        self.btn_clean_all.setProperty("class", "btn-primary")
        self.btn_clean_all.setFixedHeight(44)
        self.btn_clean_all.clicked.connect(self.action_clean_all)
        hero_layout.addWidget(self.btn_clean_all)

        layout.addWidget(cleaner_hero)

        # 2. Junk Item Cards Grid
        junk_header = QLabel("Cleanable System Caches")
        junk_header.setStyleSheet("font-size: 15px; font-weight: 700;")
        layout.addWidget(junk_header)

        grid = QGridLayout()
        grid.setSpacing(12)

        # Card: APT Packages
        self.card_apt = self._create_cleaner_card(
            title="APT Package Archives",
            desc="Downloaded .deb installer packages in /var/cache/apt/archives",
            clean_btn_text="Clean APT Cache",
            on_clean=self.action_clean_apt
        )
        grid.addWidget(self.card_apt["frame"], 0, 0)

        # Card: Journal Logs
        self.card_journal = self._create_cleaner_card(
            title="Systemd Journal Logs",
            desc="Historical rotated system logs beyond 3 days",
            clean_btn_text="Vacuum Logs",
            on_clean=self.action_vacuum_journal
        )
        grid.addWidget(self.card_journal["frame"], 0, 1)

        # Card: Thumbnails
        self.card_thumb = self._create_cleaner_card(
            title="User Thumbnail Cache",
            desc="Cached image & file previews in ~/.cache/thumbnails",
            clean_btn_text="Purge Thumbnails",
            on_clean=self.action_clean_thumbnails
        )
        grid.addWidget(self.card_thumb["frame"], 1, 0)

        # Card: Autoremove
        self.card_auto = self._create_cleaner_card(
            title="Orphaned Dependencies",
            desc="Obsolete libraries and old kernels no longer needed",
            clean_btn_text="Autoremove Unused",
            on_clean=self.action_autoremove
        )
        grid.addWidget(self.card_auto["frame"], 1, 1)

        layout.addLayout(grid)

        # 3. Mounted Partitions Section
        mounts_header = QLabel("Mounted Filesystems & Partitions")
        mounts_header.setStyleSheet("font-size: 15px; font-weight: 700; margin-top: 10px;")
        layout.addWidget(mounts_header)

        self.mounts_container = QFrame()
        self.mounts_layout = QVBoxLayout(self.mounts_container)
        self.mounts_layout.setContentsMargins(0, 0, 0, 0)
        self.mounts_layout.setSpacing(10)
        layout.addWidget(self.mounts_container)

        layout.addStretch()
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def _create_cleaner_card(self, title: str, desc: str, clean_btn_text: str, on_clean) -> Dict[str, Any]:
        frame = QFrame()
        frame.setProperty("class", "card")
        ly = QVBoxLayout(frame)
        ly.setContentsMargins(14, 12, 14, 12)
        ly.setSpacing(6)

        h_top = QHBoxLayout()
        lbl_t = QLabel(title)
        lbl_t.setStyleSheet("font-weight: 700; font-size: 13px;")
        lbl_val = QLabel("0 MB")
        lbl_val.setStyleSheet("font-weight: 700; font-size: 15px; color: #58a6ff;")
        h_top.addWidget(lbl_t)
        h_top.addStretch()
        h_top.addWidget(lbl_val)
        ly.addLayout(h_top)

        lbl_d = QLabel(desc)
        lbl_d.setStyleSheet("color: #8b949e; font-size: 11px;")
        lbl_d.setWordWrap(True)
        ly.addWidget(lbl_d)

        btn = QPushButton(clean_btn_text)
        btn.clicked.connect(on_clean)
        ly.addWidget(btn)

        return {"frame": frame, "val_label": lbl_val, "btn": btn}

    def refresh_all(self):
        # Async fetch partitions
        AsyncRunner.run(
            func=StorageBackend.get_mounted_partitions,
            on_success=self.render_partitions
        )

        # Async scan junk
        AsyncRunner.run(
            func=StorageBackend.scan_junk_sizes,
            on_success=self.render_junk_metrics
        )

    def render_partitions(self, partitions: List[MountInfo]):
        while self.mounts_layout.count():
            item = self.mounts_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for m in partitions:
            card = QFrame()
            card.setProperty("class", "card")
            c_ly = QVBoxLayout(card)
            c_ly.setContentsMargins(14, 12, 14, 12)
            c_ly.setSpacing(6)

            h_top = QHBoxLayout()
            title = QLabel(f"<b>{m.mountpoint}</b> <span style='color: #8b949e;'>({m.device} • {m.fstype})</span>")
            title.setStyleSheet("font-size: 13px;")

            stats = QLabel(f"<b>{m.used_gb} GB</b> / {m.total_gb} GB ({m.free_gb} GB Free)")
            stats.setStyleSheet("font-size: 12px; color: #c9d1d9;")

            h_top.addWidget(title)
            h_top.addStretch()
            h_top.addWidget(stats)
            c_ly.addLayout(h_top)

            bar = QProgressBar()
            bar.setFixedHeight(8)
            bar.setTextVisible(False)
            bar.setValue(int(m.percent))

            color = "#f85149" if m.percent >= 90 else ("#d29922" if m.percent >= 75 else "#388bfd")
            bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: #21262d;
                    border: none;
                    border-radius: 4px;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 4px;
                }}
            """)
            c_ly.addWidget(bar)
            self.mounts_layout.addWidget(card)

    def render_junk_metrics(self, data: Dict[str, Any]):
        self.junk_summary_lbl.setText(f"Found approximately <b>{data['total_display']}</b> of safe cleanable data.")
        self.card_apt["val_label"].setText(data["apt_display"])
        self.card_journal["val_label"].setText(data["journal_display"])
        self.card_thumb["val_label"].setText(data["thumb_display"])

    # Actions
    def action_clean_all(self):
        self.module.request_command.emit(
            StorageBackend.cmd_clean_all(),
            True,
            "Clean All System Junk",
            lambda ok: self.refresh_all()
        )

    def action_clean_apt(self):
        self.module.request_command.emit(
            StorageBackend.cmd_clean_apt(),
            True,
            "Clean APT Package Cache",
            lambda ok: self.refresh_all()
        )

    def action_vacuum_journal(self):
        self.module.request_command.emit(
            StorageBackend.cmd_vacuum_journal(),
            True,
            "Vacuum Systemd Journal (Keep 3 Days)",
            lambda ok: self.refresh_all()
        )

    def action_clean_thumbnails(self):
        self.module.request_command.emit(
            ["sh", "-c", "rm -rf ~/.cache/thumbnails/*"],
            False,
            "Purge Thumbnail Cache",
            lambda ok: self.refresh_all()
        )

    def action_autoremove(self):
        self.module.request_command.emit(
            StorageBackend.cmd_autoremove(),
            True,
            "Autoremove Orphaned Packages",
            lambda ok: self.refresh_all()
        )


class StorageModule(BaseModule):
    """Storage Telemetry and System Cleaner Module."""

    @property
    def module_id(self) -> str:
        return "storage"

    @property
    def title(self) -> str:
        return "Storage & Cleaner"

    @property
    def icon_name(self) -> str:
        return "harddisk"

    @property
    def order(self) -> int:
        return 35

    def create_widget(self) -> QWidget:
        return StorageWidget(self)

    def refresh(self):
        if self._widget and isinstance(self._widget, StorageWidget):
            self._widget.refresh_all()
