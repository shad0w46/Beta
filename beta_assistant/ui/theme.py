"""Cohesive Dark and Light Theme system for AlphaOS Beta Assistant."""

ALPHAOS_DARK_THEME = """
/* Global Window & Base */
QWidget {
    background-color: #0d1117;
    color: #e6edf3;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif;
    font-size: 13px;
    selection-background-color: #1f6feb;
    selection-color: #ffffff;
}

/* Sidebar Navigation */
QFrame#sidebar {
    background-color: #161b22;
    border-right: 1px solid #30363d;
    min-width: 220px;
    max-width: 220px;
}

QPushButton.nav-btn {
    text-align: left;
    padding: 10px 14px;
    border-radius: 6px;
    border: none;
    background-color: transparent;
    color: #8b949e;
    font-size: 13px;
    font-weight: 500;
}

QPushButton.nav-btn:hover {
    background-color: #21262d;
    color: #f0f6fc;
}

QPushButton.nav-btn:checked {
    background-color: #1f6feb;
    color: #ffffff;
    font-weight: 600;
}

/* Header Bar */
QFrame#top_header {
    background-color: #161b22;
    border-bottom: 1px solid #30363d;
    padding: 8px 16px;
}

/* Control Buttons */
QPushButton#btn_toggle_sidebar, QPushButton#btn_theme_toggle {
    background-color: #21262d;
    border: 1px solid #30363d;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 600;
    color: #c9d1d9;
    padding: 5px 10px;
}

QPushButton#btn_toggle_sidebar:hover, QPushButton#btn_theme_toggle:hover {
    background-color: #30363d;
    color: #58a6ff;
    border-color: #58a6ff;
}

/* Indeterminate Loading Bar */
QProgressBar {
    background-color: #161b22;
    border: none;
    height: 2px;
}

QProgressBar::chunk {
    background-color: #00d2ff;
}

/* Cards & Content Panels */
QFrame.card {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 14px;
}

QFrame.card-elevated {
    background-color: #21262d;
    border: 1px solid #38424d;
    border-radius: 8px;
    padding: 16px;
}

/* Standard Buttons */
QPushButton {
    background-color: #21262d;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #30363d;
    border-color: #8b949e;
    color: #f0f6fc;
}

QPushButton:pressed {
    background-color: #1c2128;
}

QPushButton:disabled {
    background-color: #161b22;
    color: #484f58;
    border-color: #21262d;
}

/* Primary Action Buttons */
QPushButton.btn-primary {
    background-color: #238636;
    color: #ffffff;
    border: 1px solid #2ea043;
    font-weight: 600;
}

QPushButton.btn-primary:hover {
    background-color: #2ea043;
    border-color: #3fb950;
}

/* Accent Buttons */
QPushButton.btn-accent {
    background-color: #1f6feb;
    color: #ffffff;
    border: 1px solid #388bfd;
    font-weight: 600;
}

QPushButton.btn-accent:hover {
    background-color: #388bfd;
}

/* Danger Buttons */
QPushButton.btn-danger {
    background-color: #da3633;
    color: #ffffff;
    border: 1px solid #f85149;
    font-weight: 600;
}

QPushButton.btn-danger:hover {
    background-color: #f85149;
}

/* Line Edits & Search Boxes */
QLineEdit {
    background-color: #0d1117;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 7px 12px;
}

QLineEdit:focus {
    border: 1px solid #58a6ff;
    background-color: #0d1117;
}

/* ComboBox */
QComboBox {
    background-color: #21262d;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 10px;
}

QComboBox:hover {
    border-color: #8b949e;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #161b22;
    color: #c9d1d9;
    selection-background-color: #1f6feb;
    border: 1px solid #30363d;
    outline: none;
}

/* Tables */
QTableWidget {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    gridline-color: #21262d;
    outline: none;
}

QTableWidget::item {
    padding: 6px 10px;
    border-bottom: 1px solid #21262d;
}

QTableWidget::item:selected {
    background-color: #1f2a3a;
    color: #58a6ff;
}

QHeaderView::section {
    background-color: #161b22;
    color: #8b949e;
    font-weight: 600;
    padding: 8px 10px;
    border: none;
    border-bottom: 2px solid #30363d;
    border-right: 1px solid #21262d;
}

/* Text Edit / Logs / Terminal */
QPlainTextEdit, QTextEdit {
    background-color: #0d1117;
    color: #58a6ff;
    border: 1px solid #30363d;
    border-radius: 6px;
    font-family: monospace;
    font-size: 12px;
    padding: 8px;
}

/* Scrollbars */
QScrollBar:vertical {
    background: #0d1117;
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #30363d;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #8b949e;
}

QScrollBar:horizontal {
    background: #0d1117;
    height: 8px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background: #30363d;
    min-width: 20px;
    border-radius: 4px;
}

/* Status Drawer */
QFrame#terminal_drawer {
    background-color: #0d1117;
    border-top: 2px solid #1f6feb;
}

/* Dialogs */
QDialog {
    background-color: #161b22;
}

/* GroupBox */
QGroupBox {
    border: 1px solid #30363d;
    border-radius: 6px;
    margin-top: 14px;
    padding-top: 14px;
    font-weight: 600;
    color: #f0f6fc;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    color: #58a6ff;
}

/* Checkbox and Radio Buttons */
QCheckBox, QRadioButton {
    color: #c9d1d9;
    spacing: 8px;
    font-size: 13px;
}

QCheckBox:hover, QRadioButton:hover {
    color: #f0f6fc;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #484f58;
    background-color: #0d1117;
    border-radius: 3px;
}

QRadioButton::indicator {
    border-radius: 8px;
}

QCheckBox::indicator:hover, QRadioButton::indicator:hover {
    border-color: #58a6ff;
}

QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background-color: #1f6feb;
    border-color: #58a6ff;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #30363d;
    border-radius: 6px;
    background-color: #161b22;
    top: -1px;
}

QTabBar::tab {
    background: #0d1117;
    color: #8b949e;
    border: 1px solid #30363d;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 8px 16px;
    margin-right: 4px;
    font-weight: 600;
}

QTabBar::tab:selected {
    background: #161b22;
    color: #58a6ff;
    border-bottom: 2px solid #1f6feb;
}
"""

