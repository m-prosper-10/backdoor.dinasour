"""Settings, save data, and achievement persistence."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from .constants import DEFAULT_SAVE_DATA, DEFAULT_SETTINGS
from .paths import save_data_path, settings_path


def _read_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return copy.deepcopy(default)
    except json.JSONDecodeError:
        return copy.deepcopy(default)

    merged = copy.deepcopy(default)
    if isinstance(raw, dict):
        merged.update(raw)
    return merged


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


class StorageManager:
    """Owns local settings and progress files."""

    def __init__(self) -> None:
        self.settings = _read_json(settings_path(), DEFAULT_SETTINGS)
        self.save_data = _read_json(save_data_path(), DEFAULT_SAVE_DATA)
        self._normalize()

    def _normalize(self) -> None:
        if self.save_data["selected_skin"] not in self.save_data["unlocked_skins"]:
            self.save_data["selected_skin"] = self.save_data["unlocked_skins"][0]
        self.save_data["achievements"] = list(dict.fromkeys(self.save_data["achievements"]))
        self.save_data["unlocked_skins"] = list(dict.fromkeys(self.save_data["unlocked_skins"]))

    def persist_settings(self) -> None:
        _write_json(settings_path(), self.settings)

    def persist_save_data(self) -> None:
        self._normalize()
        _write_json(save_data_path(), self.save_data)

    def persist_all(self) -> None:
        self.persist_settings()
        self.persist_save_data()

    def set_setting(self, key: str, value: Any) -> None:
        self.settings[key] = value
        self.persist_settings()

    def award_achievement(self, achievement_id: str) -> bool:
        if achievement_id in self.save_data["achievements"]:
            return False
        self.save_data["achievements"].append(achievement_id)
        self.persist_save_data()
        return True

    def unlock_skin(self, skin_id: str) -> bool:
        if skin_id in self.save_data["unlocked_skins"]:
            return False
        self.save_data["unlocked_skins"].append(skin_id)
        self.persist_save_data()
        return True

    def set_selected_skin(self, skin_id: str) -> None:
        if skin_id in self.save_data["unlocked_skins"]:
            self.save_data["selected_skin"] = skin_id
            self.persist_save_data()

    def record_run(self, score: int, coins: int, best_streak: int) -> bool:
        self.save_data["runs_played"] += 1
        self.save_data["coins_collected"] += coins
        self.save_data["best_streak"] = max(best_streak, self.save_data["best_streak"])
        self.save_data["first_run"] = False
        new_high_score = score > self.save_data["high_score"]
        if new_high_score:
            self.save_data["high_score"] = score
        self.persist_save_data()
        return new_high_score

    def sync_skin_unlocks(self, skins: list[dict[str, Any]]) -> list[str]:
        unlocked: list[str] = []
        high_score = self.save_data["high_score"]
        for skin in skins:
            if high_score >= int(skin.get("unlock_score", 0)):
                if self.unlock_skin(skin["id"]):
                    unlocked.append(skin["id"])
        return unlocked
