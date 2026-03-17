"""Startup checks, dependency messaging, and safe demo shortcut creation."""

from __future__ import annotations

import argparse
import platform
import sys
from pathlib import Path

from .assets import AssetLoadError, missing_required_assets
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


def check_environment() -> tuple[bool, str]:
    try:
        import pygame  # noqa: F401
    except ImportError:
        return (
            False,
            "Pygame is not installed.\n\n"
            "Run `pip install -r requirements.txt` from this project folder, "
            "then launch the game again.",
        )

    missing = missing_required_assets()
    if missing:
        formatted = "\n".join(f"- {path}" for path in missing)
        return (
            False,
            "Required local assets are missing.\n\n"
            "Restore the files below and relaunch the game:\n"
            f"{formatted}",
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
