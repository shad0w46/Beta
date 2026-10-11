"""Base class for all modular features in Beta_Assistant."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Callable
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QWidget


class BaseModule(QObject):
    """Abstract base class for all pluggable assistant modules."""

    # Signals for module-to-core communication
    # (command_list, as_root, action_title, on_finish_callback)
    request_command = pyqtSignal(list, bool, str, object)
    show_notification = pyqtSignal(str, str) # title, message
    badge_updated = pyqtSignal(str, str)     # module_id, badge_text

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.app_context: Dict[str, Any] = {}
        self._widget: Optional[QWidget] = None

    @property
    @abstractmethod
    def module_id(self) -> str:
        """Unique ID for the module, e.g., 'packages'."""
        pass

    @property
    @abstractmethod
    def title(self) -> str:
        """Display title in sidebar and headers."""
        pass

    @property
    @abstractmethod
    def icon_name(self) -> str:
        """Icon name or symbolic key."""
        pass

    @property
    def description(self) -> str:
        """Brief summary of the module's capability."""
        return ""

    @property
    def order(self) -> int:
        """Sort priority in sidebar (lower numbers appear first)."""
        return 100

    def initialize(self, app_context: Dict[str, Any]):
        """Called once during application initialization."""
        self.app_context = app_context

    @abstractmethod
    def create_widget(self) -> QWidget:
        """Constructs and returns the main QWidget view for this module."""
        pass

    def get_widget(self) -> QWidget:
        """Returns existing widget or creates one if not instantiated."""
        if self._widget is None:
            self._widget = self.create_widget()
        return self._widget

    def on_activated(self):
        """Called whenever the user switches to this module's tab."""
        pass

    def on_deactivated(self):
        """Called whenever the user navigates away from this module's tab."""
        pass

    def refresh(self):
        """Called when a refresh is requested globally or manually."""
        pass

    def cleanup(self):
        """Cleanup resources before shutdown."""
        pass
