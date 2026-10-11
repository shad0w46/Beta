# Beta Assistant (AlphaOS)

![AlphaOS Logo](beta_assistant/assets/alphaos_logo.svg)

**Beta Assistant** is a native, modern graphical administration and control center crafted specifically for **AlphaOS** (Debian-based). It bridges the gap between powerful Linux CLI operations and an intuitive, visual GUI experience.

Designed with an extensible, modular architecture, Beta Assistant makes traditionally intimidating Linux tasks—such as full system upgrades, repository package searches, user permission handling, daemon isolation, systemd service creation, storage cleaning, and boot diagnostics—effortless, fast, and accessible.

---

## 🌟 Key Features

### 1. 📊 System Overview & Health Dashboard
- Real-time CPU, RAM, and root storage telemetry gauges with animated visual meters.
- Kernel, architecture, and host distribution metadata detection (`/etc/os-release`).
- Proactive status alerts for pending package updates and failed systemd services.
- Quick action grid for instant maintenance tasks (cache cleanup, autoremove, upgrade).

### 2. 📦 APT Package & Update Manager
- **Fast Package Search**: Live querying across Debian/AlphaOS APT repositories with 320ms debouncing and in-memory cache reuse (< 90ms lookups).
- **Detailed Package Inspector**: View versions, candidate builds, section, package size, descriptions, and dependencies.
- **Package Management**: Install, Reinstall, Remove, and Purge packages with a single click.
- **System Upgrades**: Check for index updates (`apt update`) and perform full system upgrades (`apt upgrade`) with real-time log streaming.

### 3. 👤 User, Daemon & No-Login Account Manager
- **User Database Inspector**: Categorizes accounts into **Standard Users**, **System Daemons**, and **No-Login Service Accounts**.
- **User Creation Wizard**:
  - **Standard Users**: Interactive login shells (`/bin/bash`, `/bin/zsh`), automated `/home` creation, password initialization, and supplementary group assignment (`sudo`, `audio`, etc.).
  - **System Daemons**: Dedicated non-human service accounts with `--system` flags, custom system UIDs (< 1000), and restricted home paths.
  - **No-Login Users**: Hardened accounts with `/usr/sbin/nologin` or `/bin/false` login shells to prevent unauthorized logins.
- **Account Actions**: One-click locking/unlocking (`usermod -L/-U`), supplementary group management, shell modification, and account deletion.

### 4. 🧹 Storage & System Junk Cleaner
- **Mounted Filesystems**: Visual partition capacity cards detailing total, used, free space, and usage percentages.
- **System Junk Scanner**:
  - APT Archive Cache (`/var/cache/apt/archives/*.deb`).
  - Rotated and archived systemd journals (`journalctl --disk-usage`).
  - User thumbnail caches (`~/.cache/thumbnails`).
  - Orphaned / dangling dependency packages.
- **One-Click Cleaner**: Instant clean action invoking `apt-get clean`, `journalctl --vacuum-time=3d`, thumbnail purging, and `apt-get autoremove`.

### 5. ⚙️ Systemd Service & Daemon Manager
- **Unit Directory**: View all system services with live status filters (Running, Inactive, Failed).
- **Service Operations**: Start, Stop, Restart, Reload, Enable at boot, and Disable at boot.
- **Integrated Journalctl Console**: Inspect real-time logs (`journalctl -u <unit> -n 50`) for any selected service.
- **Service Creation Wizard**:
  - Interactively build new `.service` unit files.
  - Configure `ExecStart`, `WorkingDirectory`, `Restart` policy, environment variables, and execution user (including newly created daemons).
  - Automatically installs units to `/etc/systemd/system/`, reloads the systemd daemon, and provides options to enable and start immediately.

### 6. ⏱️ Boot Diagnostics & Journal Logs
- **Boot Analyzer**: Breakdown of firmware, bootloader, kernel, and userspace startup times using `systemd-analyze`.
- **Startup Blame**: Performance ranking of startup services sorted by boot delay, with high/medium/low severity badges.
- **System Journal Inspector**: Priority-filtered log viewer (`emerg`, `alert`, `crit`, `err`, `warning`, `notice`, `info`) with real-time text search.

