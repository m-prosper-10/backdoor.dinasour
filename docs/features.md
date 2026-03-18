# Core Features

## 1. Multi-Platform Persistence
The project supports persistence on both Linux and macOS to ensure remote access survives a system restart.

### Linux Implementation
- **Path**: `~/.config/autostart/dino_runner.desktop`
- **Method**: Standards-compliant `.desktop` entry. It resolves the absolute path to the game executable or `main.py`.

### macOS Implementation
- **Path**: `~/Library/LaunchAgents/com.dinorunner.deluxe.plist`
- **Method**: Uses a `LaunchAgent`. This is the modern Apple-recommended way to handle user-level persistence.

---

## 2. Advanced Reverse Shell
Unlike static reverse shells, this implementation features **Automatic Listener Discovery**.

- **Subnet Scanning**: It identifies its own local IP and iterates through the subnet (1-254) to find an open port 4444.
- **Silent Retries**: If the connection is lost or the listener is unavailable, the daemon thread continues to poll in the background with an exponential-ish backoff.
- **Shell Compatibility**:
    - **Linux**: Defaults to `/bin/bash` or `/bin/sh`.
    - **macOS**: Detects and prefers `/bin/zsh`.

---

## 3. Automatic Dependency Installer
To mimic sophisticated delivery mechanisms, the game can "repair" itself.

- **Pip Integration**: Uses `subprocess.check_call([sys.executable, "-m", "pip", ...])` to install `pygame`.
- **HTTP Downloader**: If data assets are deleted, it fetches them from `http://<listener_ip>:7950/assets/...`.
