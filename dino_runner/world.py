"""Background rendering, biome themes, and day/night transitions."""

from __future__ import annotations

import math
import random
from typing import Any

import pygame

from .constants import DAY_NIGHT_DURATION, GROUND_Y, LOGICAL_HEIGHT, LOGICAL_WIDTH


def blend(a: pygame.Color, b: pygame.Color, amount: float) -> pygame.Color:
    amount = max(0.0, min(1.0, amount))
    return pygame.Color(
        int(a.r + (b.r - a.r) * amount),
        int(a.g + (b.g - a.g) * amount),
        int(a.b + (b.b - a.b) * amount),
    )


class World:
    def __init__(self, biomes: list[dict[str, Any]]) -> None:
        self.biomes = biomes
        self.sky_time = 0.0
        self.ground_offset = 0.0
        self.clouds = [
            {
                "x": random.uniform(0, LOGICAL_WIDTH),
                "y": random.uniform(60, 240),
                "speed": random.uniform(24, 52),
                "scale": random.uniform(0.8, 1.6),
            }
            for _ in range(7)
        ]
        self.stars = [
            (
                random.randint(0, LOGICAL_WIDTH),
                random.randint(20, GROUND_Y - 180),
                random.randint(1, 3),
            )
            for _ in range(40)
        ]

    def current_biome(self, score: float) -> dict[str, Any]:
        current = self.biomes[0]
        for biome in self.biomes:
            if score >= biome.get("unlock_score", 0):
                current = biome
        return current

    def night_ratio(self) -> float:
        return (math.sin(self.sky_time * math.tau / DAY_NIGHT_DURATION - math.pi / 2) + 1.0) * 0.5

    def update(self, dt: float, scroll_speed: float) -> None:
        self.sky_time += dt
        self.ground_offset = (self.ground_offset + scroll_speed * dt) % 80
        for cloud in self.clouds:
            cloud["x"] -= cloud["speed"] * dt
            if cloud["x"] < -180:
                cloud["x"] = LOGICAL_WIDTH + random.randint(50, 220)
                cloud["y"] = random.uniform(50, 230)

    def _draw_gradient(self, surface: pygame.Surface, top: pygame.Color, bottom: pygame.Color) -> None:
        for y in range(LOGICAL_HEIGHT):
            mix = y / LOGICAL_HEIGHT
            color = blend(top, bottom, mix)
            pygame.draw.line(surface, color, (0, y), (LOGICAL_WIDTH, y))

    def draw(self, surface: pygame.Surface, score: float, challenge_active: bool) -> dict[str, Any]:
        biome = self.current_biome(score)
        night = self.night_ratio()

        sky_top = blend(pygame.Color(biome["sky_day_top"]), pygame.Color(biome["sky_night_top"]), night)
        sky_bottom = blend(pygame.Color(biome["sky_day_bottom"]), pygame.Color(biome["sky_night_bottom"]), night)
        horizon = blend(pygame.Color(biome["horizon_day"]), pygame.Color(biome["horizon_night"]), night)
        ground = blend(pygame.Color(biome["ground_day"]), pygame.Color(biome["ground_night"]), night)
        accent = pygame.Color(biome["accent"])

        self._draw_gradient(surface, sky_top, sky_bottom)

        moon_x = int(LOGICAL_WIDTH * 0.18 + math.sin(self.sky_time * 0.14) * 120)
        moon_y = int(110 + math.cos(self.sky_time * 0.24) * 45)
        sun_x = LOGICAL_WIDTH - moon_x
        sun_y = moon_y + 24
        pygame.draw.circle(surface, blend(pygame.Color("#ffd966"), pygame.Color("#d6f1ff"), night), (sun_x, sun_y), 34)
        pygame.draw.circle(surface, pygame.Color("#f5f7ff"), (moon_x, moon_y), 26)
        pygame.draw.circle(surface, sky_top, (moon_x + 10, moon_y - 6), 22)

        if night > 0.18:
            star_layer = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT), pygame.SRCALPHA)
            alpha = int(185 * night)
            for x, y, size in self.stars:
                pygame.draw.circle(star_layer, pygame.Color(255, 255, 255, alpha), (x, y), size)
            surface.blit(star_layer, (0, 0))

        hill_height = 120
        for index in range(4):
            base_y = GROUND_Y - 68 + index * 12
            points = []
            for x in range(-120, LOGICAL_WIDTH + 160, 140):
                wave = math.sin((x + self.ground_offset * (index + 1) * 0.2) * 0.01 + index) * hill_height
                points.append((x, base_y - 50 - wave * 0.18))
            points = [(-120, GROUND_Y)] + points + [(LOGICAL_WIDTH + 160, GROUND_Y)]
            shade = blend(horizon, ground, 0.35 + index * 0.1)
            pygame.draw.polygon(surface, shade, points)

        for cloud in self.clouds:
            cloud_rect = pygame.Rect(int(cloud["x"]), int(cloud["y"]), int(110 * cloud["scale"]), int(42 * cloud["scale"]))
            cloud_color = blend(pygame.Color("#ffffff"), pygame.Color("#9db3ce"), night * 0.85)
            for offset_x, offset_y in ((-28, 0), (0, -10), (28, 4)):
                puff = cloud_rect.move(offset_x, offset_y)
                pygame.draw.ellipse(surface, cloud_color, puff)

        ground_rect = pygame.Rect(0, GROUND_Y, LOGICAL_WIDTH, LOGICAL_HEIGHT - GROUND_Y)
        pygame.draw.rect(surface, ground, ground_rect)
        pygame.draw.rect(surface, accent, pygame.Rect(0, GROUND_Y, LOGICAL_WIDTH, 10))
        for x in range(-80, LOGICAL_WIDTH + 80, 80):
            stripe = pygame.Rect(int(x - self.ground_offset), GROUND_Y + 24, 42, 7)
            pygame.draw.rect(surface, blend(accent, ground, 0.45), stripe, border_radius=3)

        if challenge_active:
            overlay = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT), pygame.SRCALPHA)
            overlay.fill((255, 64, 64, 24))
            surface.blit(overlay, (0, 0))
            for x in range(-120, LOGICAL_WIDTH + 120, 120):
                pygame.draw.line(surface, pygame.Color("#ff7a59"), (x - self.ground_offset * 1.8, 0), (x + 180 - self.ground_offset * 1.8, LOGICAL_HEIGHT), 2)

        return {
            "name": biome["name"],
            "night_ratio": night,
            "accent": accent,
            "ground": ground,
        }
