"""Configuration, settings persistence, and constants for Beta_Assistant."""

import json
import os
from pathlib import Path
from typing import Any, Dict

APP_NAME = "Beta Assistant"
APP_VERSION = "1.1.0"
APP_SUBTITLE = "AlphaOS System Administration & Control Center"
APP_ID = "org.alphaos.beta_assistant"

HOME_DIR = Path.home()
CONFIG_DIR = HOME_DIR / ".config" / "beta_assistant"
LOG_DIR = CONFIG_DIR / "logs"
USER_MODULES_DIR = CONFIG_DIR / "modules"
SETTINGS_FILE = CONFIG_DIR / "settings.json"

# Ensure dirs exist
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
USER_MODULES_DIR.mkdir(parents=True, exist_ok=True)

# Theme constants
THEME_DARK = "dark"
THEME_LIGHT = "light"
DEFAULT_THEME = THEME_DARK

# Default application settings
DEFAULT_SETTINGS: Dict[str, Any] = {
    "theme": DEFAULT_THEME,
    "default_module": "dashboard",
    "auto_refresh_seconds": 3,
    "auto_open_terminal": True,
    "confirm_critical_actions": True,
    "compact_sidebar": False,
    "enable_startup_animation": True,
    "enable_ui_animations": True,
}


def load_all_settings() -> Dict[str, Any]:
    """Read all saved settings merged with defaults."""
    settings = dict(DEFAULT_SETTINGS)
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r") as f:
                saved = json.load(f)
                if isinstance(saved, dict):
                    settings.update(saved)
        except Exception:
            pass
    return settings


def save_all_settings(settings: Dict[str, Any]):
    """Persist settings dictionary to disk."""
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=2)
    except Exception:
        pass


def get_setting(key: str, default: Any = None) -> Any:
    """Retrieve single setting value."""
    all_settings = load_all_settings()
    return all_settings.get(key, default if default is not None else DEFAULT_SETTINGS.get(key))


def set_setting(key: str, value: Any):
    """Update and persist a single setting value."""
    settings = load_all_settings()
    settings[key] = value
    save_all_settings(settings)


def get_saved_theme() -> str:
    """Read saved theme preference, defaulting to dark."""
    return get_setting("theme", DEFAULT_THEME)


def save_theme(theme_name: str):
    """Save selected theme preference."""
    set_setting("theme", theme_name)
