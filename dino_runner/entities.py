"""Gameplay entities for the dinosaur, hazards, coins, and power-ups."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any

import pygame

from .constants import FAST_FALL_GRAVITY, GRAVITY, JUMP_VELOCITY, PLAYER_START_X


def _color(value: str) -> pygame.Color:
    return pygame.Color(value)


class Player:
    def __init__(self, ground_y: int, skin: dict[str, Any]) -> None:
        self.ground_y = ground_y
        self.base_width = 84
        self.base_height = 92
        self.duck_width = 118
        self.duck_height = 58
        self.x = float(PLAYER_START_X)
        self.set_skin(skin)
        self.reset()

    def set_skin(self, skin: dict[str, Any]) -> None:
        self.skin = skin
        self.body_color = _color(skin["body"])
        self.accent_color = _color(skin["accent"])
        self.outline_color = _color(skin["outline"])
        self.eye_color = _color(skin["eye"])

    def reset(self) -> None:
        self.y = float(self.ground_y - self.base_height)
        self.vy = 0.0
        self.on_ground = True
        self.ducking = False
        self.jumps_used = 0
        self.animation_time = 0.0
        self.shield_strength = 0.0
        self.max_jumps = 1

    @property
    def current_width(self) -> int:
        return self.duck_width if self.ducking else self.base_width

    @property
    def current_height(self) -> int:
        return self.duck_height if self.ducking else self.base_height

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.current_width, self.current_height)

    @property
    def collider(self) -> pygame.Rect:
        rect = self.rect.inflate(-18, -16)
        rect.x += 2
        return rect

    @property
    def center(self) -> tuple[float, float]:
        rect = self.rect
        return rect.centerx, rect.centery

    def jump(self) -> bool:
        if self.jumps_used >= self.max_jumps:
            return False
        self.vy = -JUMP_VELOCITY * (0.92 if self.jumps_used else 1.0)
        self.on_ground = False
        self.ducking = False
        self.jumps_used += 1
        return True

    def update(self, dt: float, *, duck_pressed: bool, powerups: dict[str, float]) -> bool:
        self.max_jumps = 2 if powerups.get("double_jump", 0.0) > 0 else 1
        self.shield_strength = powerups.get("shield", 0.0)

        self.animation_time += dt
        landed = False

        if not self.on_ground:
            extra_gravity = FAST_FALL_GRAVITY if duck_pressed and self.vy > -50 else 0.0
            self.vy += (GRAVITY + extra_gravity) * dt
            self.y += self.vy * dt

        if self.y >= self.ground_y - self.base_height:
            if not self.on_ground:
                landed = True
            self.on_ground = True
            self.vy = 0.0
            self.jumps_used = 0
            self.ducking = duck_pressed
            target_height = self.duck_height if self.ducking else self.base_height
            self.y = self.ground_y - target_height
        else:
            self.on_ground = False
            self.ducking = False

        if self.on_ground and duck_pressed:
            self.ducking = True
            self.y = self.ground_y - self.duck_height
        elif self.on_ground:
            self.ducking = False
            self.y = self.ground_y - self.base_height

        return landed

    def draw(self, surface: pygame.Surface) -> None:
        blink = self.shield_strength > 0 and int(self.animation_time * 12) % 2 == 0
        if self.shield_strength > 0:
            radius = max(self.current_width, self.current_height) // 2 + 18
            pygame.draw.circle(surface, pygame.Color("#6cf6ff"), self.rect.center, radius, width=3)
        if blink and self.shield_strength < 0.4:
            return

        rect = self.rect
        x, y, w, h = rect.x, rect.y, rect.w, rect.h
        pace = math.sin(self.animation_time * 15.0)
        leg_lift = 7 if pace > 0 else -5

        shadow = pygame.Rect(x + 10, self.ground_y + 6, max(24, w - 18), 10)
        pygame.draw.ellipse(surface, pygame.Color(0, 0, 0, 70), shadow)

        if self.ducking:
            body = pygame.Rect(x + 14, y + 16, w - 26, h - 22)
            head = pygame.Rect(x + w - 34, y + 8, 26, 24)
            tail = [(x + 12, y + h - 18), (x - 8, y + h - 24), (x + 10, y + h - 32)]
            leg_a = pygame.Rect(x + 26, y + h - 12, 18, 8)
            leg_b = pygame.Rect(x + 54, y + h - 12, 20, 8)
        else:
            body = pygame.Rect(x + 18, y + 24, w - 28, h - 34)
            head = pygame.Rect(x + w - 30, y + 6, 24, 26)
            tail = [(x + 14, y + h - 18), (x - 10, y + h - 28), (x + 12, y + h - 42)]
            leg_a = pygame.Rect(x + 24, y + h - 18 + leg_lift, 14, 18)
            leg_b = pygame.Rect(x + 48, y + h - 18 - leg_lift, 14, 18)

        arm = pygame.Rect(x + w - 34, y + h // 2 - 2, 18, 8)
        pygame.draw.polygon(surface, self.accent_color, tail)
        pygame.draw.rect(surface, self.body_color, body, border_radius=8)
        pygame.draw.rect(surface, self.body_color, head, border_radius=6)
        pygame.draw.rect(surface, self.accent_color, arm, border_radius=4)
        pygame.draw.rect(surface, self.accent_color, leg_a, border_radius=3)
        pygame.draw.rect(surface, self.accent_color, leg_b, border_radius=3)

        eye = pygame.Rect(head.x + 16, head.y + 8, 4, 4)
        pygame.draw.rect(surface, self.eye_color, eye)
        pygame.draw.line(surface, self.outline_color, (head.x + 4, head.y + 14), (head.x + 14, head.y + 14), 2)

        for shape in (body, head, arm, leg_a, leg_b):
            pygame.draw.rect(surface, self.outline_color, shape, width=2, border_radius=4)
        pygame.draw.polygon(surface, self.outline_color, tail, width=2)


@dataclass
class Hazard:
    kind: str
    x: float
    y: float
    width: int
    height: int
    tint: str
    speed_scale: float = 1.0
    phase: float = field(default_factory=lambda: random.uniform(0.0, math.tau))

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    @property
    def collider(self) -> pygame.Rect:
        padding_x = 12 if self.kind == "cactus" else 8
        padding_y = 8
        return self.rect.inflate(-padding_x, -padding_y)

    @property
    def offscreen(self) -> bool:
        return self.x + self.width < -32

    def update(self, dt: float, speed: float) -> None:
        self.x -= speed * self.speed_scale * dt
        self.phase += dt * 8.0

    def draw(self, surface: pygame.Surface) -> None:
        color = _color(self.tint)
        outline = pygame.Color("#12202a")
        rect = self.rect

        if self.kind == "cactus":
            trunk = pygame.Rect(rect.x + rect.w // 3, rect.y + 8, rect.w // 3, rect.h - 8)
            arm_left = pygame.Rect(rect.x + 6, rect.y + rect.h // 3, rect.w // 4, rect.h // 4)
            arm_right = pygame.Rect(rect.right - rect.w // 4 - 6, rect.y + rect.h // 2 - 6, rect.w // 4, rect.h // 4)
            pygame.draw.rect(surface, color, trunk, border_radius=4)
            pygame.draw.rect(surface, color, arm_left, border_radius=4)
            pygame.draw.rect(surface, color, arm_right, border_radius=4)
            for shape in (trunk, arm_left, arm_right):
                pygame.draw.rect(surface, outline, shape, width=2, border_radius=4)
        elif self.kind == "bird":
            wing_offset = 12 if math.sin(self.phase) > 0 else -6
            body = pygame.Rect(rect.x + 12, rect.y + 14, rect.w - 24, rect.h - 22)
            wing_top = [(rect.centerx - 8, rect.y + 22), (rect.centerx + wing_offset, rect.y + 8), (rect.centerx + 8, rect.y + 28)]
            wing_bottom = [(rect.centerx - 8, rect.y + 26), (rect.centerx + wing_offset, rect.y + 42), (rect.centerx + 8, rect.y + 32)]
            beak = [(rect.right - 8, rect.y + 26), (rect.right + 6, rect.y + 30), (rect.right - 8, rect.y + 34)]
            pygame.draw.ellipse(surface, color, body)
            pygame.draw.polygon(surface, color, wing_top)
            pygame.draw.polygon(surface, color, wing_bottom)
            pygame.draw.polygon(surface, pygame.Color("#f2a541"), beak)
            pygame.draw.ellipse(surface, outline, body, width=2)
        else:
            body = pygame.Rect(rect.x + 6, rect.y + 12, rect.w - 12, rect.h - 18)
            core = pygame.Rect(rect.x + rect.w // 2 - 8, rect.y + rect.h // 2 - 8, 16, 16)
            pygame.draw.rect(surface, color, body, border_radius=10)
            pygame.draw.rect(surface, outline, body, width=2, border_radius=10)
            pygame.draw.rect(surface, pygame.Color("#ff9f40"), core, border_radius=6)
            for offset in (-18, 18):
                tip = (rect.centerx + offset, rect.y + 8)
                pygame.draw.line(surface, outline, (rect.centerx, rect.y + 18), tip, 3)
                pygame.draw.circle(surface, color, tip, 5)


@dataclass
class Coin:
    x: float
    y: float
    radius: int = 16
    phase: float = field(default_factory=lambda: random.uniform(0.0, math.tau))

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - self.radius), int(self.y - self.radius), self.radius * 2, self.radius * 2)

    @property
    def offscreen(self) -> bool:
        return self.x + self.radius < -32

    def update(self, dt: float, speed: float, magnet_target: tuple[float, float] | None = None) -> None:
        self.x -= speed * dt
        self.phase += dt * 7.0
        if magnet_target is not None:
            tx, ty = magnet_target
            dx = tx - self.x
            dy = ty - self.y
            distance = math.hypot(dx, dy)
            if 0 < distance < 240:
                strength = 1.0 - distance / 240.0
                self.x += dx * dt * 4.0 * strength
                self.y += dy * dt * 4.0 * strength

    def draw(self, surface: pygame.Surface) -> None:
        width = max(6, int(abs(math.sin(self.phase)) * self.radius * 2))
        body = pygame.Rect(int(self.x - width // 2), int(self.y - self.radius), width, self.radius * 2)
        pygame.draw.ellipse(surface, pygame.Color("#f9da57"), body)
        pygame.draw.ellipse(surface, pygame.Color("#7a5b18"), body, width=3)
        pygame.draw.line(surface, pygame.Color("#fff3a6"), (body.centerx, body.y + 5), (body.centerx, body.bottom - 5), 2)


@dataclass
class PowerUpItem:
    power_type: str
    x: float
    y: float
    size: int = 28
    phase: float = field(default_factory=lambda: random.uniform(0.0, math.tau))

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - self.size // 2), int(self.y - self.size // 2), self.size, self.size)

    @property
    def offscreen(self) -> bool:
        return self.x + self.size < -32

    def update(self, dt: float, speed: float) -> None:
        self.x -= speed * dt
        self.phase += dt * 6.0

    def draw(self, surface: pygame.Surface) -> None:
        colors = {
            "shield": "#6cf6ff",
            "slow": "#8ab7ff",
            "double_jump": "#ff9ae8",
            "magnet": "#ff7a59",
            "multiplier": "#caff7a",
        }
        rect = self.rect.move(0, int(math.sin(self.phase) * 4))
        color = pygame.Color(colors.get(self.power_type, "#ffffff"))
        pygame.draw.rect(surface, color, rect, border_radius=8)
        pygame.draw.rect(surface, pygame.Color("#102030"), rect, width=2, border_radius=8)
        glyph = self.power_type[0].upper()
        font = pygame.font.SysFont(["Consolas", "Courier New"], 18, bold=True)
        text = font.render(glyph, True, pygame.Color("#102030"))
        surface.blit(text, text.get_rect(center=rect.center))


def spawn_ground_hazard(spawn_x: float, ground_y: int) -> Hazard:
    variants = [
        (44, 78, "#355f39"),
        (58, 94, "#2b6c50"),
        (72, 112, "#4b7042"),
    ]
    width, height, tint = random.choice(variants)
    return Hazard("cactus", spawn_x, ground_y - height, width, height, tint, speed_scale=random.uniform(0.95, 1.1))


def spawn_flying_hazard(spawn_x: float, ground_y: int, *, challenge: bool = False) -> Hazard:
    if challenge and random.random() < 0.45:
        width, height = 76, 52
        y = ground_y - random.choice((164, 210, 246))
        return Hazard("drone", spawn_x, y, width, height, "#96a3ff", speed_scale=random.uniform(1.1, 1.25))
    width, height = 84, 56
    y = ground_y - random.choice((134, 196, 250))
    return Hazard("bird", spawn_x, y, width, height, "#ece7d2", speed_scale=random.uniform(1.0, 1.18))


def spawn_coin_line(spawn_x: float, ground_y: int) -> list[Coin]:
    height = random.choice((110, 150, 210))
    count = random.randint(3, 6)
    spacing = 42
    return [Coin(spawn_x + index * spacing, ground_y - height - index % 2 * 8) for index in range(count)]


def spawn_powerup(spawn_x: float, ground_y: int) -> PowerUpItem:
    power_type = random.choice(["shield", "slow", "double_jump", "magnet", "multiplier"])
    return PowerUpItem(power_type=power_type, x=spawn_x, y=ground_y - random.choice((136, 176, 222)))
