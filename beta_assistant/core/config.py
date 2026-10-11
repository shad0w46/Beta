"""Configuration and constants for Beta_Assistant."""

import os
from pathlib import Path

APP_NAME = "Beta Assistant"
APP_VERSION = "1.0.0"
APP_SUBTITLE = "AlphaOS System Administration & Control Center"
APP_ID = "org.alphaos.beta_assistant"

HOME_DIR = Path.home()
CONFIG_DIR = HOME_DIR / ".config" / "beta_assistant"
LOG_DIR = CONFIG_DIR / "logs"
USER_MODULES_DIR = CONFIG_DIR / "modules"

# Ensure dirs exist
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
USER_MODULES_DIR.mkdir(parents=True, exist_ok=True)

# Default theme settings
THEME_DARK = "dark"
THEME_LIGHT = "light"
DEFAULT_THEME = THEME_DARK

# Common system paths
SYSTEMD_SYSTEM_DIR = Path("/etc/systemd/system")
SYSTEMD_USER_DIR = HOME_DIR / ".config" / "systemd" / "user"
SYSTEMD_USER_DIR.mkdir(parents=True, exist_ok=True)

PASSWD_FILE = Path("/etc/passwd")
GROUP_FILE = Path("/etc/group")
