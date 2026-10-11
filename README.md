# Beta Assistant (AlphaOS)

**Beta Assistant** is a native, modern graphical administration and control center crafted specifically for **AlphaOS** (Debian-based). It bridges the gap between powerful Linux CLI operations and an intuitive, visual GUI experience.

Designed with an extensible, modular architecture, Beta Assistant makes traditionally intimidating Linux tasks—such as full system upgrades, repository package searches, user permission handling, daemon isolation, systemd service creation, and journalctl analysis—effortless and accessible.

---

## 🌟 Key Features

### 1. 📊 System Overview & Health Dashboard
- Real-time CPU, RAM, and root storage telemetry gauges.
- Kernel and host distribution metadata detection (`/etc/os-release`).
- Proactive alerts for pending package updates and failed systemd services.
- One-click shortcuts for frequent maintenance tasks (cache cleanup, autoremove, upgrade).

### 2. 📦 APT Package & Update Manager
- **Fast Package Search**: Live querying across Debian/AlphaOS APT repositories.
- **Detailed Package Inspector**: View versions, candidate builds, section, package size, descriptions, and dependencies.
- **Package Management**: Install, Reinstall, Remove, and Purge packages with a single click.
- **System Upgrades**: Check for index updates (`apt update`) and perform full system upgrades (`apt upgrade`) with real-time log streaming.

### 3. 👤 User, Daemon & No-Login Account Manager
- **User Database Inspector**: Categorizes accounts into **Standard Users**, **System Daemons**, and **No-Login Service Accounts**.
- **User Creation Wizard**:
  - **Standard Users**: Interactive login shells (`/bin/bash`, `/bin/zsh`), automated `/home` creation, password initialization, and supplementary group assignment (`sudo`, `audio`, etc.).
  - **System Daemons**: Dedicated non-human service accounts with `--system` flags, custom system UIDs (< 1000), and restricted home paths.
  - **No-Login Users**: Restricted accounts with `/usr/sbin/nologin` or `/bin/false` login shells to enhance system hardening.
- **Account Actions**: One-click locking/unlocking (`usermod -L/-U`), supplementary group management, shell modification, and account removal.

### 4. ⚙️ Systemd Service & Daemon Manager
- **Unit Directory**: View all system services with live status filters (Running, Inactive, Failed).
- **Service Operations**: Start, Stop, Restart, Reload, Enable at boot, and Disable at boot.
- **Integrated Journalctl Console**: Inspect real-time logs (`journalctl -u <unit> -n 50`) for any selected service.
- **Service Creation Wizard**:
  - Interactively build new `.service` unit files.
  - Configure `ExecStart`, `WorkingDirectory`, `Restart` policy, environment variables, and execution user (including newly created daemons).
  - Automatically installs units to `/etc/systemd/system/`, reloads the systemd daemon, and provides options to enable and start immediately.

### 5. 💻 Live Streaming Console Drawer
- Commands execute asynchronously in background worker threads without freezing the user interface.
- Real-time line-by-line output streaming with ANSI and error color coding.
- Support for process cancellation and elevated privilege operations via `sudo`/`pkexec`.

---

## 🧱 Modular Architecture

Beta Assistant is engineered to be **100% modular**. Every core feature is an independent module subclassing `BaseModule`. New modules can be added without altering any core logic.

```
Beta_Assistant/
├── beta_assistant/
│   ├── core/
│   │   ├── config.py           # Paths, constants, theme configs
│   │   ├── runner.py           # Async command runner with streaming signals
│   │   ├── module_base.py      # Abstract BaseModule interface
│   │   ├── module_manager.py   # Dynamic loader and registry
│   │   └── system_info.py      # Telemetry and OS inspection
│   ├── modules/
│   │   ├── dashboard/          # System overview and quick tasks
│   │   ├── packages/           # APT package and upgrade manager
│   │   ├── users/              # Users, daemons, and nologin manager
│   │   └── services/           # Systemd unit manager and daemon wizard
│   ├── ui/
│   │   ├── main_window.py      # Main window shell & navigation
│   │   ├── theme.py            # Modern AlphaOS dark stylesheet
│   │   └── components/         # Badges, metric cards, terminal drawer
│   └── assets/                 # Brand logos and iconography
├── desktop/                    # XDG desktop file and SVG icon
├── tests/                      # Backend and module unit tests
├── run.sh                      # Launch script with Wayland detection
└── setup.py                    # Setuptools packaging script
```

### Adding a New Module

To create a new module, simply create a class inheriting from `BaseModule`:

```python
from beta_assistant.core.module_base import BaseModule
from PyQt6.QtWidgets import QLabel, QWidget

class FirewallModule(BaseModule):
    @property
    def module_id(self) -> str:
        return "firewall"

    @property
    def title(self) -> str:
        return "Firewall (UFW)"

    @property
    def icon_name(self) -> str:
        return "shield"

    @property
    def order(self) -> int:
        return 50

    def create_widget(self) -> QWidget:
        return QLabel("Firewall Management View")
```

Place it in `beta_assistant/modules/` or drop it into `~/.config/beta_assistant/modules/`. `ModuleManager` will auto-discover it on startup, register it in the navigation sidebar, and connect all signals automatically.

---

## 🚀 Running Beta Assistant

### Quick Start
Make sure dependencies are installed:
```bash
sudo apt install python3-pyqt6 python3-pyqt6.qtsvg python3-apt python3-psutil
```

Launch the application:
```bash
./run.sh
```

Or run via Python:
```bash
python3 -m beta_assistant
```

### Running Tests
Execute the automated test suite:
```bash
python3 -m unittest discover tests
```

---

## 🖥️ Desktop Integration for AlphaOS
To add Beta Assistant to your application menu:
```bash
mkdir -p ~/.local/share/applications ~/.local/share/icons/hicolor/scalable/apps
cp desktop/beta-assistant.desktop ~/.local/share/applications/
cp desktop/beta-assistant.svg ~/.local/share/icons/hicolor/scalable/apps/
update-desktop-database ~/.local/share/applications/ 2>/dev/null || true
```
