"""Stunning animated splash screen and startup sequence for Beta Assistant."""

import os
from typing import Optional, Callable
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QFrame, QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QApplication
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, QPoint
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter, QPainterPath

from beta_assistant.core.config import APP_NAME, APP_VERSION, APP_SUBTITLE
from beta_assistant.ui.components.badges import StatusBadge


class SplashScreen(QWidget):
    """Frameless, animated startup screen with glowing branding and milestone progress."""

    finished = pyqtSignal()

    MILESTONES = [
        (15, "Initializing AlphaOS modular engine..."),
        (35, "Scanning system telemetry & hardware..."),
        (60, "Discovering administrative modules..."),
        (82, "Auditing network firewall & services..."),
        (96, "Applying appearance & security settings..."),
        (100, "Ready. Launching Beta Assistant...")
    ]

    def __init__(self, on_finish: Optional[Callable] = None, parent=None):
        super().__init__(parent)
        self.on_finish_callback = on_finish
        self.progress_value = 0
        self.milestone_index = 0
        self.is_closing = False

        # Configure frameless & translucent window
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.SplashScreen |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(540, 360)

        # Center on primary screen
        screen = QApplication.primaryScreen()
        if screen:
            screen_geo = screen.geometry()
            x = (screen_geo.width() - self.width()) // 2
            y = (screen_geo.height() - self.height()) // 2
            self.move(x, y)

        self.init_ui()
        self.setup_animations()

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(12, 12, 12, 12)

        # Outer rounded card container
        self.container = QFrame()
        self.container.setObjectName("splash_container")
        self.container.setStyleSheet("""
            QFrame#splash_container {
                background-color: #0d1117;
                border: 1px solid #30363d;
                border-radius: 16px;
            }
        """)

        # Drop shadow for floating glassmorphism depth
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(36)
        shadow.setColor(QColor(0, 210, 255, 60))
        shadow.setOffset(0, 8)
        self.container.setGraphicsEffect(shadow)

        c_layout = QVBoxLayout(self.container)
        c_layout.setContentsMargins(32, 28, 32, 26)
        c_layout.setSpacing(12)

        # 1. Top Bar: AlphaOS Badge
        top_bar = QHBoxLayout()
        badge = StatusBadge("AlphaOS", "installed")
        top_bar.addStretch()
        top_bar.addWidget(badge)
        c_layout.addLayout(top_bar)

        # 2. Glowing Logo in center
        logo_layout = QHBoxLayout()
        logo_layout.addStretch()

        self.lbl_logo = QLabel()
        self.lbl_logo.setFixedSize(68, 68)
        self.lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "assets", "alphaos_logo.svg"
        )
        if os.path.exists(logo_path):
            pix = QIcon(logo_path).pixmap(64, 64)
            self.lbl_logo.setPixmap(pix)

        # Breathing glow effect on logo
        self.logo_shadow = QGraphicsDropShadowEffect(self.lbl_logo)
        self.logo_shadow.setBlurRadius(20)
        self.logo_shadow.setColor(QColor(0, 210, 255, 180))
        self.logo_shadow.setOffset(0, 0)
        self.lbl_logo.setGraphicsEffect(self.logo_shadow)

        logo_layout.addWidget(self.lbl_logo)
        logo_layout.addStretch()
        c_layout.addLayout(logo_layout)

        # 3. Titles
        self.lbl_title = QLabel(APP_NAME)
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_title.setStyleSheet("""
            font-size: 22px;
            font-weight: 800;
            color: #58a6ff;
            letter-spacing: 0.5px;
        """)
        c_layout.addWidget(self.lbl_title)

        self.lbl_sub = QLabel(APP_SUBTITLE)
        self.lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_sub.setStyleSheet("font-size: 12px; color: #8b949e;")
        c_layout.addWidget(self.lbl_sub)

        c_layout.addSpacing(10)

        # 4. Animated Neon Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #1f6feb,
                    stop: 0.5 #00d2ff,
                    stop: 1 #7028e4
                );
                border-radius: 3px;
            }
        """)
        c_layout.addWidget(self.progress_bar)

        # 5. Status Text
        self.lbl_status = QLabel("Initializing AlphaOS Core...")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("color: #c9d1d9; font-size: 11px; font-weight: 600;")
        c_layout.addWidget(self.lbl_status)

        # 6. Subtle footer hint
        self.lbl_foot = QLabel(f"v{APP_VERSION} • Click anywhere to skip")
        self.lbl_foot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_foot.setStyleSheet("color: #484f58; font-size: 10px;")
        c_layout.addWidget(self.lbl_foot)

        root_layout.addWidget(self.container)

    def setup_animations(self):
        # 1. Entrance Fade-in on container (works across all X11 and Wayland compositors without warnings)
        self.container_opacity = QGraphicsOpacityEffect(self.container)
        self.container_opacity.setOpacity(0.0)
        self.container.setGraphicsEffect(self.container_opacity)

        self.anim_fade_in = QPropertyAnimation(self.container_opacity, b"opacity")
        self.anim_fade_in.setDuration(240)
        self.anim_fade_in.setStartValue(0.0)
        self.anim_fade_in.setEndValue(1.0)
        self.anim_fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)

        # 2. Breathing logo glow animation
        self.glow_timer = QTimer(self)
        self.glow_timer.setInterval(40)
        self.glow_direction = 1
        self.current_blur = 18
        self.glow_timer.timeout.connect(self._pulse_glow)

        # 3. Step advancement timer
        self.step_timer = QTimer(self)
        self.step_timer.setInterval(45)
        self.step_timer.timeout.connect(self._advance_progress)

    def start_animation(self):
        """Begin splash playback."""
        self.show()
        self.anim_fade_in.start()
        self.glow_timer.start()
        self.step_timer.start()

    def _pulse_glow(self):
        self.current_blur += 0.4 * self.glow_direction
        if self.current_blur >= 32:
            self.glow_direction = -1
        elif self.current_blur <= 16:
            self.glow_direction = 1
        self.logo_shadow.setBlurRadius(self.current_blur)

    def _advance_progress(self):
        if self.is_closing:
            return

        target_pct, message = self.MILESTONES[self.milestone_index]
        if self.progress_value < target_pct:
            self.progress_value += 2
            self.progress_bar.setValue(self.progress_value)
            self.lbl_status.setText(f"{message} ({self.progress_value}%)")
        else:
            if self.milestone_index < len(self.MILESTONES) - 1:
                self.milestone_index += 1
            else:
                self.progress_bar.setValue(100)
                self.finish_splash()

    def finish_splash(self):
        if self.is_closing:
            return
        self.is_closing = True
        self.step_timer.stop()
        self.glow_timer.stop()

        # Fade out container
        curr_op = self.container_opacity.opacity() if hasattr(self, "container_opacity") else 1.0
        self.anim_fade_out = QPropertyAnimation(self.container_opacity, b"opacity")
        self.anim_fade_out.setDuration(220)
        self.anim_fade_out.setStartValue(curr_op)
        self.anim_fade_out.setEndValue(0.0)
        self.anim_fade_out.setEasingCurve(QEasingCurve.Type.InCubic)
        self.anim_fade_out.finished.connect(self._on_fade_out_finished)
        self.anim_fade_out.start()

    def _on_fade_out_finished(self):
        self.close()
        self.finished.emit()
        if self.on_finish_callback:
            try:
                self.on_finish_callback()
            except Exception:
                pass

    def mousePressEvent(self, event):
        """Click to skip splash immediately."""
        self.finish_splash()

    def keyPressEvent(self, event):
        """Any key / Escape skips splash."""
        self.finish_splash()
