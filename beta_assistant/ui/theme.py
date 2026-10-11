"""Modern AlphaOS QSS theme and styling system."""

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
    min-width: 210px;
    max-width: 210px;
}

QFrame#brand_header {
    background-color: #161b22;
    padding: 12px 10px;
    border-bottom: 1px solid #30363d;
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
    padding: 10px 16px;
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

QPushButton.btn-primary:pressed {
    background-color: #196c2e;
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
    font-family: "JetBrains Mono", "Cascadia Code", "Fira Code", monospace;
    font-size: 12px;
    padding: 8px;
}

/* Progress Bars */
QProgressBar {
    background-color: #21262d;
    border: 1px solid #30363d;
    border-radius: 4px;
    text-align: center;
    color: #c9d1d9;
    font-size: 11px;
    font-weight: 600;
    height: 12px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1f6feb, stop:1 #58a6ff);
    border-radius: 3px;
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

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
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

QCheckBox::indicator:checked {
    background-color: #1f6feb;
    border-color: #58a6ff;
    image: none;
}

QRadioButton::indicator:checked {
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

QTabBar::tab:hover:!selected {
    background: #21262d;
    color: #c9d1d9;
}
"""
