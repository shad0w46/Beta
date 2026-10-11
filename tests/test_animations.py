"""Unit tests for UI micro-animations and AnimatedStackedWidget."""

import os
import unittest
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication, QPushButton, QLabel, QProgressBar, QFrame
from beta_assistant.ui.animations import (
    ButtonAnimationFilter, AnimatedStackedWidget, animate_progress_bar, CardHoverFilter
)

app = QApplication.instance() or QApplication([])


class TestUIAnimations(unittest.TestCase):
    """Test suite for button animations, stack transitions, and progress bar animation."""

    def test_button_animation_filter(self):
        btn = QPushButton("Test Action")
        btn.setProperty("class", "btn-primary")
        animator = ButtonAnimationFilter()
        btn.installEventFilter(animator)

        # Trigger enter and leave
        from PyQt6.QtCore import QEvent, QPointF, Qt
        from PyQt6.QtGui import QMouseEvent

        app.sendEvent(btn, QEvent(QEvent.Type.Enter))
        self.assertIsNotNone(btn.graphicsEffect())

        press_ev = QMouseEvent(QEvent.Type.MouseButtonPress, QPointF(5, 5), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        app.sendEvent(btn, press_ev)

        rel_ev = QMouseEvent(QEvent.Type.MouseButtonRelease, QPointF(5, 5), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        app.sendEvent(btn, rel_ev)

        app.sendEvent(btn, QEvent(QEvent.Type.Leave))

    def test_animated_stacked_widget(self):
        stack = AnimatedStackedWidget()
        page1 = QLabel("Page 1")
        page2 = QLabel("Page 2")
        stack.addWidget(page1)
        stack.addWidget(page2)

        # Transition to page 2
        stack.fade_to_widget(page2, direction=1)
        self.assertEqual(stack.currentWidget(), page2)

        # Transition back to page 1
        stack.fade_to_widget(page1, direction=-1)
        self.assertEqual(stack.currentWidget(), page1)

    def test_animate_progress_bar(self):
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(20)
        animate_progress_bar(bar, 80, duration=100)
        app.processEvents()

    def test_button_classes_glow(self):
        for cls_name in ["btn-primary", "btn-danger", "btn-accent", "nav-btn", ""]:
            btn = QPushButton("Action")
            btn.setProperty("class", cls_name)
            animator = ButtonAnimationFilter()
            btn.installEventFilter(animator)

            from PyQt6.QtCore import QEvent
            app.sendEvent(btn, QEvent(QEvent.Type.Enter))
            eff = btn.graphicsEffect()
            self.assertIsNotNone(eff)
            app.sendEvent(btn, QEvent(QEvent.Type.Leave))

    def test_animations_disabled_mode(self):
        from beta_assistant.core.config import set_setting
        set_setting("enable_ui_animations", False)
        try:
            btn = QPushButton("No Anim")
            animator = ButtonAnimationFilter()
            btn.installEventFilter(animator)
            from PyQt6.QtCore import QEvent
            app.sendEvent(btn, QEvent(QEvent.Type.Enter))
            self.assertIsNone(btn.graphicsEffect())

            stack = AnimatedStackedWidget()
            lbl = QLabel("Page")
            stack.addWidget(lbl)
            stack.fade_to_widget(lbl)
            self.assertEqual(stack.currentWidget(), lbl)
        finally:
            set_setting("enable_ui_animations", True)

    def test_animate_dialog_fade_in(self):
        from beta_assistant.ui.animations import animate_dialog_fade_in
        widget = QFrame()
        animate_dialog_fade_in(widget, duration=50)
        self.assertIsNotNone(widget.graphicsEffect())


if __name__ == "__main__":
    unittest.main()

