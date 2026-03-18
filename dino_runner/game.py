"""Main game loop and screen/state orchestration."""

from __future__ import annotations

import random
from typing import Any

import pygame

from .assets import AssetLibrary
from .audio import AudioManager
from .constants import (
    APP_NAME,
    BASE_SCROLL_SPEED,
    CHALLENGE_DURATION,
    CHALLENGE_INTERVAL,
    COIN_SCORE,
    COMBO_WINDOW,
    FPS,
    GROUND_Y,
    LOGICAL_HEIGHT,
    LOGICAL_SIZE,
    LOGICAL_WIDTH,
    MAX_SCROLL_SPEED,
    POWERUP_DURATIONS,
    SCORE_RATE,
    WINDOW_TITLE,
)
from .effects import ParticleSystem
from .entities import (
    Player,
    spawn_coin_line,
    spawn_flying_hazard,
    spawn_ground_hazard,
    spawn_powerup,
)
from .storage import StorageManager
from .ui import Button, UIRenderer
from .world import World


class Game:
    def __init__(self, *, debug: bool = False) -> None:
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()
        pygame.display.set_caption(WINDOW_TITLE)

        self.debug = debug
        self.assets = AssetLibrary()
        self.storage = StorageManager()
        self.audio = AudioManager(self.storage.settings)
        self.ui = UIRenderer(self.assets)
        self.world = World(self.assets.biomes)
        self.player = Player(GROUND_Y, self.assets.get_skin(self.storage.save_data["selected_skin"]))
        self.particles = ParticleSystem()

        self.windowed_size = list(LOGICAL_SIZE)
        self.fullscreen = bool(self.storage.settings.get("fullscreen", False))
        self.screen = self._create_display(self.fullscreen)
        self.canvas = pygame.Surface(LOGICAL_SIZE, pygame.SRCALPHA)
        self.clock = pygame.time.Clock()
        self.present_rect = pygame.Rect(0, 0, *LOGICAL_SIZE)

        self.running = True
        self.state = "notice"
        self.settings_return_state = "menu"
        self.hovered_action: str | None = None
        self.last_summary = {
            "score": 0,
            "coins": 0,
            "streak": 0,
            "challenges": 0,
            "new_high_score": False,
            "new_items": [],
        }
        self.toasts: list[dict[str, Any]] = []

        self._reset_run_state()
        self._update_cursor_visibility()

    def _create_display(self, fullscreen: bool) -> pygame.Surface:
        flags = 0
        size: tuple[int, int]
        if fullscreen:
            flags = pygame.FULLSCREEN
            size = (0, 0)
        else:
            flags = pygame.RESIZABLE
            size = tuple(self.windowed_size)
        return pygame.display.set_mode(size, flags)

    def _logical_mouse_pos(self, position: tuple[int, int]) -> tuple[int, int]:
        if self.present_rect.width == 0 or self.present_rect.height == 0:
            return position
        x, y = position
        if not self.present_rect.collidepoint(position):
            return (-1, -1)
        px = (x - self.present_rect.x) / self.present_rect.width
        py = (y - self.present_rect.y) / self.present_rect.height
        return int(px * LOGICAL_WIDTH), int(py * LOGICAL_HEIGHT)

    def _present(self) -> None:
        window_size = self.screen.get_size()
        scale = min(window_size[0] / LOGICAL_WIDTH, window_size[1] / LOGICAL_HEIGHT)
        draw_size = (max(1, int(LOGICAL_WIDTH * scale)), max(1, int(LOGICAL_HEIGHT * scale)))
        offset = ((window_size[0] - draw_size[0]) // 2, (window_size[1] - draw_size[1]) // 2)
        self.present_rect = pygame.Rect(offset, draw_size)
        self.screen.fill((8, 10, 16))
        frame = pygame.transform.smoothscale(self.canvas, draw_size)
        self.screen.blit(frame, offset)
        pygame.display.flip()

    def _update_cursor_visibility(self) -> None:
        focus_mode = bool(self.storage.settings.get("focus_mode", True))
        hide = focus_mode and self.state == "playing"
        pygame.mouse.set_visible(not hide)

    def _queue_toast(self, title: str, body: str, *, duration: float = 3.2) -> None:
        self.toasts.append({"title": title, "body": body, "timer": duration})

    def _update_toasts(self, dt: float) -> None:
        for toast in self.toasts:
            toast["timer"] -= dt
        self.toasts = [toast for toast in self.toasts if toast["timer"] > 0]

    def _reset_run_state(self) -> None:
        self.player.set_skin(self.assets.get_skin(self.storage.save_data["selected_skin"]))
        self.player.reset()

        self.score = 0.0
        self.run_coins = 0
        self.combo_streak = 0
        self.combo_timer = 0.0
        self.best_run_streak = 0
        self.completed_challenges = 0
        self.flags: set[str] = set()
        self.run_unlocks: list[str] = []

        self.scroll_speed = BASE_SCROLL_SPEED
        self.challenge_active = False
        self.challenge_timer = 0.0
        self.next_challenge_score = CHALLENGE_INTERVAL

        self.hazards: list[Any] = []
        self.coins: list[Any] = []
        self.powerups_on_track: list[Any] = []
        self.powerup_timers = {key: 0.0 for key in POWERUP_DURATIONS}

        self.obstacle_timer = 1.0
        self.coin_timer = 2.0
        self.powerup_timer = 8.0

    def _current_buttons(self) -> list[Button]:
        if self.state == "notice":
            return self.ui.notice_buttons()
        if self.state == "menu":
            return self.ui.menu_buttons()
        if self.state == "tutorial":
            return self.ui.tutorial_buttons()
        if self.state == "settings":
            return self.ui.settings_buttons()
        if self.state == "paused":
            return self.ui.pause_buttons()
        if self.state == "game_over":
            return self.ui.game_over_buttons()
        return []

    def _button_action_at(self, logical_mouse: tuple[int, int]) -> str | None:
        for button in self._current_buttons():
            if button.contains(logical_mouse):
                return button.action
        return None

    def _open_settings(self) -> None:
        self.settings_return_state = self.state if self.state != "settings" else self.settings_return_state
        if self.settings_return_state == "playing":
            self.settings_return_state = "paused"
        self.state = "settings"
        self.audio.play_effect("menu")
        self._update_cursor_visibility()

    def _close_settings(self) -> None:
        self.state = self.settings_return_state
        self.audio.play_effect("menu")
        self._update_cursor_visibility()

    def _toggle_fullscreen(self) -> None:
        self.fullscreen = not self.fullscreen
        self.storage.set_setting("fullscreen", self.fullscreen)
        self.screen = self._create_display(self.fullscreen)

    def _toggle_mute(self) -> None:
        muted = not bool(self.storage.settings.get("mute", False))
        self.storage.set_setting("mute", muted)

    def _toggle_focus_mode(self) -> None:
        enabled = not bool(self.storage.settings.get("focus_mode", True))
        self.storage.set_setting("focus_mode", enabled)
        self._update_cursor_visibility()

    def _adjust_volume(self, key: str, delta: float) -> None:
        value = float(self.storage.settings.get(key, 0.5))
        value = max(0.0, min(1.0, value + delta))
        self.storage.set_setting(key, round(value, 2))

    def _cycle_skin(self, direction: int) -> None:
        unlocked = self.storage.save_data["unlocked_skins"]
        if not unlocked:
            return
        current = self.storage.save_data["selected_skin"]
        index = unlocked.index(current)
        new_id = unlocked[(index + direction) % len(unlocked)]
        self.storage.set_selected_skin(new_id)
        self.player.set_skin(self.assets.get_skin(new_id))
        self.audio.play_effect("menu")

    def _continue_notice(self) -> None:
        self.state = "tutorial" if self.storage.save_data.get("first_run", True) else "menu"
        self.audio.play_effect("menu")
        self._update_cursor_visibility()

    def _start_run(self) -> None:
        self._reset_run_state()
        self.state = "playing"
        self.audio.play_effect("menu")
        self._update_cursor_visibility()

    def _return_menu(self) -> None:
        self.state = "menu"
        self.settings_return_state = "menu"
        self.audio.play_effect("menu")
        self._update_cursor_visibility()

    def _pause(self) -> None:
        if self.state == "playing":
            self.state = "paused"
            self.audio.play_effect("menu")
            self._update_cursor_visibility()

    def _resume(self) -> None:
        if self.state == "paused":
            self.state = "playing"
            self.audio.play_effect("menu")
            self._update_cursor_visibility()

    def _activate_action(self, action: str | None) -> None:
        if action is None:
            return
        if action == "continue_notice":
            self._continue_notice()
        elif action == "start_run":
            self._start_run()
        elif action == "show_tutorial":
            self.state = "tutorial"
            self.audio.play_effect("menu")
        elif action == "show_settings":
            self._open_settings()
        elif action == "toggle_fullscreen":
            self._toggle_fullscreen()
        elif action == "toggle_focus_mode":
            self._toggle_focus_mode()
        elif action == "toggle_mute":
            self._toggle_mute()
        elif action == "music_down":
            self._adjust_volume("music_volume", -0.05)
        elif action == "music_up":
            self._adjust_volume("music_volume", 0.05)
        elif action == "effects_down":
            self._adjust_volume("effects_volume", -0.05)
        elif action == "effects_up":
            self._adjust_volume("effects_volume", 0.05)
        elif action == "skin_prev":
            self._cycle_skin(-1)
        elif action == "skin_next":
            self._cycle_skin(1)
        elif action == "close_settings":
            self._close_settings()
        elif action == "resume":
            self._resume()
        elif action == "return_menu":
            self._return_menu()
        elif action == "quit":
            self.running = False

    def _spawn_obstacle(self) -> None:
        if self.hazards and max(hazard.x for hazard in self.hazards) > LOGICAL_WIDTH - 220:
            return
        spawn_x = LOGICAL_WIDTH + random.randint(120, 260)
        flying_weight = min(0.18 + self.score / 2600.0, 0.55)
        if self.challenge_active or random.random() < flying_weight:
            hazard = spawn_flying_hazard(spawn_x, GROUND_Y, challenge=self.challenge_active)
        else:
            hazard = spawn_ground_hazard(spawn_x, GROUND_Y)
        self.hazards.append(hazard)
        base = random.uniform(0.78, 1.28) - min(0.38, self.scroll_speed / 2400.0)
        self.obstacle_timer = max(0.34, base * (0.64 if self.challenge_active else 1.0))

    def _spawn_coin_wave(self) -> None:
        if self.coins and max(coin.x for coin in self.coins) > LOGICAL_WIDTH - 180:
            return
        self.coins.extend(spawn_coin_line(LOGICAL_WIDTH + random.randint(120, 240), GROUND_Y))
        self.coin_timer = random.uniform(2.4, 4.0) * (0.72 if self.challenge_active else 1.0)

    def _spawn_powerup(self) -> None:
        if self.powerups_on_track:
            self.powerup_timer = random.uniform(6.0, 10.0)
            return
        self.powerups_on_track.append(spawn_powerup(LOGICAL_WIDTH + random.randint(160, 280), GROUND_Y))
        self.powerup_timer = random.uniform(9.0, 15.0)

    def _start_challenge(self) -> None:
        self.challenge_active = True
        self.challenge_timer = CHALLENGE_DURATION
        self.next_challenge_score += CHALLENGE_INTERVAL
        self.flags.add("challenge_started")
        self._queue_toast("Challenge Wave", "Dense hazards incoming. Score gain boosted.")

    def _finish_challenge(self) -> None:
        if not self.challenge_active:
            return
        self.challenge_active = False
        self.completed_challenges += 1
        self._queue_toast("Wave Cleared", "You survived the special challenge section.")

    def _collect_coin(self, coin: Any) -> None:
        self.coins.remove(coin)
        self.run_coins += 1
        if self.combo_timer > 0:
            self.combo_streak += 1
        else:
            self.combo_streak = 1
        self.combo_timer = COMBO_WINDOW
        self.best_run_streak = max(self.best_run_streak, self.combo_streak)
        self.score += COIN_SCORE * (2 if self.powerup_timers["multiplier"] > 0 else 1)
        self.particles.emit_pickup((coin.x, coin.y))
        self.audio.play_effect("coin")
        if self.combo_streak in {3, 5, 8}:
            self._queue_toast("Combo Up", f"Coin streak reached x{self.combo_streak}.")

    def _collect_powerup(self, item: Any) -> None:
        self.powerups_on_track.remove(item)
        self.powerup_timers[item.power_type] = max(
            self.powerup_timers[item.power_type],
            POWERUP_DURATIONS[item.power_type],
        )
        self.particles.emit_pickup(item.rect.center, "#8ef2ff")
        self.audio.play_effect("powerup")
        self._queue_toast("Power-Up", item.power_type.replace("_", " ").title())

    def _achievement_met(self, achievement: dict[str, Any]) -> bool:
        achievement_type = achievement["type"]
        value = achievement.get("value")
        if achievement_type == "score":
            return int(self.score) >= int(value)
        if achievement_type == "coins":
            return self.run_coins >= int(value)
        if achievement_type == "streak":
            return self.best_run_streak >= int(value)
        if achievement_type == "challenges":
            return self.completed_challenges >= int(value)
        if achievement_type == "flag":
            return achievement.get("flag") in self.flags
        return False

    def _check_achievements(self) -> None:
        for achievement in self.assets.achievements:
            if achievement["id"] in self.storage.save_data["achievements"]:
                continue
            if not self._achievement_met(achievement):
                continue
            if self.storage.award_achievement(achievement["id"]):
                self.run_unlocks.append(achievement["name"])
                self.audio.play_effect("achievement")
                self._queue_toast("Achievement", achievement["name"], duration=4.2)

    def _end_run(self) -> None:
        score = int(self.score)
        new_high_score = self.storage.record_run(score, self.run_coins, self.best_run_streak)
        unlocked_skins = self.storage.sync_skin_unlocks(self.assets.skins)
        if unlocked_skins:
            skin_names = [self.assets.get_skin(skin_id)["name"] for skin_id in unlocked_skins]
            self.run_unlocks.extend(skin_names)
        self.last_summary = {
            "score": score,
            "coins": self.run_coins,
            "streak": self.best_run_streak,
            "challenges": self.completed_challenges,
            "new_high_score": new_high_score,
            "new_items": self.run_unlocks[:],
        }
        self.state = "game_over"
        self._update_cursor_visibility()

    def _update_idle_scene(self, dt: float) -> None:
        self.world.update(dt * 0.4, 90.0)
        self.player.animation_time += dt * 0.7
        self.player.on_ground = True
        self.player.ducking = False
        self.player.y = GROUND_Y - self.player.base_height
        self._update_toasts(dt)

    def _update_playing(self, dt: float) -> None:
        self._update_toasts(dt)
        self.scroll_speed = min(MAX_SCROLL_SPEED, BASE_SCROLL_SPEED + self.score * 0.25)
        active_slow = self.powerup_timers["slow"] > 0
        effective_speed = self.scroll_speed * (0.66 if active_slow else 1.0)

        for key in self.powerup_timers:
            self.powerup_timers[key] = max(0.0, self.powerup_timers[key] - dt)

        if self.combo_timer > 0:
            self.combo_timer -= dt
        else:
            self.combo_streak = 0

        if self.challenge_active:
            self.challenge_timer -= dt
            if self.challenge_timer <= 0:
                self._finish_challenge()
        elif self.score >= self.next_challenge_score:
            self._start_challenge()

        self.world.update(dt, effective_speed)
        keys = pygame.key.get_pressed()
        duck_pressed = keys[pygame.K_DOWN] or keys[pygame.K_s] or keys[pygame.K_LCTRL]
        landed = self.player.update(dt, duck_pressed=duck_pressed, powerups=self.powerup_timers)
        if landed:
            self.particles.emit_landing((self.player.rect.centerx, GROUND_Y))
            self.audio.play_effect("land")

        self.obstacle_timer -= dt
        self.coin_timer -= dt
        self.powerup_timer -= dt
        if self.obstacle_timer <= 0:
            self._spawn_obstacle()
        if self.coin_timer <= 0:
            self._spawn_coin_wave()
        if self.powerup_timer <= 0:
            self._spawn_powerup()

        for hazard in self.hazards:
            hazard.update(dt, effective_speed)
        magnet_target = self.player.center if self.powerup_timers["magnet"] > 0 else None
        for coin in self.coins:
            coin.update(dt, effective_speed, magnet_target=magnet_target)
        for item in self.powerups_on_track:
            item.update(dt, effective_speed)
        self.particles.update(dt)

        player_hitbox = self.player.collider
        for hazard in self.hazards[:]:
            if hazard.offscreen:
                self.hazards.remove(hazard)
                continue
            if not hazard.collider.colliderect(player_hitbox):
                continue
            if self.powerup_timers["shield"] > 0:
                self.powerup_timers["shield"] = 0.0
                self.hazards.remove(hazard)
                self.flags.add("shield_save")
                self.particles.emit_shield(hazard.rect.center)
                self.audio.play_effect("shield_break")
                self._queue_toast("Shield Used", "The impact was absorbed.")
                break
            self.particles.emit_crash(self.player.center)
            self.audio.play_effect("hit")
            self._end_run()
            return

        for coin in self.coins[:]:
            if coin.offscreen:
                self.coins.remove(coin)
                continue
            if player_hitbox.colliderect(coin.rect):
                self._collect_coin(coin)

        for item in self.powerups_on_track[:]:
            if item.offscreen:
                self.powerups_on_track.remove(item)
                continue
            if player_hitbox.colliderect(item.rect):
                self._collect_powerup(item)

        if self.world.night_ratio() > 0.58:
            self.flags.add("night_run")

        score_multiplier = 1.0 + min(self.combo_streak, 10) * 0.12
        if self.powerup_timers["multiplier"] > 0:
            score_multiplier *= 2.0
        if self.challenge_active:
            score_multiplier *= 1.12
        self.score += dt * SCORE_RATE * score_multiplier
        self.best_run_streak = max(self.best_run_streak, self.combo_streak)
        self._check_achievements()

    def _draw_run_scene(self, theme: dict[str, Any]) -> None:
        for coin in self.coins:
            coin.draw(self.canvas)
        for item in self.powerups_on_track:
            item.draw(self.canvas)
        for hazard in self.hazards:
            hazard.draw(self.canvas)
        self.player.draw(self.canvas)
        self.particles.draw(self.canvas)

        self.ui.draw_hud(
            self.canvas,
            score=int(self.score),
            high_score=int(self.storage.save_data["high_score"]),
            coins=self.run_coins,
            streak=self.combo_streak,
            biome_name=theme["name"],
            powerups=self.powerup_timers,
            muted=bool(self.storage.settings.get("mute", False)),
            challenge_active=self.challenge_active,
        )

    def _draw(self) -> None:
        self.canvas.fill((0, 0, 0))
        draw_score = self.score if self.state in {"playing", "paused", "game_over", "settings"} else float(self.storage.save_data["high_score"])
        challenge_overlay = self.challenge_active and self.state in {"playing", "paused", "game_over", "settings"}
        theme = self.world.draw(self.canvas, draw_score, challenge_overlay)

        if self.state in {"playing", "paused", "game_over"} or (
            self.state == "settings" and self.settings_return_state in {"paused", "game_over"}
        ):
            self._draw_run_scene(theme)
        else:
            self.player.draw(self.canvas)

        if self.state == "notice":
            self.ui.draw_notice(self.canvas, self.hovered_action)
        elif self.state == "menu":
            self.ui.draw_menu(
                self.canvas,
                self.hovered_action,
                high_score=int(self.storage.save_data["high_score"]),
                total_coins=int(self.storage.save_data["coins_collected"]),
                selected_skin=self.assets.get_skin(self.storage.save_data["selected_skin"]),
                unlocked_count=len(self.storage.save_data["unlocked_skins"]),
            )
        elif self.state == "tutorial":
            self.ui.draw_tutorial(self.canvas, self.hovered_action, self.assets.tutorial)
        elif self.state == "settings":
            self.ui.draw_settings(
                self.canvas,
                self.hovered_action,
                self.storage.settings,
                self.assets.get_skin(self.storage.save_data["selected_skin"]),
            )
        elif self.state == "paused":
            self.ui.draw_pause(self.canvas, self.hovered_action)
        elif self.state == "game_over":
            self.ui.draw_game_over(self.canvas, self.hovered_action, self.last_summary)

        if self.toasts:
            self.ui.draw_toasts(self.canvas, self.toasts)

        footer_font = self.assets.get_font(18)
        footer = footer_font.render("Safe local demo. Saves only settings, scores, and optional demo shortcut files.", True, pygame.Color("#f8f3e5"))
        self.canvas.blit(footer, (20, LOGICAL_HEIGHT - 28))

        self._present()

    def _handle_keydown(self, key: int) -> None:
        if key == pygame.K_F11:
            self._toggle_fullscreen()
            return
        if key == pygame.K_m:
            self._toggle_mute()
            return

        if self.state == "notice":
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self._continue_notice()
            elif key == pygame.K_ESCAPE:
                self.running = False
            return

        if self.state == "menu":
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._start_run()
            elif key == pygame.K_t:
                self.state = "tutorial"
            elif key == pygame.K_s:
                self._open_settings()
            elif key == pygame.K_ESCAPE:
                self.running = False
            return

        if self.state == "tutorial":
            if key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER):
                self._return_menu()
            return

        if self.state == "settings":
            if key == pygame.K_ESCAPE:
                self._close_settings()
            elif key == pygame.K_LEFT:
                self._cycle_skin(-1)
            elif key == pygame.K_RIGHT:
                self._cycle_skin(1)
            elif key == pygame.K_MINUS:
                self._adjust_volume("music_volume", -0.05)
            elif key == pygame.K_EQUALS:
                self._adjust_volume("music_volume", 0.05)
            return

        if self.state == "playing":
            if key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                if self.player.jump():
                    self.particles.emit_jump((self.player.rect.x + 20, GROUND_Y))
                    self.audio.play_effect("jump")
            elif key in (pygame.K_ESCAPE, pygame.K_p):
                self._pause()
            return

        if self.state == "paused":
            if key == pygame.K_p:
                self._resume()
            elif key == pygame.K_ESCAPE:
                self._return_menu()
            elif key == pygame.K_s:
                self._open_settings()
            return

        if self.state == "game_over":
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_r):
                self._start_run()
            elif key == pygame.K_ESCAPE:
                self._return_menu()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE and not self.fullscreen:
                self.windowed_size = [max(960, event.w), max(540, event.h)]
                self.screen = self._create_display(False)
            elif event.type == pygame.WINDOWFOCUSLOST:
                if self.state == "playing" and self.storage.settings.get("focus_mode", True):
                    self._pause()
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event.key)
            elif event.type == pygame.MOUSEMOTION:
                self.hovered_action = self._button_action_at(self._logical_mouse_pos(event.pos))
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                action = self._button_action_at(self._logical_mouse_pos(event.pos))
                self._activate_action(action)

    def run(self) -> int:
        while self.running:
            dt = min(0.05, self.clock.tick(FPS) / 1000.0)
            self._handle_events()

            if self.state == "playing":
                self._update_playing(dt)
            elif self.state == "paused":
                self._update_toasts(dt)
            elif self.state == "settings" and self.settings_return_state in {"paused", "game_over"}:
                self._update_toasts(dt)
            else:
                self._update_idle_scene(dt)

            paused_music = self.state in {"paused", "game_over"} or (
                self.state == "settings" and self.settings_return_state == "paused"
            )
            self.audio.update(dt, paused=paused_music, challenge_active=self.challenge_active and self.state == "playing")
            self._draw()

        self.storage.persist_all()
        pygame.quit()
        return 0
