"""UI rendering helpers and clickable button layouts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pygame

from .constants import APP_NAME, LOGICAL_HEIGHT, LOGICAL_WIDTH, STARTUP_NOTICE_LINES, VERSION


@dataclass
class Button:
    label: str
    action: str
    rect: pygame.Rect
    hotkey: str = ""

    def contains(self, point: tuple[int, int]) -> bool:
        return self.rect.collidepoint(point)


class UIRenderer:
    def __init__(self, assets: Any) -> None:
        self.assets = assets

    def _text(
        self,
        surface: pygame.Surface,
        text: str,
        size: int,
        color: str | pygame.Color,
        pos: tuple[int, int],
        *,
        center: bool = False,
        bold: bool = False,
    ) -> pygame.Rect:
        font = self.assets.get_font(size, bold=bold)
        rendered = font.render(text, True, pygame.Color(color))
        rect = rendered.get_rect(center=pos) if center else rendered.get_rect(topleft=pos)
        shadow = rendered.copy()
        shadow.fill((0, 0, 0, 120), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(shadow, rect.move(3, 3))
        surface.blit(rendered, rect)
        return rect

    def _panel(self, surface: pygame.Surface, rect: pygame.Rect, fill: str, outline: str) -> None:
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel.fill((0, 0, 0, 0))
        pygame.draw.rect(panel, pygame.Color(fill), panel.get_rect(), border_radius=18)
        pygame.draw.rect(panel, pygame.Color(outline), panel.get_rect(), width=3, border_radius=18)
        surface.blit(panel, rect.topleft)

    def _button(self, surface: pygame.Surface, button: Button, hovered: bool) -> None:
        fill = "#f3c969" if hovered else "#f7efe1"
        text_color = "#1d2430"
        pygame.draw.rect(surface, pygame.Color(fill), button.rect, border_radius=14)
        pygame.draw.rect(surface, pygame.Color("#253347"), button.rect, width=3, border_radius=14)
        self._text(surface, button.label, 26, text_color, button.rect.center, center=True, bold=True)
        if button.hotkey:
            self._text(surface, button.hotkey, 18, "#253347", (button.rect.right - 56, button.rect.y + 10), bold=True)

    def notice_buttons(self) -> list[Button]:
        return [
            Button("Continue", "continue_notice", pygame.Rect(410, 540, 220, 62), "Enter"),
            Button("Quit", "quit", pygame.Rect(650, 540, 220, 62), "Esc"),
        ]

    def menu_buttons(self) -> list[Button]:
        return [
            Button("Start Run", "start_run", pygame.Rect(96, 420, 260, 62), "Enter"),
            Button("Tutorial", "show_tutorial", pygame.Rect(96, 498, 260, 62), "T"),
            Button("Settings", "show_settings", pygame.Rect(96, 576, 260, 62), "S"),
            Button("Quit", "quit", pygame.Rect(96, 654, 260, 52), "Esc"),
        ]

    def pause_buttons(self) -> list[Button]:
        return [
            Button("Resume", "resume", pygame.Rect(480, 300, 320, 62), "P"),
            Button("Settings", "show_settings", pygame.Rect(480, 380, 320, 62), "S"),
            Button("Menu", "return_menu", pygame.Rect(480, 460, 320, 62), "Esc"),
        ]

    def game_over_buttons(self) -> list[Button]:
        return [
            Button("Restart", "start_run", pygame.Rect(420, 520, 200, 60), "Enter"),
            Button("Menu", "return_menu", pygame.Rect(650, 520, 200, 60), "Esc"),
        ]

    def settings_buttons(self) -> list[Button]:
        return [
            Button("Toggle Fullscreen", "toggle_fullscreen", pygame.Rect(96, 238, 320, 56), "F11"),
            Button("Toggle Focus Mode", "toggle_focus_mode", pygame.Rect(96, 310, 320, 56), "F"),
            Button("Toggle Mute", "toggle_mute", pygame.Rect(96, 382, 320, 56), "M"),
            Button("Music -", "music_down", pygame.Rect(96, 478, 150, 56), ""),
            Button("Music +", "music_up", pygame.Rect(266, 478, 150, 56), ""),
            Button("FX -", "effects_down", pygame.Rect(96, 550, 150, 56), ""),
            Button("FX +", "effects_up", pygame.Rect(266, 550, 150, 56), ""),
            Button("Prev Skin", "skin_prev", pygame.Rect(96, 622, 150, 56), ""),
            Button("Next Skin", "skin_next", pygame.Rect(266, 622, 150, 56), ""),
            Button("Back", "close_settings", pygame.Rect(960, 626, 180, 56), "Esc"),
        ]

    def tutorial_buttons(self) -> list[Button]:
        return [Button("Back To Menu", "return_menu", pygame.Rect(930, 628, 220, 58), "Esc")]

    def draw_notice(self, surface: pygame.Surface, hovered_action: str | None) -> None:
        self._panel(surface, pygame.Rect(180, 90, 920, 560), "#f9efd0dd", "#253347")
        self._text(surface, "Startup Notice", 48, "#1d2430", (640, 150), center=True, bold=True)
        y = 220
        for line in STARTUP_NOTICE_LINES:
            size = 22 if line else 12
            color = "#2b3445" if line else "#00000000"
            self._text(surface, line, size, color, (220, y))
            y += 38 if line else 18

        for button in self.notice_buttons():
            self._button(surface, button, hovered_action == button.action)

    def draw_menu(
        self,
        surface: pygame.Surface,
        hovered_action: str | None,
        high_score: int,
        total_coins: int,
        selected_skin: dict[str, Any],
        unlocked_count: int,
    ) -> None:
        self._text(surface, APP_NAME, 60, "#f8f3e5", (96, 92), bold=True)
        self._text(surface, "A polished, assignment-safe endless runner demo.", 28, "#f8f3e5", (98, 154))
        self._text(surface, f"Version {VERSION}", 18, "#f7d66a", (98, 194))
        self._text(surface, f"Best Score: {high_score}", 26, "#ffffff", (96, 270), bold=True)
        self._text(surface, f"Lifetime Coins: {total_coins}", 24, "#ffffff", (96, 308))
        self._text(surface, f"Unlocked Skins: {unlocked_count}", 24, "#ffffff", (96, 342))

        for button in self.menu_buttons():
            self._button(surface, button, hovered_action == button.action)

        card = pygame.Rect(748, 132, 420, 468)
        self._panel(surface, card, "#101724cc", "#f7d66a")
        self._text(surface, "Selected Skin", 34, "#f8f3e5", (958, 176), center=True, bold=True)
        preview = pygame.Rect(834, 242, 250, 212)
        pygame.draw.rect(surface, pygame.Color("#f4ecd4"), preview, border_radius=18)
        pygame.draw.rect(surface, pygame.Color("#1d2430"), preview, width=3, border_radius=18)
        pygame.draw.rect(surface, pygame.Color(selected_skin["body"]), pygame.Rect(906, 332, 120, 70), border_radius=14)
        pygame.draw.rect(surface, pygame.Color(selected_skin["accent"]), pygame.Rect(1006, 288, 54, 54), border_radius=10)
        pygame.draw.rect(surface, pygame.Color(selected_skin["outline"]), pygame.Rect(906, 332, 120, 70), width=3, border_radius=14)
        pygame.draw.rect(surface, pygame.Color(selected_skin["eye"]), pygame.Rect(1040, 304, 6, 6))
        self._text(surface, selected_skin["name"], 30, "#f8f3e5", (958, 488), center=True, bold=True)
        self._text(surface, f"Unlock Score: {selected_skin['unlock_score']}", 22, "#f8f3e5", (958, 524), center=True)
        self._text(surface, "F11 fullscreen  |  M mute  |  P pause", 20, "#f7d66a", (958, 572), center=True)

    def draw_settings(
        self,
        surface: pygame.Surface,
        hovered_action: str | None,
        settings: dict[str, Any],
        current_skin: dict[str, Any],
    ) -> None:
        self._panel(surface, pygame.Rect(56, 74, 1168, 600), "#f7efe4eb", "#253347")
        self._text(surface, "Settings", 48, "#1d2430", (96, 110), bold=True)
        self._text(surface, "Adjust window, audio, and skin preferences.", 24, "#415069", (96, 156))

        for button in self.settings_buttons():
            self._button(surface, button, hovered_action == button.action)

        status_lines = [
            f"Fullscreen: {'On' if settings['fullscreen'] else 'Off'}",
            f"Focus Mode: {'On' if settings['focus_mode'] else 'Off'}",
            f"Mute: {'On' if settings['mute'] else 'Off'}",
            f"Music Volume: {int(settings['music_volume'] * 100)}%",
            f"Effects Volume: {int(settings['effects_volume'] * 100)}%",
            f"Current Skin: {current_skin['name']}",
        ]
        y = 244
        for line in status_lines:
            self._text(surface, line, 26, "#243246", (488, y), bold=True)
            y += 58

        preview = pygame.Rect(852, 196, 284, 290)
        pygame.draw.rect(surface, pygame.Color("#fff7e9"), preview, border_radius=18)
        pygame.draw.rect(surface, pygame.Color("#253347"), preview, width=3, border_radius=18)
        pygame.draw.rect(surface, pygame.Color(current_skin["body"]), pygame.Rect(910, 322, 132, 82), border_radius=14)
        pygame.draw.rect(surface, pygame.Color(current_skin["accent"]), pygame.Rect(1014, 272, 56, 56), border_radius=12)
        pygame.draw.rect(surface, pygame.Color(current_skin["outline"]), pygame.Rect(910, 322, 132, 82), width=3, border_radius=14)
        self._text(surface, current_skin["name"], 28, "#1d2430", (994, 432), center=True, bold=True)

    def draw_tutorial(self, surface: pygame.Surface, hovered_action: str | None, tutorial_steps: list[str]) -> None:
        self._panel(surface, pygame.Rect(72, 70, 1136, 612), "#eef5ffec", "#253347")
        self._text(surface, "First-Time Tutorial", 48, "#1d2430", (96, 110), bold=True)
        y = 196
        for index, line in enumerate(tutorial_steps, start=1):
            self._text(surface, f"{index}. {line}", 27, "#27374d", (104, y))
            y += 68
        self._text(surface, "Tip: coins extend streaks, power-ups stack, and challenge waves increase score gain.", 22, "#415069", (104, 560))

        for button in self.tutorial_buttons():
            self._button(surface, button, hovered_action == button.action)

    def draw_hud(
        self,
        surface: pygame.Surface,
        *,
        score: int,
        high_score: int,
        coins: int,
        streak: int,
        biome_name: str,
        powerups: dict[str, float],
        muted: bool,
        challenge_active: bool,
    ) -> None:
        hud = pygame.Rect(28, 22, 410, 122)
        self._panel(surface, hud, "#101724bb", "#f7d66a")
        self._text(surface, f"Score {score:05d}", 30, "#f8f3e5", (48, 42), bold=True)
        self._text(surface, f"Best {high_score:05d}", 22, "#f8f3e5", (48, 84))
        self._text(surface, f"Coins {coins}", 22, "#f8f3e5", (232, 84))
        self._text(surface, f"Streak x{max(streak, 1)}", 22, "#f7d66a", (320, 84))

        tag = pygame.Rect(1038, 22, 214, 54)
        self._panel(surface, tag, "#101724bb", "#f7d66a")
        text = biome_name + ("  |  CHALLENGE" if challenge_active else "")
        self._text(surface, text, 20, "#f8f3e5", tag.center, center=True, bold=True)
        if muted:
            self._text(surface, "MUTED", 18, "#ff9f71", (1146, 92), center=True, bold=True)

        active = [(name.replace("_", " ").title(), timer) for name, timer in powerups.items() if timer > 0.1]
        y = 134
        for name, timer in active[:4]:
            self._text(surface, f"{name}: {timer:0.1f}s", 20, "#f8f3e5", (1020, y), bold=True)
            y += 28

    def draw_pause(self, surface: pygame.Surface, hovered_action: str | None) -> None:
        overlay = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 10, 16, 180))
        surface.blit(overlay, (0, 0))
        self._panel(surface, pygame.Rect(430, 210, 420, 360), "#f7efe4f2", "#253347")
        self._text(surface, "Paused", 50, "#1d2430", (640, 264), center=True, bold=True)
        self._text(surface, "Gameplay is cleanly paused. No hidden background activity.", 22, "#415069", (640, 314), center=True)
        for button in self.pause_buttons():
            self._button(surface, button, hovered_action == button.action)

    def draw_game_over(
        self,
        surface: pygame.Surface,
        hovered_action: str | None,
        summary: dict[str, Any],
    ) -> None:
        self._panel(surface, pygame.Rect(300, 108, 680, 520), "#f7efe4f0", "#253347")
        self._text(surface, "Run Complete", 52, "#1d2430", (640, 162), center=True, bold=True)
        lines = [
            f"Score: {summary['score']}",
            f"Coins: {summary['coins']}",
            f"Best Streak: {summary['streak']}",
            f"Challenge Waves Cleared: {summary['challenges']}",
            "New High Score!" if summary["new_high_score"] else "Try another run to beat your best.",
        ]
        y = 250
        for line in lines:
            self._text(surface, line, 28, "#253347", (640, y), center=True, bold=True)
            y += 52

        if summary["new_items"]:
            self._text(surface, "New Unlocks", 26, "#d06a34", (640, 500), center=True, bold=True)
            self._text(surface, ", ".join(summary["new_items"][:3]), 22, "#415069", (640, 538), center=True)

        for button in self.game_over_buttons():
            self._button(surface, button, hovered_action == button.action)

    def draw_toasts(self, surface: pygame.Surface, toasts: list[dict[str, Any]]) -> None:
        y = 162
        for toast in toasts[:3]:
            rect = pygame.Rect(24, y, 320, 70)
            self._panel(surface, rect, "#101724dd", "#f7d66a")
            self._text(surface, toast["title"], 24, "#f7d66a", (40, y + 14), bold=True)
            self._text(surface, toast["body"], 18, "#f8f3e5", (40, y + 42))
            y += 84