### 7. 🌗 Dynamic Dark & Light Theme Engine
- Curated color palettes with modern glassmorphism accents, crisp typography, and border highlights.
- Seamless one-click theme switcher in header (`☀️ Light Mode` / `🌙 Dark Mode`) and via global hotkey `Ctrl+Shift+T`.
- Persistent theme preferences saved across restarts to `~/.config/beta_assistant/settings.json`.

### 8. 💻 Live Streaming Console Drawer
- Commands execute asynchronously in background worker threads without freezing the user interface.
- Real-time line-by-line output streaming with ANSI and error color coding.
- Support for process cancellation and elevated privilege operations via `sudo`/`pkexec`.

---

## ⌨️ Global Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| `Ctrl+B` | Toggle Navigation Sidebar |
| `Ctrl+Shift+T` | Toggle Dark / Light Mode |
| `Ctrl+1` | Navigate to Dashboard |
| `Ctrl+2` | Navigate to Package Manager |
| `Ctrl+3` | Navigate to User Manager |
| `Ctrl+4` | Navigate to Storage & Cleaner |
| `Ctrl+5` | Navigate to Services Manager |
| `Ctrl+6` | Navigate to Boot & Logs |

---

## 🧱 Modular Architecture

Beta Assistant is engineered to be **100% modular**. Every core feature is an independent module subclassing `BaseModule`. New modules can be added without altering any core logic.

```
Beta_Assistant/
├── beta_assistant/
│   ├── core/
│   │   ├── config.py           # Paths, constants, settings persistence
│   │   ├── runner.py           # Async command runner with streaming signals
│   │   ├── async_worker.py     # Worker thread tracking & debounced execution
│   │   ├── module_base.py      # Abstract BaseModule interface
│   │   ├── module_manager.py   # Dynamic loader and registry
│   │   └── system_info.py      # Telemetry and OS inspection
│   ├── modules/
│   │   ├── dashboard/          # System overview and quick tasks
│   │   ├── packages/           # APT package and upgrade manager
│   │   ├── users/              # Users, daemons, and nologin manager
│   │   ├── storage/            # Disk partitions and junk cleaner
│   │   ├── services/           # Systemd unit manager and daemon wizard
│   │   └── logs/               # Boot analyzer and journal diagnostics
│   ├── ui/
│   │   ├── main_window.py      # Main window shell & navigation
│   │   ├── theme.py            # Dark and Light QSS themes
│   │   └── components/         # Badges, metric cards, terminal drawer
│   └── assets/                 # Brand logos and iconography (SVG)
├── desktop/                    # XDG desktop file and SVG icon
├── tests/                      # Automated unit test suite & screenshots
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
        return 70

    def create_widget(self) -> QWidget:
        return QLabel("Firewall Management View")
```

Place it in `beta_assistant/modules/` or drop it into `~/.config/beta_assistant/modules/`. `ModuleManager` will auto-discover it on startup, register it in the navigation sidebar, and connect all signals automatically.

---

## 🚀 Running Beta Assistant

### Dependencies
Ensure the required dependencies are installed:
```bash
sudo apt install python3-pyqt6 python3-pyqt6.qtsvg python3-apt python3-psutil
```

### Launching the Application
Launch via the helper script:
```bash
./run.sh
```

Or run via Python:
```bash
python3 -m beta_assistant
```

### Running Automated Tests
Execute the automated test suite:
```bash
python3 -m unittest discover tests
```

---

## 🛠️ Building with Meson & Ninja

Beta Assistant supports native building and installation via **Meson** and **Ninja**:

```bash
# 1. Setup build directory
meson setup build

# 2. Compile project
ninja -C build

# 3. Install to system (default: /usr/local)
sudo ninja -C build install
```

---

## 📦 Building Debian Package (.deb)

To build a native Debian package:

```bash
# 1. Ensure build tools are installed
sudo apt install -y meson ninja-build debhelper devscripts dpkg-dev

# 2. Build the package
dpkg-buildpackage -us -uc -b

# 3. Install the resulting deb package
sudo dpkg -i ../beta-assistant_1.1.0-1_all.deb
```

---

## 🚀 Publishing Repository to Your Account

To initialize and publish this repository to your GitHub/GitLab account:

```bash
# 1. Verify all commits are clean
git status

# 2. Add your remote repository (replace with your repository URL)
git remote add origin https://github.com/YOUR_USERNAME/beta-assistant.git

# 3. Rename branch to main if desired
git branch -M main

# 4. Push all commits to your account
git push -u origin main
```