ALPHAOS_LIGHT_THEME = """
/* Global Window & Base */
QWidget {
    background-color: #f6f8fa;
    color: #1f2328;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif;
    font-size: 13px;
    selection-background-color: #0969da;
    selection-color: #ffffff;
}

/* Sidebar Navigation */
QFrame#sidebar {
    background-color: #ffffff;
    border-right: 1px solid #d0d7de;
    min-width: 220px;
    max-width: 220px;
}

QPushButton.nav-btn {
    text-align: left;
    padding: 10px 14px;
    border-radius: 6px;
    border: none;
    background-color: transparent;
    color: #656d76;
    font-size: 13px;
    font-weight: 500;
}

QPushButton.nav-btn:hover {
    background-color: #f3f4f6;
    color: #1f2328;
}

QPushButton.nav-btn:checked {
    background-color: #0969da;
    color: #ffffff;
    font-weight: 600;
}

/* Header Bar */
QFrame#top_header {
    background-color: #ffffff;
    border-bottom: 1px solid #d0d7de;
    padding: 8px 16px;
}

/* Control Buttons */
QPushButton#btn_toggle_sidebar, QPushButton#btn_theme_toggle {
    background-color: #f6f8fa;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 600;
    color: #1f2328;
    padding: 5px 10px;
}

QPushButton#btn_toggle_sidebar:hover, QPushButton#btn_theme_toggle:hover {
    background-color: #e5e7eb;
    color: #0969da;
    border-color: #0969da;
}

/* Indeterminate Loading Bar */
QProgressBar {
    background-color: #eaeef2;
    border: none;
    height: 2px;
}

QProgressBar::chunk {
    background-color: #0969da;
}

/* Cards & Content Panels */
QFrame.card {
    background-color: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 8px;
    padding: 14px;
}

QFrame.card-elevated {
    background-color: #ffffff;
    border: 1px solid #c0c6cc;
    border-radius: 8px;
    padding: 16px;
}

/* Standard Buttons */
QPushButton {
    background-color: #f6f8fa;
    color: #1f2328;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #e5e7eb;
    border-color: #8c959f;
    color: #1f2328;
}

QPushButton:pressed {
    background-color: #d0d7de;
}

QPushButton:disabled {
    background-color: #f6f8fa;
    color: #8c959f;
    border-color: #e1e4e8;
}

/* Primary Action Buttons */
QPushButton.btn-primary {
    background-color: #1f883d;
    color: #ffffff;
    border: 1px solid #1a7f37;
    font-weight: 600;
}

QPushButton.btn-primary:hover {
    background-color: #1a7f37;
    border-color: #156f30;
}

/* Accent Buttons */
QPushButton.btn-accent {
    background-color: #0969da;
    color: #ffffff;
    border: 1px solid #0860ca;
    font-weight: 600;
}

QPushButton.btn-accent:hover {
    background-color: #0860ca;
}

/* Danger Buttons */
QPushButton.btn-danger {
    background-color: #cf222e;
    color: #ffffff;
    border: 1px solid #b62324;
    font-weight: 600;
}

QPushButton.btn-danger:hover {
    background-color: #b62324;
}

/* Line Edits & Search Boxes */
QLineEdit {
    background-color: #ffffff;
    color: #1f2328;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    padding: 7px 12px;
}

QLineEdit:focus {
    border: 1px solid #0969da;
    background-color: #ffffff;
}

/* ComboBox */
QComboBox {
    background-color: #ffffff;
    color: #1f2328;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    padding: 6px 10px;
}

QComboBox:hover {
    border-color: #8c959f;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #1f2328;
    selection-background-color: #0969da;
    selection-color: #ffffff;
    border: 1px solid #d0d7de;
    outline: none;
}

/* Tables */
QTableWidget {
    background-color: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    gridline-color: #eaeef2;
    outline: none;
}

QTableWidget::item {
    padding: 6px 10px;
    border-bottom: 1px solid #eaeef2;
}

QTableWidget::item:selected {
    background-color: #ddf4ff;
    color: #0969da;
}

QHeaderView::section {
    background-color: #f6f8fa;
    color: #656d76;
    font-weight: 600;
    padding: 8px 10px;
    border: none;
    border-bottom: 2px solid #d0d7de;
    border-right: 1px solid #eaeef2;
}

/* Text Edit / Logs / Terminal (Retains high-contrast dark console) */
QPlainTextEdit, QTextEdit {
    background-color: #0a0e14;
    color: #58a6ff;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    font-family: monospace;
    font-size: 12px;
    padding: 8px;
}

/* Scrollbars */
QScrollBar:vertical {
    background: #f6f8fa;
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #c0c6cc;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #8c959f;
}

QScrollBar:horizontal {
    background: #f6f8fa;
    height: 8px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background: #c0c6cc;
    min-width: 20px;
    border-radius: 4px;
}

/* Status Drawer */
QFrame#terminal_drawer {
    background-color: #0a0e14;
    border-top: 2px solid #0969da;
}

/* Dialogs */
QDialog {
    background-color: #ffffff;
}

/* GroupBox */
QGroupBox {
    border: 1px solid #d0d7de;
    border-radius: 6px;
    margin-top: 14px;
    padding-top: 14px;
    font-weight: 600;
    color: #1f2328;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    color: #0969da;
}

/* Checkbox and Radio Buttons */
QCheckBox, QRadioButton {
    color: #1f2328;
    spacing: 8px;
    font-size: 13px;
}

QCheckBox:hover, QRadioButton:hover {
    color: #0969da;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #d0d7de;
    background-color: #ffffff;
    border-radius: 3px;
}

QRadioButton::indicator {
    border-radius: 8px;
}

QCheckBox::indicator:hover, QRadioButton::indicator:hover {
    border-color: #0969da;
}

QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background-color: #0969da;
    border-color: #0969da;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #d0d7de;
    border-radius: 6px;
    background-color: #ffffff;
    top: -1px;
}

QTabBar::tab {
    background: #f6f8fa;
    color: #656d76;
    border: 1px solid #d0d7de;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 8px 16px;
    margin-right: 4px;
    font-weight: 600;
}

QTabBar::tab:selected {
    background: #ffffff;
    color: #0969da;
    border-bottom: 2px solid #0969da;
}
"""
