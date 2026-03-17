"""Application entry point for source execution and PyInstaller builds."""

from dino_runner.bootstrap import launch


if __name__ == "__main__":
    raise SystemExit(launch())
