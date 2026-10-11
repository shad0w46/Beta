"""Collapsible live command console and execution drawer."""

from typing import Optional, List, Callable
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QPlainTextEdit, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QTextCursor, QColor

from beta_assistant.core.runner import ProcessWorker


class TerminalDrawer(QFrame):
    """Bottom slide-out console displaying real-time command output."""

    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("terminal_drawer")
        self.setMinimumHeight(0)
        self.worker: Optional[ProcessWorker] = None
        self.current_callback: Optional[Callable] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 12)
        layout.setSpacing(8)

        # Header bar
        header_layout = QHBoxLayout()

        # Title and status
        self.title_label = QLabel("Console Output")
        self.title_label.setStyleSheet("font-weight: 700; color: #58a6ff; font-size: 13px;")

        self.status_label = QLabel("Idle")
        self.status_label.setStyleSheet("color: #8b949e; font-size: 12px; margin-left: 10px;")

        header_layout.addWidget(self.title_label)
        header_layout.addWidget(self.status_label)
        header_layout.addStretch()

        # Action Buttons
        self.stop_btn = QPushButton("Stop Process")
        self.stop_btn.setProperty("class", "btn-danger")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_current_process)
        header_layout.addWidget(self.stop_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_output)
        header_layout.addWidget(self.clear_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.hide_drawer)
        header_layout.addWidget(self.close_btn)

        layout.addLayout(header_layout)

        # Indeterminate progress bar during execution
        self.busy_bar = QProgressBar()
        self.busy_bar.setFixedHeight(3)
        self.busy_bar.setRange(0, 0) # Indeterminate
        self.busy_bar.setTextVisible(False)
        self.busy_bar.hide()
        layout.addWidget(self.busy_bar)

        # Output Text Console
        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setMaximumBlockCount(2500)
        self.console.setStyleSheet("""
            QPlainTextEdit {
                background-color: #05070a;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 4px;
                font-family: monospace;
                font-size: 12px;
                line-height: 1.4;
            }
        """)
        layout.addWidget(self.console)

    def execute_command(self, cmd: List[str], as_root: bool = False,
                        title: str = "Command Execution", callback: Optional[Callable] = None):
        """Execute a command asynchronously and stream output to console."""
        self.current_callback = callback
        self.show()
        self.title_label.setText(f"Executing: {title}")
        self.status_label.setText("Running...")
        self.status_label.setStyleSheet("color: #d29922; font-weight: 600;")
        self.stop_btn.setEnabled(True)
        self.busy_bar.show()

        self.append_line(f"==> [{title}] Starting: {' '.join(cmd)} (root={as_root})", is_error=False)

        self.worker = ProcessWorker(command=cmd, as_root=as_root)
        self.worker.line_output.connect(self.append_line)
        self.worker.finished.connect(self.on_process_finished)
        self.worker.start()

    def append_line(self, line: str, is_error: bool = False):
        if is_error:
            # Highlight errors
            self.console.appendHtml(f"<span style='color: #f85149;'>{line}</span>")
        else:
            self.console.appendPlainText(line)
        self.console.moveCursor(QTextCursor.MoveOperation.End)

    def on_process_finished(self, returncode: int, message: str):
        self.busy_bar.hide()
        self.stop_btn.setEnabled(False)

        if returncode == 0:
            self.status_label.setText("Finished Successfully")
            self.status_label.setStyleSheet("color: #3fb950; font-weight: 600;")
            self.append_line(f"\n[DONE] {message}", is_error=False)
        else:
            self.status_label.setText(f"Exited with code {returncode}")
            self.status_label.setStyleSheet("color: #f85149; font-weight: 600;")
            self.append_line(f"\n[FAILED] {message}", is_error=True)

        if self.current_callback:
            try:
                self.current_callback(returncode == 0)
            except Exception:
                pass

    def stop_current_process(self):
        if self.worker and self.worker.isRunning():
            self.status_label.setText("Terminating...")
            self.worker.cancel()

    def clear_output(self):
        self.console.clear()

    def hide_drawer(self):
        parent = self.parent()
        if parent and hasattr(parent, "animate_drawer"):
            parent.animate_drawer(show=False)
        else:
            self.hide()
        self.closed.emit()
