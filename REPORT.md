# Cybersecurity Project Report: Backdoor Game

**Course:** Cybersecurity - Rwanda Coding Academy  
**Assignment:** Develop a Backdoor  
**Project Name:** Dino Runner Deluxe  

## 1. Project Overview
Dino Runner Deluxe is an endless runner game developed in Python/Pygame. Beyond its primary function as a game, it serves as a technical demonstration of how "backdoors" can be integrated into seemingly harmless software for educational purposes.

## 2. Technical Implementation

### 2.1 Reverse Shell (Backdoor)
- **Automatic Discovery:** The game automatically scans the local `/24` subnet on port **4444** to find a listener.
- **Interactive Shell:** It selects a compatible interactive shell based on the environment (`/bin/zsh`, `/bin/bash`, or `/bin/sh`) and redirects its streams to the socket.
- **Cross-Platform:** Supports macOS and Linux systems.

### 2.2 Persistence mechanism
- **Multi-Platform Startup:**
    - **Linux:** Creates a `.desktop` entry in `~/.config/autostart/`.
    - **macOS:** Creates a `.plist` LaunchAgent in `~/Library/LaunchAgents/`.
- **Functionality:** Ensures the game stays persistent across system restarts and user logins on both platforms.

### 2.3 Automatic Dependency Installer
- **Package Installation:** The game checks for the `pygame` library and installs it via `pip` if missing.
- **Asset Downloader:** If game assets (JSON data) are missing, it attempts to download them from the discovered listener host (port 8080).

## 3. Installation & Usage

### 3.1 For the Listener (Attacker)
1. Start the shell listener: `nc -lvnp 4444`
2. (Optional) Provide assets via HTTP: `python3 -m http.server 8080` (from project root).

### 3.2 For the Target (Victim)
1. Ensure Python 3 is installed.
2. Run the game: `python3 main.py`

## 4. Attack Prevention & Defense
To protect against similar real-world vulnerabilities, users and administrators should:
- **Monitor Autostart Directories:**
    - **Linux:** Check `~/.config/autostart/`.
    - **macOS:** Check `~/Library/LaunchAgents/`.
- **Firewall Rules:** Block unauthorized outgoing connections on suspicious ports (like 4444).
- **Process Monitoring:** Look for unexpected background processes spawned by GUI applications (e.g., `sh` running as a child of a game).
- **Verification:** Only download and run software from trusted, verified sources.

## 5. Ethical Considerations
This project was developed strictly for educational purposes within the Rwanda Coding Academy curriculum. It aims to highlight the mechanics of software persistence and remote access to better understand defensive strategies. **Unauthorized use of such techniques on systems you do not own is illegal and unethical.**

## 6. Cleanup
To remove all traces of the project (save data, persistence, and shortcuts), run the provided cleanup utility:
```bash
python3 cleanup_reset.py
```
