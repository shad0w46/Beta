"""Reusable status badges and chip components."""

from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt


class StatusBadge(QLabel):
    """Pill badge showing status with distinct color styling."""

    STYLES = {
        "active": "background-color: rgba(46, 160, 67, 0.15); color: #3fb950; border: 1px solid rgba(46, 160, 67, 0.4);",
        "running": "background-color: rgba(46, 160, 67, 0.15); color: #3fb950; border: 1px solid rgba(46, 160, 67, 0.4);",
        "installed": "background-color: rgba(56, 139, 253, 0.15); color: #58a6ff; border: 1px solid rgba(56, 139, 253, 0.4);",
        "upgradable": "background-color: rgba(210, 153, 34, 0.15); color: #d29922; border: 1px solid rgba(210, 153, 34, 0.4);",
        "failed": "background-color: rgba(248, 81, 73, 0.15); color: #f85149; border: 1px solid rgba(248, 81, 73, 0.4);",
        "inactive": "background-color: rgba(139, 148, 158, 0.15); color: #8b949e; border: 1px solid rgba(139, 148, 158, 0.3);",
        "standard": "background-color: rgba(56, 139, 253, 0.15); color: #58a6ff; border: 1px solid rgba(56, 139, 253, 0.4);",
        "daemon": "background-color: rgba(163, 113, 247, 0.15); color: #bc8cff; border: 1px solid rgba(163, 113, 247, 0.4);",
        "nologin": "background-color: rgba(219, 109, 40, 0.15); color: #f0883e; border: 1px solid rgba(219, 109, 40, 0.4);",
        "system": "background-color: rgba(163, 113, 247, 0.15); color: #bc8cff; border: 1px solid rgba(163, 113, 247, 0.4);",
    }

    def __init__(self, text: str, status_type: str = "inactive", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStatus(text, status_type)

    def setStatus(self, text: str, status_type: str):
        self.setText(f" {text} ")
        st = status_type.lower()
        style_rule = self.STYLES.get(st, self.STYLES["inactive"])
        self.setStyleSheet(f"""
            QLabel {{
                {style_rule}
                border-radius: 10px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: 600;
            }}
        """)
