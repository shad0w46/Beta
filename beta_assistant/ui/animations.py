"""Comprehensive UI and button micro-animations system for Beta Assistant."""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QPushButton, QStackedWidget, QProgressBar,
    QGraphicsDropShadowEffect, QGraphicsOpacityEffect
)
from PyQt6.QtCore import (
    Qt, QObject, QEvent, QPropertyAnimation, QEasingCurve,
    QParallelAnimationGroup, QPoint
)
from PyQt6.QtGui import QColor

from beta_assistant.core.config import get_setting


class ButtonAnimationFilter(QObject):
    """Event filter adding smooth hover glow and tactile click micro-animations to buttons."""

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if not get_setting("enable_ui_animations", True):
            return super().eventFilter(watched, event)

        if isinstance(watched, QPushButton) and watched.isEnabled():
            if event.type() == QEvent.Type.Enter:
                self._on_enter(watched)
            elif event.type() == QEvent.Type.Leave:
                self._on_leave(watched)
            elif event.type() == QEvent.Type.MouseButtonPress:
                self._on_press(watched)
            elif event.type() == QEvent.Type.MouseButtonRelease:
                self._on_release(watched)

        return super().eventFilter(watched, event)

    def _ensure_shadow_effect(self, btn: QPushButton) -> QGraphicsDropShadowEffect:
        eff = btn.graphicsEffect()
        if not isinstance(eff, QGraphicsDropShadowEffect):
            eff = QGraphicsDropShadowEffect(btn)
            eff.setBlurRadius(0)
            eff.setOffset(0, 2)

            # Palette matching button class
            cls_prop = btn.property("class") or ""
            btn_id = btn.objectName() or ""
            if "btn-danger" in cls_prop:
                eff.setColor(QColor(248, 81, 73, 160))
            elif "btn-primary" in cls_prop:
                eff.setColor(QColor(46, 160, 67, 180))
            elif "btn-accent" in cls_prop:
                eff.setColor(QColor(31, 111, 235, 180))
            elif "nav-btn" in cls_prop:
                eff.setColor(QColor(0, 210, 255, 120))
            elif "btn_toggle" in btn_id:
                eff.setColor(QColor(0, 210, 255, 140))
            else:
                # Standard and header buttons
                eff.setColor(QColor(88, 166, 255, 120))

            btn.setGraphicsEffect(eff)
        return eff

    def _on_enter(self, btn: QPushButton):
        eff = self._ensure_shadow_effect(btn)
        anim = getattr(btn, "_btn_glow_anim", None)
        if anim and anim.state() == QPropertyAnimation.State.Running:
            anim.stop()

        anim = QPropertyAnimation(eff, b"blurRadius")
        anim.setDuration(160)
        anim.setStartValue(eff.blurRadius())
        anim.setEndValue(16)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        btn._btn_glow_anim = anim
        anim.start()

    def _on_leave(self, btn: QPushButton):
        eff = btn.graphicsEffect()
        if not isinstance(eff, QGraphicsDropShadowEffect):
            return

        anim = getattr(btn, "_btn_glow_anim", None)
        if anim and anim.state() == QPropertyAnimation.State.Running:
            anim.stop()

        anim = QPropertyAnimation(eff, b"blurRadius")
        anim.setDuration(160)
        anim.setStartValue(eff.blurRadius())
        anim.setEndValue(0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        btn._btn_glow_anim = anim
        anim.start()

    def _on_press(self, btn: QPushButton):
        eff = btn.graphicsEffect()
        if isinstance(eff, QGraphicsDropShadowEffect):
            eff.setOffset(0, 0)
            eff.setBlurRadius(6)

    def _on_release(self, btn: QPushButton):
        eff = btn.graphicsEffect()
        if isinstance(eff, QGraphicsDropShadowEffect):
            eff.setOffset(0, 2)
            eff.setBlurRadius(16)


class AnimatedStackedWidget(QStackedWidget):
    """StackedWidget with smooth horizontal glide and cross-fade page transitions."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.transition_duration = 180
        self._anim_group: Optional[QParallelAnimationGroup] = None
        self._current_effect: Optional[QGraphicsOpacityEffect] = None

    def fade_to_widget(self, target_widget: QWidget, direction: int = 1):
        """Cross-fade and subtle slide transition to target widget."""
        curr_widget = self.currentWidget()
        if curr_widget == target_widget or not target_widget:
            self.setCurrentWidget(target_widget)
            return

        if not get_setting("enable_ui_animations", True):
            self.setCurrentWidget(target_widget)
            return

        # Stop ongoing transition if running
        if self._anim_group and self._anim_group.state() == QParallelAnimationGroup.State.Running:
            self._anim_group.stop()
            if self._current_effect and self.currentWidget():
                self.currentWidget().setGraphicsEffect(None)

        self.setCurrentWidget(target_widget)

        # Setup opacity effect on incoming page
        eff = QGraphicsOpacityEffect(target_widget)
        eff.setOpacity(0.15)
        target_widget.setGraphicsEffect(eff)
        self._current_effect = eff

        # 1. Fade animation
        anim_fade = QPropertyAnimation(eff, b"opacity")
        anim_fade.setDuration(self.transition_duration)
        anim_fade.setStartValue(0.15)
        anim_fade.setEndValue(1.0)
        anim_fade.setEasingCurve(QEasingCurve.Type.OutCubic)

        # 2. Subtle horizontal glide animation (18px)
        offset_x = 18 * (1 if direction >= 0 else -1)
        anim_pos = QPropertyAnimation(target_widget, b"pos")
        anim_pos.setDuration(self.transition_duration)
        anim_pos.setStartValue(QPoint(offset_x, 0))
        anim_pos.setEndValue(QPoint(0, 0))
        anim_pos.setEasingCurve(QEasingCurve.Type.OutCubic)

        group = QParallelAnimationGroup(self)
        group.addAnimation(anim_fade)
        group.addAnimation(anim_pos)

        def on_finished():
            target_widget.setGraphicsEffect(None)
            self._current_effect = None
            self._anim_group = None

        group.finished.connect(on_finished)
        self._anim_group = group
        group.start()


def animate_progress_bar(bar: QProgressBar, target_value: int, duration: int = 280):
    """Smoothly animate progress bar value interpolation."""
    current = bar.value()
    if current == target_value:
        return

    if not get_setting("enable_ui_animations", True):
        bar.setValue(target_value)
        return

    anim = getattr(bar, "_smooth_anim", None)
    if anim and anim.state() == QPropertyAnimation.State.Running:
        anim.stop()

    anim = QPropertyAnimation(bar, b"value")
    anim.setDuration(duration)
    anim.setStartValue(current)
    anim.setEndValue(target_value)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    bar._smooth_anim = anim
    anim.start()


class CardHoverFilter(QObject):
    """Adds subtle floating elevation and glow when hovering over metric and content cards."""

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if not get_setting("enable_ui_animations", True):
            return super().eventFilter(watched, event)

        if isinstance(watched, QWidget):
            cls_prop = watched.property("class") or ""
            if "card" in cls_prop:
                if event.type() == QEvent.Type.Enter:
                    self._elevate_card(watched, True)
                elif event.type() == QEvent.Type.Leave:
                    self._elevate_card(watched, False)

        return super().eventFilter(watched, event)

    def _elevate_card(self, card: QWidget, enter: bool):
        eff = card.graphicsEffect()
        if not isinstance(eff, QGraphicsDropShadowEffect):
            eff = QGraphicsDropShadowEffect(card)
            eff.setOffset(0, 4)
            eff.setColor(QColor(0, 210, 255, 60))
            eff.setBlurRadius(0)
            card.setGraphicsEffect(eff)

        anim = getattr(card, "_card_glow_anim", None)
        if anim and anim.state() == QPropertyAnimation.State.Running:
            anim.stop()

        anim = QPropertyAnimation(eff, b"blurRadius")
        anim.setDuration(180)
        anim.setStartValue(eff.blurRadius())
        anim.setEndValue(20 if enter else 0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        card._card_glow_anim = anim
        anim.start()


def animate_dialog_fade_in(dialog: QWidget, duration: int = 180):
    """Subtle and sleek fade-in animation for modal dialogs."""
    from PyQt6.QtCore import QTimer
    eff = QGraphicsOpacityEffect(dialog)
    eff.setOpacity(0.0)
    dialog.setGraphicsEffect(eff)

    anim = QPropertyAnimation(eff, b"opacity")
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    anim.finished.connect(lambda: QTimer.singleShot(0, lambda: dialog.setGraphicsEffect(None)))
    dialog._fade_in_anim = anim
    anim.start()


