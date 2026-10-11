"""Module manager for dynamic discovery, loading, and management of modules."""

import importlib
import inspect
import logging
import os
import pkgutil
from pathlib import Path
from typing import Dict, List, Optional, Type
from PyQt6.QtCore import QObject, pyqtSignal

from beta_assistant.core.module_base import BaseModule
from beta_assistant.core.config import USER_MODULES_DIR

logger = logging.getLogger(__name__)


class ModuleManager(QObject):
    """Discovers, loads, and maintains the lifecycle of all assistant modules."""

    modules_changed = pyqtSignal()

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._modules: Dict[str, BaseModule] = {}
        self._app_context: dict = {}

    def set_app_context(self, context: dict):
        self._app_context = context
        for mod in self._modules.values():
            try:
                mod.initialize(self._app_context)
            except Exception as e:
                logger.error(f"Error initializing module '{mod.module_id}': {e}", exc_info=True)

    def register_module_class(self, cls: Type[BaseModule]):
        """Register a module class instance."""
        try:
            instance = cls()
            mod_id = instance.module_id
            self._modules[mod_id] = instance
        except Exception as e:
            logger.error(f"Failed to register module {cls}: {e}")

    def discover_and_load_all(self):
        """Scans built-in and user module directories for BaseModule implementations."""
        self._modules.clear()

        # 1. Register core built-in modules
        try:
            from beta_assistant.modules.dashboard import DashboardModule
            from beta_assistant.modules.packages import PackagesModule
            from beta_assistant.modules.storage import StorageModule
            from beta_assistant.modules.users import UsersModule
            from beta_assistant.modules.services import ServicesModule
            from beta_assistant.modules.logs import LogsModule

            for cls in [DashboardModule, PackagesModule, StorageModule, UsersModule, ServicesModule, LogsModule]:
                self.register_module_class(cls)
        except Exception as e:
            logger.error(f"Error loading built-in modules: {e}")

        # 2. Dynamic discovery in built-in package for future additions
        try:
            import beta_assistant.modules as builtins_pkg
            self._scan_package(builtins_pkg)
        except Exception as e:
            logger.warning(f"Error scanning package: {e}")

        # 3. Discover user plugins / custom modules from ~/.config/beta_assistant/modules
        if USER_MODULES_DIR.exists():
            self._scan_directory(USER_MODULES_DIR)

        # Initialize all loaded modules
        for mod in self._modules.values():
            try:
                mod.initialize(self._app_context)
            except Exception as e:
                logger.error(f"Error initializing module '{mod.module_id}': {e}", exc_info=True)

        self.modules_changed.emit()

    def _scan_package(self, pkg):
        """Walk package submodules and find BaseModule classes."""
        for _, module_name, is_pkg in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
            try:
                mod = importlib.import_module(module_name)
                self._extract_modules_from_module(mod)
            except Exception as e:
                logger.debug(f"Submodule inspect info for '{module_name}': {e}")

    def _scan_directory(self, directory: Path):
        """Dynamically load python files from custom modules directory."""
        for item in directory.glob("*.py"):
            if item.name.startswith("__"):
                continue
            try:
                spec = importlib.util.spec_from_file_location(item.stem, str(item))
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    self._extract_modules_from_module(mod)
            except Exception as e:
                logger.warning(f"Could not load custom module from '{item}': {e}")

    def _extract_modules_from_module(self, python_module):
        """Extract and instantiate BaseModule classes."""
        for name, cls in inspect.getmembers(python_module, inspect.isclass):
            if issubclass(cls, BaseModule) and cls is not BaseModule:
                try:
                    instance = cls()
                    mod_id = instance.module_id
                    if mod_id not in self._modules:
                        self._modules[mod_id] = instance
                        logger.info(f"Loaded dynamic module: {instance.title} ({mod_id})")
                except Exception as e:
                    logger.error(f"Failed to instantiate {name}: {e}")

    def get_module(self, module_id: str) -> Optional[BaseModule]:
        return self._modules.get(module_id)

    def get_all_modules(self) -> List[BaseModule]:
        """Returns all modules sorted by priority order."""
        return sorted(self._modules.values(), key=lambda m: m.order)
