
# Qt-XKiller

A powerful task manager and scheduled task killer built with PyQt6 and Python.

## Features

- **Process Viewer**: View running processes with memory usage.
- **Search & Filter**: Quickly find processes by name or PID.
- **Kill Modes**:
  - **Instant Kill**: Terminate immediately.
  - **Timer Kill**: Kill after X hours/minutes.
  - **Schedule Kill**: Kill at a specific time of day.
- **Safety**:
  - **Hard Whitelist**: Prevents killing critical system processes.
  - **User Whitelist**: Add your own protected processes.
- **System Tray**: Runs in the background, minimizes to tray.
- **Notifications**: Alerts on success or blocked attempts.

## Installation

### From Source

1. Clone the repo:
   ```bash
   git clone https://github.com/hdung7903/qt-xkiller.git
   cd qt-xkiller
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run:
   ```bash
   python main.py
   ```

### Binaries (Recommended)

1. Download `Qt-XKiller-Setup.exe` from the [Releases](https://github.com/hdung7903/qt-xkiller/releases) page.
2. Run the installer.
3. Choose your install directory and select if you want Desktop/Start Menu shortcuts.
4. Launch "Qt-XKiller" from your desktop or start menu.

## Development & Build

### Prerequisites

- Python 3.10+
- `pip`

### Setup

1. Clone the repo:
   ```bash
   git clone https://github.com/hdung7903/qt-xkiller.git
   cd qt-xkiller
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Building Release

To build the standalone executable and the installer:

1. Ensure requirements are installed.
2. Run the build script:
   ```bash
   python build_release.py
   ```
3. The artifacts will be created in the `dist/` folder:
   - `Qt-XKiller.exe`: Portable application.
   - `Qt-XKiller-Setup.exe`: Installer.

## Manual Build (PyInstaller)

```bash
pyinstaller --noconfirm --onefile --windowed --name "Qt-XKiller" --add-data "src;src" --hidden-import "qtawesome" main.py
```
