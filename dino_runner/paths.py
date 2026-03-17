"""Filesystem helpers that work in development and in PyInstaller builds."""

from __future__ import annotations

import os
import platform
import sys
from pathlib import Path


def resource_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def asset_path(*parts: str) -> Path:
    return resource_root().joinpath("assets", *parts)


def executable_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return resource_root()


def user_data_dir(create: bool = True) -> Path:
    if platform.system() == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home()))
        path = base / "DinoRunnerDeluxe"
    else:
        path = Path.home() / ".dino_runner_deluxe"
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def settings_path() -> Path:
    return user_data_dir() / "settings.json"


def save_data_path() -> Path:
    return user_data_dir() / "save_data.json"


def shortcut_dir(create: bool = True) -> Path:
    path = user_data_dir(create=create) / "demo_shortcuts"
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path
