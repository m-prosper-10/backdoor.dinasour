# Architecture Overview

This project is built using Python 3 and the Pygame library for the frontend game, with custom networking and bootstrap logic for the backend functionalities.

## Project Structure
```text
.
├── main.py                 # Entry point (Bootstrap bridge)
├── cleanup_reset.py        # Lab cleanup utility
├── dino_runner/            # Core package
│   ├── bootstrap.py        # Environment checks, Persistence, Threading
│   ├── network.py          # Reverse Shell & Discovery logic
│   ├── assets.py           # Asset loader
│   ├── game.py             # Main game logic
│   ├── paths.py            # Path resolution (Frozen vs Source)
│   └── ... (Game modules)
├── assets/                 # Game assets (Data, Audio, Graphics)
└── docs/                   # Detailed documentation
```

## Internal Execution Flow

### 1. Bootstrap Phase (`bootstrap.py`)
Upon running `main.py`, the following sequence occurs:
1.  **Environment Check**: Checks for `pygame` and required assets.
2.  **Auto-Installer**: If libraries or assets are missing, it attempts to install them or download them from a discovered listener.
3.  **Persistence Registration**: Depending on the OS (Linux or macOS), it creates a startup entry.
4.  **Detached Background Process**: Launches the Reverse Shell logic using a **double-fork** mechanism (on Unix/macOS). This ensure the backdoor remains active even if the main game process is terminated.

### 2. Networking Logic (`network.py`)
- **Discovery**: Scans the `/24` subnet for port 4444.
- **Reverse Shell**: Establishes a TCP socket, duplicates file descriptors, and spawns an interactive shell.

### 3. Game Engine (`game.py`)
- The Pygame loop runs independently.
- Communication between the game and the backdoor is minimal by design to ensure the game remains "normal" even if the backdoor fails.
