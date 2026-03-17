"""Remove local save data, settings, and optional demo shortcut files."""

from __future__ import annotations

import shutil
from pathlib import Path

from dino_runner.paths import shortcut_dir, user_data_dir


def remove_path(path: Path) -> bool:
    if not path.exists():
        return False
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    return True


def main() -> int:
    data_dir = user_data_dir(create=False)
    shortcuts = shortcut_dir(create=False)

    removed_any = False
    if remove_path(shortcuts):
        print(f"Removed demo shortcut folder: {shortcuts}")
        removed_any = True
    if remove_path(data_dir):
        print(f"Removed local config/save folder: {data_dir}")
        removed_any = True

    if not removed_any:
        print("Nothing to clean. No local save data or demo shortcuts were found.")
    else:
        print("Cleanup complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
