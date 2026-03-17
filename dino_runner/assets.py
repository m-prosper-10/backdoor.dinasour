"""Local data asset loading and lightweight font helpers."""

from __future__ import annotations

import copy
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from .constants import REQUIRED_DATA_FILES
from .paths import asset_path


class AssetLoadError(RuntimeError):
    """Raised when required local assets are missing or invalid."""


def _clone(value: Any) -> Any:
    return copy.deepcopy(value)


def missing_required_assets() -> list[Path]:
    missing: list[Path] = []
    for filename in REQUIRED_DATA_FILES:
        path = asset_path("data", filename)
        if not path.is_file():
            missing.append(path)
    return missing


def load_json_asset(filename: str, *, required: bool = False, fallback: Any = None) -> Any:
    path = asset_path("data", filename)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        if required:
            raise AssetLoadError(f"Required asset is missing: {path}") from exc
        return _clone(fallback)
    except json.JSONDecodeError as exc:
        if required:
            raise AssetLoadError(f"Asset is invalid JSON: {path}") from exc
        return _clone(fallback)


class AssetLibrary:
    """Loads required JSON-driven game data and font helpers."""

    def __init__(self) -> None:
        self.biomes = sorted(
            load_json_asset("biomes.json", required=True),
            key=lambda biome: biome.get("unlock_score", 0),
        )
        self.skins = load_json_asset("skins.json", required=True)
        self.achievements = load_json_asset("achievements.json", required=True)
        self.tutorial = load_json_asset("tutorial.json", required=True)

    @lru_cache(maxsize=32)
    def get_font(self, size: int, bold: bool = False):
        import pygame

        preferred = ["Consolas", "Courier New", "monospace"]
        return pygame.font.SysFont(preferred, size, bold=bold)

    def get_skin(self, skin_id: str) -> dict[str, Any]:
        for skin in self.skins:
            if skin["id"] == skin_id:
                return skin
        return self.skins[0]
