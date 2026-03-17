"""Lightweight particle effects for movement, collisions, and pickups."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

import pygame


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    size: float
    color: pygame.Color
    gravity: float = 0.0

    def update(self, dt: float) -> None:
        self.life -= dt
        self.vy += self.gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

    def draw(self, surface: pygame.Surface) -> None:
        if self.life <= 0:
            return
        alpha = max(0, min(255, int(255 * (self.life / self.max_life))))
        color = pygame.Color(self.color)
        color.a = alpha
        rect = pygame.Rect(int(self.x), int(self.y), max(1, int(self.size)), max(1, int(self.size)))
        pygame.draw.rect(surface, color, rect)


class ParticleSystem:
    def __init__(self) -> None:
        self.particles: list[Particle] = []

    def _burst(
        self,
        position: tuple[float, float],
        color: str,
        *,
        count: int,
        speed: tuple[float, float],
        lifetime: tuple[float, float],
        size: tuple[float, float],
        gravity: float = 0.0,
        spread: float = math.pi,
        angle_bias: float = 0.0,
    ) -> None:
        px, py = position
        base = pygame.Color(color)
        for _ in range(count):
            angle = angle_bias + random.uniform(-spread * 0.5, spread * 0.5)
            magnitude = random.uniform(*speed)
            self.particles.append(
                Particle(
                    x=px,
                    y=py,
                    vx=math.cos(angle) * magnitude,
                    vy=math.sin(angle) * magnitude,
                    life=random.uniform(*lifetime),
                    max_life=lifetime[1],
                    size=random.uniform(*size),
                    color=base,
                    gravity=gravity,
                )
            )

    def emit_jump(self, position: tuple[float, float]) -> None:
        self._burst(position, "#d9c47a", count=10, speed=(40, 160), lifetime=(0.20, 0.44), size=(3, 7))

    def emit_landing(self, position: tuple[float, float]) -> None:
        self._burst(
            position,
            "#8d7b5a",
            count=12,
            speed=(70, 210),
            lifetime=(0.18, 0.40),
            size=(3, 8),
            gravity=420,
            angle_bias=-math.pi / 2,
            spread=math.pi / 1.6,
        )

    def emit_pickup(self, position: tuple[float, float], color: str = "#f8e45c") -> None:
        self._burst(position, color, count=14, speed=(60, 200), lifetime=(0.20, 0.50), size=(2, 6))

    def emit_crash(self, position: tuple[float, float]) -> None:
        self._burst(
            position,
            "#ff7058",
            count=20,
            speed=(90, 260),
            lifetime=(0.28, 0.65),
            size=(4, 10),
            gravity=320,
        )

    def emit_shield(self, position: tuple[float, float]) -> None:
        self._burst(position, "#82ecff", count=18, speed=(110, 260), lifetime=(0.24, 0.55), size=(3, 8))

    def update(self, dt: float) -> None:
        for particle in self.particles:
            particle.update(dt)
        self.particles = [particle for particle in self.particles if particle.life > 0]

    def draw(self, surface: pygame.Surface) -> None:
        for particle in self.particles:
            particle.draw(surface)
