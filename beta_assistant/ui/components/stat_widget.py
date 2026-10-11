"""Stat metric card widget with progress indicator and theme awareness."""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt


class MetricCard(QFrame):
    """Modern metric card displaying a KPI value and progress bar."""

    def __init__(self, title: str, unit: str = "%", parent=None):
        super().__init__(parent)
        self.setProperty("class", "card")
        self.unit = unit

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        # Top row: Title and Value
        top_row = QHBoxLayout()
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #8b949e; font-size: 12px; font-weight: 500;")

        self.value_label = QLabel(f"0{unit}")
        self.value_label.setStyleSheet("font-size: 18px; font-weight: 700;")
        top_row.addWidget(self.title_label)
        top_row.addStretch()
        top_row.addWidget(self.value_label)
        layout.addLayout(top_row)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        layout.addWidget(self.progress_bar)

        # Subtitle
        self.subtitle_label = QLabel("")
        self.subtitle_label.setStyleSheet("color: #8b949e; font-size: 11px;")
        layout.addWidget(self.subtitle_label)

    def update_metric(self, value: float, subtitle: str = ""):
        int_val = int(value)
        self.progress_bar.setValue(int_val)
        self.value_label.setText(f"{value:.1f}{self.unit}")
        if subtitle:
            self.subtitle_label.setText(subtitle)

        # Visual color threshold on progress bar
        if int_val >= 90:
            chunk_color = "#f85149"
        elif int_val >= 75:
            chunk_color = "#d29922"
        else:
            chunk_color = "#00d2ff"

        self.progress_bar.setStyleSheet(f"""
            QProgressBar::chunk {{
                background-color: {chunk_color};
                border-radius: 4px;
            }}
        """)
