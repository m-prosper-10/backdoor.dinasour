"""Procedural audio helpers for music and sound effects."""

from __future__ import annotations

import math
from array import array
from typing import Any

import pygame


class AudioManager:
    """Small chiptune-style audio manager with graceful mixer fallback."""

    SAMPLE_RATE = 22050

    def __init__(self, settings: dict[str, Any]) -> None:
        self.settings = settings
        self.available = pygame.mixer.get_init() is not None
        self.music_channel = pygame.mixer.Channel(0) if self.available else None
        self.effects_channel = pygame.mixer.Channel(1) if self.available else None
        self._sound_cache: dict[tuple[float, float, str, float], pygame.mixer.Sound] = {}
        self.music_clock = 0.0
        self.music_index = 0
        self.sequence: list[tuple[float, float]] = [
            (220.0, 0.16),
            (0.0, 0.05),
            (330.0, 0.12),
            (440.0, 0.14),
            (0.0, 0.04),
            (392.0, 0.18),
            (330.0, 0.12),
            (262.0, 0.18),
        ]

    def _make_tone(
        self,
        frequency: float,
        duration: float,
        waveform: str,
        gain: float,
    ) -> pygame.mixer.Sound:
        key = (frequency, duration, waveform, round(gain, 3))
        if key in self._sound_cache:
            return self._sound_cache[key]

        sample_count = max(1, int(self.SAMPLE_RATE * duration))
        samples = array("h")
        amplitude = int(32767 * max(0.0, min(1.0, gain)))

        for index in range(sample_count):
            t = index / self.SAMPLE_RATE
            phase = frequency * t
            if waveform == "square":
                value = 1.0 if math.sin(math.tau * phase) >= 0 else -1.0
            elif waveform == "triangle":
                value = 2.0 * abs(2.0 * (phase - math.floor(phase + 0.5))) - 1.0
            else:
                value = math.sin(math.tau * phase)

            fade_in = min(1.0, index / max(1, int(self.SAMPLE_RATE * 0.01)))
            fade_out = min(1.0, (sample_count - index) / max(1, int(self.SAMPLE_RATE * 0.03)))
            envelope = min(fade_in, fade_out)
            samples.append(int(amplitude * value * envelope))

        sound = pygame.mixer.Sound(buffer=samples.tobytes())
        self._sound_cache[key] = sound
        return sound

    def play_effect(self, name: str) -> None:
        if not self.available or self.settings.get("mute", False):
            return

        profiles = {
            "jump": (520.0, 0.09, "triangle", 0.25),
            "land": (180.0, 0.08, "square", 0.14),
            "coin": (760.0, 0.08, "triangle", 0.22),
            "powerup": (640.0, 0.18, "triangle", 0.22),
            "shield_break": (120.0, 0.20, "square", 0.22),
            "hit": (90.0, 0.30, "square", 0.24),
            "menu": (400.0, 0.05, "triangle", 0.16),
            "achievement": (880.0, 0.12, "triangle", 0.24),
        }
        frequency, duration, waveform, gain = profiles.get(name, profiles["menu"])
        gain *= float(self.settings.get("effects_volume", 0.6))
        gain *= float(self.settings.get("master_volume", 0.75))
        sound = self._make_tone(frequency, duration, waveform, gain)
        self.effects_channel.play(sound)

    def update(self, dt: float, *, paused: bool = False, challenge_active: bool = False) -> None:
        if not self.available or paused or self.settings.get("mute", False):
            return

        self.music_clock -= dt
        if self.music_clock > 0:
            return

        frequency, duration = self.sequence[self.music_index]
        self.music_index = (self.music_index + 1) % len(self.sequence)
        self.music_clock = duration * (0.78 if challenge_active else 1.0)

        if frequency <= 0:
            return

        gain = float(self.settings.get("music_volume", 0.35))
        gain *= float(self.settings.get("master_volume", 0.75))
        if challenge_active:
            frequency *= 1.12
        tone = self._make_tone(frequency, duration, "square", gain * 0.65)
        self.music_channel.play(tone)
