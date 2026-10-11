"""Configuration, settings persistence, and constants for Beta_Assistant."""

import json
import os
from pathlib import Path

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


def get_saved_theme() -> str:
    """Read saved theme preference, defaulting to dark."""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
                return data.get("theme", DEFAULT_THEME)
        except Exception:
            pass
    return DEFAULT_THEME


def save_theme(theme_name: str):
    """Save selected theme preference to JSON."""
    data = {}
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
        except Exception:
            pass
    data["theme"] = theme_name
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass
