"""Shared constants for Dino Runner Deluxe."""

from __future__ import annotations

APP_NAME = "Dino Runner Deluxe"
WINDOW_TITLE = f"{APP_NAME} - Educational Demo"
VERSION = "1.0.0"

LOGICAL_WIDTH = 1280
LOGICAL_HEIGHT = 720
LOGICAL_SIZE = (LOGICAL_WIDTH, LOGICAL_HEIGHT)
FPS = 60

GROUND_Y = 600
PLAYER_START_X = 180

GRAVITY = 2450.0
JUMP_VELOCITY = 920.0
FAST_FALL_GRAVITY = 1450.0

BASE_SCROLL_SPEED = 420.0
MAX_SCROLL_SPEED = 980.0
SCORE_RATE = 20.0
COIN_SCORE = 30
BIOME_ROTATE_SCORE = 900

COMBO_WINDOW = 3.2
DAY_NIGHT_DURATION = 26.0
CHALLENGE_INTERVAL = 1200
CHALLENGE_DURATION = 12.0

POWERUP_DURATIONS = {
    "shield": 8.0,
    "slow": 6.0,
    "double_jump": 10.0,
    "magnet": 8.0,
    "multiplier": 9.0,
}

REQUIRED_DATA_FILES = [
    "achievements.json",
    "biomes.json",
    "skins.json",
    "tutorial.json",
]

STARTUP_NOTICE_LINES = [
    "Educational Game Demo",
    "",
    "This project is a safe classroom demo built with Python and Pygame.",
    "It only saves local settings, high scores, and optional demo shortcut files.",
    "It does not install anything silently, change startup behavior, or access the network.",
    "",
    "Press Enter to continue or Esc to quit.",
]

SETTINGS_DESCRIPTION = {
    "fullscreen": "Toggle fullscreen play for distraction-free sessions.",
    "focus_mode": "Hide the cursor during play and auto-pause when focus is lost.",
    "mute": "Mute music and sound effects instantly.",
    "music_volume": "Adjust procedural chiptune music volume.",
    "effects_volume": "Adjust jump, pickup, and impact effect volume.",
}

DEFAULT_SETTINGS = {
    "fullscreen": False,
    "focus_mode": True,
    "mute": False,
    "music_volume": 0.35,
    "effects_volume": 0.65,
    "master_volume": 0.75,
}

DEFAULT_SAVE_DATA = {
    "high_score": 0,
    "coins_collected": 0,
    "runs_played": 0,
    "best_streak": 0,
    "selected_skin": "classic",
    "unlocked_skins": ["classic"],
    "achievements": [],
    "first_run": True,
}
