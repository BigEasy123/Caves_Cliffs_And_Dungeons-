import random

import pygame

from game.anim import DirectionalStepAnimator
from game.assets_manifest import PATHS
from game.constants import (
    COLOR_BG,
    COLOR_FLOOR,
    COLOR_PICKUP,
    COLOR_PLAYER,
    COLOR_ENEMY,
    COLOR_STAIRS_DOWN,
    COLOR_STAIRS_UP,
    COLOR_TEXT,
    COLOR_WALL,
    TILE_DUNGEON_EXIT,
    GRID_HEIGHT,
    GRID_WIDTH,
    TILE_FLOOR,
    TILE_STAIRS_DOWN,
    TILE_STAIRS_UP,
    TILE_WALL,
    TILE_SIZE,
)
from game.assets import load_sprite_variants, pick_variant, try_load_sprite
from game.enemies import enemy_table_for_dungeon, spawn_enemy
from game.entities.enemy import Enemy
from game.entities.pickup import Pickup
from game.entities.player import GridPlayer
from game.items import ITEMS, get_item
from game.scenes.base import Scene
from game.state import STATE
from game.story.missions import MISSIONS
from game.story.quest_manager import is_mission_complete, mission_objective_text
from game.world.dungeon_gen import generate_dungeon
from game.world.dungeon_run import DungeonRun
from game.save import save_slot


class DungeonScene(Scene):
    def __init__(self, app, run: DungeonRun, *, return_to: str = "outskirts") -> None:
        super().__init__(app)
        self.font = pygame.font.SysFont(None, 22)
        self.run = run
        self.return_to = return_to
        self.app.audio.play_music(PATHS.music / "dungeon.ogg", volume=0.45)
        self.rng = random.Random(self.run.seed_for_floor(self.run.floor))

        self.grid: list[list[int]] = []
        self.player: GridPlayer
        self.enemies: list[Enemy] = []
        self.pickups: list[Pickup] = []

        self.grid = self._generate_floor()
        self.player = self._spawn_player()
        self._populate_floor()

        self.player_idle = {
            "down": try_load_sprite(PATHS.sprites / "player_down.png", size=(TILE_SIZE, TILE_SIZE)),
            "up": try_load_sprite(PATHS.sprites / "player_up.png", size=(TILE_SIZE, TILE_SIZE)),
            "left": try_load_sprite(PATHS.sprites / "player_left.png", size=(TILE_SIZE, TILE_SIZE)),
            "right": try_load_sprite(PATHS.sprites / "player_right.png", size=(TILE_SIZE, TILE_SIZE)),
        }
        self.player_walk = {
            "down": [try_load_sprite(PATHS.sprites / f"player_walk{i}_down.png", size=(TILE_SIZE, TILE_SIZE)) for i in range(3)],
            "up": [try_load_sprite(PATHS.sprites / f"player_walk{i}_up.png", size=(TILE_SIZE, TILE_SIZE)) for i in range(3)],
            "left": [try_load_sprite(PATHS.sprites / f"player_walk{i}_left.png", size=(TILE_SIZE, TILE_SIZE)) for i in range(3)],
            "right": [try_load_sprite(PATHS.sprites / f"player_walk{i}_right.png", size=(TILE_SIZE, TILE_SIZE)) for i in range(3)],
        }

        # Back-compat (older single-file sprite + generic walk frames)
        self.player_sprite = try_load_sprite(PATHS.sprites / "player.png", size=(TILE_SIZE, TILE_SIZE))
        if not any(self.player_idle.values()):
            self.player_idle["down"] = self.player_sprite

        try:
            from game.direction import Direction

            frames_by_dir = {
                Direction.DOWN: [f for f in self.player_walk["down"] if f is not None],
                Direction.UP: [f for f in self.player_walk["up"] if f is not None],
                Direction.LEFT: [f for f in self.player_walk["left"] if f is not None],
                Direction.RIGHT: [f for f in self.player_walk["right"] if f is not None],
            }
            if not any(frames_by_dir.values()):
                legacy_walk = [
                    try_load_sprite(PATHS.sprites / "player_walk0.png", size=(TILE_SIZE, TILE_SIZE)),
                    try_load_sprite(PATHS.sprites / "player_walk1.png", size=(TILE_SIZE, TILE_SIZE)),
                    try_load_sprite(PATHS.sprites / "player_walk2.png", size=(TILE_SIZE, TILE_SIZE)),
                ]
                legacy_frames = [f for f in legacy_walk if f is not None]
                frames_by_dir = {
                    Direction.DOWN: legacy_frames,
                    Direction.UP: legacy_frames,
                    Direction.LEFT: legacy_frames,
                    Direction.RIGHT: legacy_frames,
                }
            self.player_anim = DirectionalStepAnimator(frames_by_dir)
        except Exception:
            self.player_anim = None
        self.enemy_sprite = try_load_sprite("assets/sprites/enemy.png", size=(TILE_SIZE, TILE_SIZE))
        self.floor_stone = load_sprite_variants(PATHS.tiles, prefix="floor_stone", size=(TILE_SIZE, TILE_SIZE)) or load_sprite_variants(
            PATHS.tiles, prefix="floor", size=(TILE_SIZE, TILE_SIZE)
        )
        self.floor_grass = load_sprite_variants(PATHS.tiles, prefix="floor_grass", size=(TILE_SIZE, TILE_SIZE)) or self.floor_stone
        self.floor_gravel = load_sprite_variants(PATHS.tiles, prefix="floor_gravel", size=(TILE_SIZE, TILE_SIZE)) or self.floor_stone
        self.floor_mud = load_sprite_variants(PATHS.tiles, prefix="floor_mud", size=(TILE_SIZE, TILE_SIZE)) or self.floor_gravel
        self.wall_rock = load_sprite_variants(PATHS.tiles, prefix="wall_rock", size=(TILE_SIZE, TILE_SIZE)) or load_sprite_variants(
            PATHS.tiles, prefix="wall", size=(TILE_SIZE, TILE_SIZE)
        )
        self.wall_stone = load_sprite_variants(PATHS.tiles, prefix="wall_stone", size=(TILE_SIZE, TILE_SIZE)) or self.wall_rock
        self.special_tiles = {
            TILE_STAIRS_DOWN: try_load_sprite(PATHS.tiles / "stairs_down.png", size=(TILE_SIZE, TILE_SIZE)),
            TILE_STAIRS_UP: try_load_sprite(PATHS.tiles / "stairs_up.png", size=(TILE_SIZE, TILE_SIZE)),
            TILE_DUNGEON_EXIT: try_load_sprite(PATHS.tiles / "exit.png", size=(TILE_SIZE, TILE_SIZE)),
        }
        self.visual_seed = self.run.seed_for_floor(self.run.floor) % 100000
        self.message = ""
        self.inventory_open = False
        self.inventory_index = 0
        self.pending_scene: Scene | None = None
        self.turn = 0
        self.minimap_open = True
        self.seen = [[False for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.kills = 0
        self.gold_gained = 0
        self.items_gained: dict[str, int] = {}
        self.skills_open = False
        self.skill_index = 0
        self._reveal()

    def _generate_floor(self) -> list[list[int]]:
        self.rng = random.Random(self.run.seed_for_floor(self.run.floor))
        self.visual_seed = self.run.seed_for_floor(self.run.floor) % 100000
        grid = generate_dungeon(
            GRID_WIDTH,
            GRID_HEIGHT,
            seed=self.run.seed_for_floor(self.run.floor),
            place_stairs_up=self.run.floor > 1,
            place_stairs_down=self.run.floor < self.run.max_floor,
        )
        if self.run.floor >= self.run.max_floor:
            pos = _find_tile(grid, TILE_FLOOR)
            if pos is not None:
                x, y = pos
                grid[y][x] = TILE_DUNGEON_EXIT
        return grid

    def _spawn_player(self) -> GridPlayer:
        if self.run.floor > 1:
            pos = _find_tile(self.grid, TILE_STAIRS_UP)
            if pos is not None:
                return GridPlayer(*pos)
        pos = _find_tile(self.grid, TILE_FLOOR)
        if pos is not None:
            return GridPlayer(*pos)
        return GridPlayer.spawn_on_floor(self.grid)

    def _populate_floor(self) -> None:
        self.enemies.clear()
        self.pickups.clear()

        # Enemies and pickups are seeded per floor to stay stable until regen.
        floor_cells = _all_floor_like(self.grid)
        self.rng.shuffle(floor_cells)

        enemy_count = max(1, 2 + self.run.floor // 2)
        difficulty_floor = self.run.floor + max(0, STATE.combat_level - 1) // 3
        table = enemy_table_for_dungeon(self.run.dungeon_id, difficulty_floor)
        for _ in range(enemy_count):
            if not floor_cells:
                break
            x, y = floor_cells.pop()
            if (x, y) == (self.player.x, self.player.y):
                continue
            if self.grid[y][x] in (TILE_STAIRS_DOWN, TILE_STAIRS_UP):
                continue
            enemy_id = self.rng.choice(table)
            self.enemies.append(spawn_enemy(enemy_id, x=x, y=y, floor=self.run.floor, combat_level=STATE.combat_level, rng=self.rng))

        # A couple simple pickups
        for _ in range(2):
            if not floor_cells:
                break
            x, y = floor_cells.pop()
            if self.grid[y][x] in (TILE_STAIRS_DOWN, TILE_STAIRS_UP):
                continue
            self.pickups.append(Pickup(item_id="potion_small", x=x, y=y))

        # Rare-ish relic shard
        if self.rng.random() < 0.35 and floor_cells:
            x, y = floor_cells.pop()
            self.pickups.append(Pickup(item_id="relic_shard", x=x, y=y))

        # Mission items (rescue/collect style): ensure at least a chance to find them during a run.
        mission_id = STATE.active_mission
        mission = MISSIONS.get(mission_id) if mission_id else None
        if mission is not None:
            for obj in mission.objectives:
                if str(obj.get("type", "")) != "collect_item":
                    continue
                item_id = str(obj.get("item_id", ""))
                if not item_id or item_id == "relic_shard":
                    continue
                if STATE.item_count(item_id) > 0:
                    continue
                if not floor_cells:
                    break
                if self.rng.random() < 0.60:
                    x, y = floor_cells.pop()
                    self.pickups.append(Pickup(item_id=item_id, x=x, y=y))

    def handle_event(self, event: pygame.event.Event) -> Scene | None:
        if self.pending_scene is not None:
            return self.pending_scene

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_i:
                self.inventory_open = not self.inventory_open
                self.message = ""
                self.app.audio.play_sfx(
                    PATHS.sfx / ("ui_open.wav" if self.inventory_open else "ui_close.wav"),
                    volume=0.35,
                )
                return None

            if event.key == pygame.K_m:
                self.minimap_open = not self.minimap_open
                self.app.audio.play_sfx(
                    PATHS.sfx / ("ui_open.wav" if self.minimap_open else "ui_close.wav"),
                    volume=0.30,
                )
                return None

            if event.key == pygame.K_k:
                self.skills_open = not self.skills_open
                self.message = ""
                self.app.audio.play_sfx(
                    PATHS.sfx / ("ui_open.wav" if self.skills_open else "ui_close.wav"),
                    volume=0.35,
                )
                return None

            if event.key == pygame.K_ESCAPE:
                if self.inventory_open:
                    self.inventory_open = False
                    self.app.audio.play_sfx(PATHS.sfx / "ui_close.wav", volume=0.35)
                    return None
                if self.skills_open:
                    self.skills_open = False
                    self.app.audio.play_sfx(PATHS.sfx / "ui_close.wav", volume=0.35)
                    return None
                self.message = "You can't leave mid-run. Finish the mission or reach the bottom."
                self.app.audio.play_sfx(PATHS.sfx / "error.wav", volume=0.40)
                return None

            if self.inventory_open:
                return self._handle_inventory_keys(event)
            if self.skills_open:
                return self._handle_skill_keys(event)

            dx, dy = 0, 0
            if event.key in (pygame.K_LEFT, pygame.K_a):
                dx = -1
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                dx = 1
            elif event.key in (pygame.K_UP, pygame.K_w):
                dy = -1
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                dy = 1
            elif event.key == pygame.K_r:
                self.grid = self._generate_floor()
                self.player = self._spawn_player()
                self._populate_floor()
                self.seen = [[False for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
                self._reveal()
                return None
            elif event.key == pygame.K_e:
                next_scene = self._try_use_stairs()
                if next_scene is None:
                    self._enemy_turn()
                    self._reveal()
                return next_scene

            if dx != 0 or dy != 0:
                acted = self._try_player_step(dx, dy)
                if acted:
                    self._enemy_turn()
                    self._reveal()

        return None

    def update(self, dt: float) -> Scene | None:
        if self.pending_scene is not None:
            return self.pending_scene
        return None

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)

        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                if not self.seen[y][x]:
                    pygame.draw.rect(
                        surface,
                        (8, 9, 12),
                        pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE),
                    )
                    continue
                if cell == TILE_FLOOR:
                    if self.run.dungeon_id == "jungle_cavern":
                        variants = self.floor_grass if (x + y + self.visual_seed) % 5 else self.floor_mud
                    else:
                        variants = self.floor_stone if (x + y + self.visual_seed) % 7 else self.floor_gravel
                    sprite = pick_variant(variants, x=x, y=y, seed=self.visual_seed)
                    if sprite is not None:
                        surface.blit(sprite, (x * TILE_SIZE, y * TILE_SIZE))
                        continue
                if cell == TILE_WALL:
                    wall_variants = self.wall_rock if self.run.dungeon_id == "jungle_cavern" else self.wall_stone
                    sprite = pick_variant(wall_variants, x=x, y=y, seed=self.visual_seed)
                    if sprite is not None:
                        surface.blit(sprite, (x * TILE_SIZE, y * TILE_SIZE))
                        continue
                sprite = self.special_tiles.get(cell)
                if sprite is not None:
                    surface.blit(sprite, (x * TILE_SIZE, y * TILE_SIZE))
                    continue
                if cell == TILE_WALL:
                    color = COLOR_WALL
                elif cell == TILE_STAIRS_DOWN:
                    color = COLOR_STAIRS_DOWN
                elif cell == TILE_STAIRS_UP:
                    color = COLOR_STAIRS_UP
                else:
                    color = COLOR_FLOOR
                pygame.draw.rect(
                    surface,
                    color,
                    pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE),
                )

        for pickup in self.pickups:
            if not self.seen[pickup.y][pickup.x]:
                continue
            pygame.draw.rect(
                surface,
                COLOR_PICKUP,
                pygame.Rect(pickup.x * TILE_SIZE + 8, pickup.y * TILE_SIZE + 8, TILE_SIZE - 16, TILE_SIZE - 16),
            )

        for enemy in self.enemies:
            if not enemy.is_alive():
                continue
            if not self.seen[enemy.y][enemy.x]:
                continue
            ex = enemy.x * TILE_SIZE
            ey = enemy.y * TILE_SIZE
            if self.enemy_sprite is not None:
                surface.blit(self.enemy_sprite, (ex, ey))
            else:
                pygame.draw.rect(surface, COLOR_ENEMY, pygame.Rect(ex, ey, TILE_SIZE, TILE_SIZE))
            if enemy.aggro_turns > 0:
                pygame.draw.circle(surface, (255, 255, 255), (ex + TILE_SIZE // 2, ey + 6), 4)

        px = self.player.x * TILE_SIZE
        py = self.player.y * TILE_SIZE
        fallback_by_dir = None
        if self.player_anim is not None:
            from game.direction import Direction

            fallback_by_dir = {
                Direction.DOWN: self.player_idle.get("down") or self.player_sprite,
                Direction.UP: self.player_idle.get("up") or self.player_sprite,
                Direction.LEFT: self.player_idle.get("left") or self.player_sprite,
                Direction.RIGHT: self.player_idle.get("right") or self.player_sprite,
            }
        sprite = self.player_anim.current(fallback_by_dir) if self.player_anim is not None else self.player_sprite
        if sprite is not None:
            surface.blit(sprite, (px, py))
        else:
            pygame.draw.rect(surface, COLOR_PLAYER, pygame.Rect(px, py, TILE_SIZE, TILE_SIZE))

        hud = self.font.render(
            f"{self.run.dungeon_name} - Floor {self.run.floor}/{self.run.max_floor} | "
            f"HP {STATE.hp}/{STATE.max_hp_total()}  Gold {STATE.gold} | "
            "Move: WASD/arrows  E: stairs  I: inventory  M: map  R: regen",
            True,
            COLOR_TEXT,
        )
        surface.blit(hud, (10, 8))

        mission_line = self._mission_hud_text()
        if mission_line:
            mission = self.font.render(mission_line, True, (200, 200, 210))
            surface.blit(mission, (10, 32))

        if self.message:
            msg = self.font.render(self.message, True, COLOR_TEXT)
            surface.blit(msg, (10, 56))

        if self.inventory_open:
            self._draw_inventory(surface)
        if self.minimap_open:
            self._draw_minimap(surface)
        if self.skills_open:
            self._draw_skills(surface)

    def _try_use_stairs(self) -> Scene | None:
        tile = self.grid[self.player.y][self.player.x]

        if tile == TILE_DUNGEON_EXIT:
            self.message = "You escape the dungeon!"
            save_slot(1)
            self.app.toast("Autosaved (slot 1)")
            self.app.audio.play_sfx(PATHS.sfx / "door.wav", volume=0.45)
            return self._summary_scene(reason="Reached the bottom")

        if tile == TILE_STAIRS_DOWN:
            if self.run.floor >= self.run.max_floor:
                self.message = "This is as deep as it goes (for now)."
                self.app.audio.play_sfx(PATHS.sfx / "error.wav", volume=0.40)
                return None
            self.run.floor += 1
            self.grid = self._generate_floor()
            pos = _find_tile(self.grid, TILE_STAIRS_UP)
            self.player = GridPlayer(*(pos if pos is not None else (1, 1)))
            self._populate_floor()
            self.seen = [[False for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
            self._reveal()
            if self._check_missions_progress():
                return self.pending_scene
            self.message = ""
            return None

        if tile == TILE_STAIRS_UP:
            if self.run.floor <= 1:
                self.message = "No turning back now."
                self.app.audio.play_sfx(PATHS.sfx / "error.wav", volume=0.40)
                return None
            self.run.floor -= 1
            self.grid = self._generate_floor()
            pos = _find_tile(self.grid, TILE_STAIRS_DOWN) or _find_tile(self.grid, TILE_FLOOR)
            self.player = GridPlayer(*(pos if pos is not None else (1, 1)))
            self._populate_floor()
            self.seen = [[False for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
            self._reveal()
            self.message = ""
            return None

        self.message = "No stairs here."
        self.app.audio.play_sfx(PATHS.sfx / "error.wav", volume=0.40)
        return None

    def _try_player_step(self, dx: int, dy: int) -> bool:
        nx = self.player.x + dx
        ny = self.player.y + dy
        if ny < 0 or ny >= len(self.grid) or nx < 0 or nx >= len(self.grid[0]):
            return False
        if self.grid[ny][nx] == TILE_WALL:
            return False

        enemy = self._enemy_at(nx, ny)
        if enemy is not None and enemy.is_alive():
            self._player_attack(enemy)
            return True

        prev = (self.player.x, self.player.y)
        self.player.try_move(dx, dy, self.grid, walls={TILE_WALL})
        if (self.player.x, self.player.y) != prev:
            if self.player_anim is not None:
                self.player_anim.on_step(dx, dy)
            self.app.audio.play_sfx(PATHS.sfx / "step.wav", volume=0.18)
        self._pickup_if_present()
        self.message = ""
        return True

    def _enemy_turn(self) -> None:
        if STATE.hp <= 0:
            return

        if STATE.poison_turns > 0:
            STATE.hp = max(0, STATE.hp - STATE.poison_damage)
            STATE.poison_turns -= 1
            if STATE.hp <= 0:
                self.message = "Poison drops you... (Returned to Home Base)"
                self._handle_player_death()
                return

        self.turn += 1
        for enemy in self.enemies:
            if not enemy.is_alive():
                continue

            if enemy.stunned_turns > 0:
                enemy.stunned_turns -= 1
                continue

            self._update_aggro(enemy)
            if enemy.aggro_turns <= 0:
                # Idle wander sometimes
                if enemy.behavior.endswith("patrol") and enemy.should_move(self.turn):
                    self._enemy_patrol(enemy)
                elif enemy.should_move(self.turn) and self.rng.random() < 0.35:
                    self._enemy_wander(enemy)
                continue

            if enemy.behavior == "ranged":
                if self._enemy_try_ranged(enemy):
                    continue

            if abs(enemy.x - self.player.x) + abs(enemy.y - self.player.y) == 1 and enemy.should_attack(self.turn):
                damage = max(1, enemy.attack - STATE.defense())
                if STATE.guard_turns > 0:
                    damage = max(1, damage // 2)
                    STATE.guard_turns = max(0, STATE.guard_turns - 1)
                STATE.hp = max(0, STATE.hp - damage)
                self.message = f"{enemy.name} hits you for {damage}."
                self.app.audio.play_sfx(PATHS.sfx / "hit.wav", volume=0.5)
                if enemy.behavior == "poison_melee" and enemy.poison_turns > 0:
                    STATE.poison_turns = max(STATE.poison_turns, enemy.poison_turns)
                    STATE.poison_damage = max(STATE.poison_damage, enemy.poison_damage)
                    self.message += " You feel poison spreading."
                if STATE.hp <= 0:
                    self.message = "You collapse... (Returned to Home Base)"
                    self._handle_player_death()
                continue

            if enemy.should_move(self.turn):
                self._enemy_step_toward(enemy)

    def _enemy_step_toward(self, enemy: Enemy) -> None:
        dx = 1 if self.player.x > enemy.x else (-1 if self.player.x < enemy.x else 0)
        dy = 1 if self.player.y > enemy.y else (-1 if self.player.y < enemy.y else 0)

        candidates = []
        if dx != 0:
            candidates.append((enemy.x + dx, enemy.y))
        if dy != 0:
            candidates.append((enemy.x, enemy.y + dy))
        self.rng.shuffle(candidates)

        for nx, ny in candidates:
            if self.grid[ny][nx] == TILE_WALL:
                continue
            if (nx, ny) == (self.player.x, self.player.y):
                continue
            if self._enemy_at(nx, ny) is not None:
                continue
            enemy.x, enemy.y = nx, ny
            break

    def _enemy_wander(self, enemy: Enemy) -> None:
        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        self.rng.shuffle(dirs)
        for dx, dy in dirs:
            nx, ny = enemy.x + dx, enemy.y + dy
            if self.grid[ny][nx] == TILE_WALL:
                continue
            if (nx, ny) == (self.player.x, self.player.y):
                continue
            if self._enemy_at(nx, ny) is not None:
                continue
            enemy.x, enemy.y = nx, ny
            break

    def _enemy_patrol(self, enemy: Enemy) -> None:
        nx = enemy.x + enemy.patrol_dx
        ny = enemy.y
        if self.grid[ny][nx] == TILE_WALL or self._enemy_at(nx, ny) is not None or (nx, ny) == (self.player.x, self.player.y):
            enemy.patrol_dx *= -1
            return
        enemy.x = nx

    def _player_attack(self, enemy: Enemy) -> None:
        damage = max(1, STATE.attack() - getattr(enemy, "defense", 0))
        enemy.hp = max(0, enemy.hp - damage)
        if enemy.hp <= 0:
            STATE.record_kill(enemy.enemy_id)
            levels = STATE.add_combat_xp(6 + self.run.floor)
            if levels:
                self.app.toast(f"Combat level up! Lv {STATE.combat_level}")
                self.app.audio.play_sfx(PATHS.sfx / "confirm.wav", volume=0.35)
            self.message = f"You defeat {enemy.name}!"
            self.app.audio.play_sfx(PATHS.sfx / "hit.wav", volume=0.55)
            gained = 5 + self.run.floor
            STATE.gold += gained
            self.gold_gained += gained
            self.kills += 1
            if self.rng.random() < 0.25:
                STATE.add_item("potion_small", 1)
                self.items_gained["potion_small"] = self.items_gained.get("potion_small", 0) + 1
                self.message += " Found a Small Potion."
            self._check_missions_progress()
        else:
            self.message = f"You hit {enemy.name} for {damage}."
            self.app.audio.play_sfx(PATHS.sfx / "hit.wav", volume=0.55)

    def _pickup_if_present(self) -> None:
        for idx, pickup in enumerate(list(self.pickups)):
            if pickup.x == self.player.x and pickup.y == self.player.y:
                STATE.add_item(pickup.item_id, pickup.amount)
                self.items_gained[pickup.item_id] = self.items_gained.get(pickup.item_id, 0) + pickup.amount
                item = get_item(pickup.item_id)
                self.message = f"Picked up {item.name}."
                self.app.audio.play_sfx(PATHS.sfx / "pickup.wav", volume=0.45)
                self.pickups.pop(idx)
                if pickup.item_id == "relic_shard":
                    self._check_missions_progress()
                break

    def _enemy_at(self, x: int, y: int) -> Enemy | None:
        for enemy in self.enemies:
            if enemy.is_alive() and enemy.x == x and enemy.y == y:
                return enemy
        return None

    def _update_aggro(self, enemy: Enemy) -> None:
        dist = abs(enemy.x - self.player.x) + abs(enemy.y - self.player.y)
        if dist <= enemy.aggro_range and self._has_simple_los(enemy.x, enemy.y, self.player.x, self.player.y):
            enemy.aggro_turns = 6
        else:
            enemy.aggro_turns = max(0, enemy.aggro_turns - 1)

    def _has_simple_los(self, x1: int, y1: int, x2: int, y2: int) -> bool:
        # Simple LOS: clear if same row/col with no walls between, else allow within 2 tiles.
        if x1 == x2:
            step = 1 if y2 > y1 else -1
            for y in range(y1 + step, y2, step):
                if self.grid[y][x1] == TILE_WALL:
                    return False
            return True
        if y1 == y2:
            step = 1 if x2 > x1 else -1
            for x in range(x1 + step, x2, step):
                if self.grid[y1][x] == TILE_WALL:
                    return False
            return True
        return abs(x1 - x2) + abs(y1 - y2) <= 2

    def _handle_player_death(self) -> None:
        # Reset player and send them home immediately.
        STATE.hp = STATE.max_hp_total()
        from game.scenes.home import HomeBaseScene

        self.pending_scene = HomeBaseScene(self.app)

    def _handle_skill_keys(self, event: pygame.event.Event) -> Scene | None:
        if event.key in (pygame.K_ESCAPE, pygame.K_k):
            self.skills_open = False
            return None
        skills = self._skills()
        if not skills:
            return None
        if event.key in (pygame.K_UP, pygame.K_w):
            self.skill_index = (self.skill_index - 1) % len(skills)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.skill_index = (self.skill_index + 1) % len(skills)
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_e):
            self._use_skill(skills[self.skill_index])
            self.skills_open = False
            self._enemy_turn()
            self._reveal()
        return None

    def _skills(self) -> list[str]:
        return ["whip", "throw_rock", "guard"]

    def _use_skill(self, skill_id: str) -> None:
        if skill_id == "guard":
            STATE.guard_turns = 1
            self.message = "You brace yourself."
            self.app.audio.play_sfx(PATHS.sfx / "confirm.wav", volume=0.35)
            return
        if skill_id == "throw_rock":
            target = self._nearest_enemy_in_range(4)
            if target is None:
                self.message = "No target in range."
                return
            damage = max(1, STATE.attack() - 1)
            target.hp = max(0, target.hp - damage)
            self.message = f"You throw a rock at {target.name} ({damage})."
            self.app.audio.play_sfx(PATHS.sfx / "shoot.wav", volume=0.4)
            if target.hp <= 0:
                STATE.record_kill(target.enemy_id)
                levels = STATE.add_combat_xp(5 + self.run.floor)
                if levels:
                    self.app.toast(f"Combat level up! Lv {STATE.combat_level}")
                    self.app.audio.play_sfx(PATHS.sfx / "confirm.wav", volume=0.35)
                self.kills += 1
                gained = 4 + self.run.floor
                STATE.gold += gained
                self.gold_gained += gained
                self.message += " Defeated!"
                self._check_missions_progress()
            return
        if skill_id == "whip":
            target = self._enemy_at_adjacent()
            if target is None:
                self.message = "No adjacent target."
                return
            damage = max(1, STATE.attack() + 2 - target.defense)
            target.hp = max(0, target.hp - damage)
            if self.rng.random() < 0.25:
                target.stunned_turns = max(target.stunned_turns, 1)
            self.message = f"You crack the whip at {target.name} ({damage})."
            self.app.audio.play_sfx(PATHS.sfx / "hit.wav", volume=0.55)
            if target.hp <= 0:
                STATE.record_kill(target.enemy_id)
                levels = STATE.add_combat_xp(6 + self.run.floor)
                if levels:
                    self.app.toast(f"Combat level up! Lv {STATE.combat_level}")
                    self.app.audio.play_sfx(PATHS.sfx / "confirm.wav", volume=0.35)
                self.kills += 1
                gained = 5 + self.run.floor
                STATE.gold += gained
                self.gold_gained += gained
                self.message += " Defeated!"
                self._check_missions_progress()
            return

    def _enemy_at_adjacent(self) -> Enemy | None:
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            e = self._enemy_at(self.player.x + dx, self.player.y + dy)
            if e is not None:
                return e
        return None

    def _nearest_enemy_in_range(self, r: int) -> Enemy | None:
        best = None
        best_d = 999
        for e in self.enemies:
            if not e.is_alive():
                continue
            if not self.seen[e.y][e.x]:
                continue
            d = abs(e.x - self.player.x) + abs(e.y - self.player.y)
            if d <= r and d < best_d and self._has_simple_los(self.player.x, self.player.y, e.x, e.y):
                best = e
                best_d = d
        return best

    def _enemy_try_ranged(self, enemy: Enemy) -> bool:
        if not enemy.should_attack(self.turn):
            return False
        d = abs(enemy.x - self.player.x) + abs(enemy.y - self.player.y)
        if enemy.ranged_range <= 0 or d > enemy.ranged_range:
            return False
        if not self._has_simple_los(enemy.x, enemy.y, self.player.x, self.player.y):
            return False
        damage = max(1, enemy.attack - STATE.defense())
        if STATE.guard_turns > 0:
            damage = max(1, damage // 2)
            STATE.guard_turns = max(0, STATE.guard_turns - 1)
        STATE.hp = max(0, STATE.hp - damage)
        self.message = f"{enemy.name} shoots you for {damage}."
        self.app.audio.play_sfx(PATHS.sfx / "shoot.wav", volume=0.45)
        if STATE.hp <= 0:
            self.message = "You collapse... (Returned to Home Base)"
            self._handle_player_death()
        return True

    def _draw_skills(self, surface: pygame.Surface) -> None:
        width, height = surface.get_size()
        rect = pygame.Rect(60, 90, width - 120, height - 180)
        overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        surface.blit(overlay, rect.topleft)
        pygame.draw.rect(surface, (255, 255, 255), rect, 2)
        title = self.font.render("Skills (Up/Down, Enter/E, K/Esc)", True, COLOR_TEXT)
        surface.blit(title, (rect.left + 12, rect.top + 12))
        skills = self._skills()
        y = rect.top + 46
        labels = {
            "whip": "Whip (melee, high damage, may stun)",
            "throw_rock": "Throw Rock (ranged, nearest target)",
            "guard": "Guard (halve next hit)",
        }
        for idx, skill_id in enumerate(skills):
            prefix = "> " if idx == self.skill_index else "  "
            line = self.font.render(prefix + labels.get(skill_id, skill_id), True, COLOR_TEXT)
            surface.blit(line, (rect.left + 12, y))
            y += 26

    def _handle_inventory_keys(self, event: pygame.event.Event) -> Scene | None:
        if event.key in (pygame.K_ESCAPE, pygame.K_i):
            self.inventory_open = False
            return None

        items = self._inventory_items()
        if not items:
            return None

        if event.key in (pygame.K_UP, pygame.K_w):
            self.inventory_index = (self.inventory_index - 1) % len(items)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.inventory_index = (self.inventory_index + 1) % len(items)
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_e):
            item_id = items[self.inventory_index]
            self._use_item(item_id)
            self._enemy_turn()
        return None

    def _inventory_items(self) -> list[str]:
        return [item_id for item_id in STATE.inventory.keys() if item_id in ITEMS]

    def _use_item(self, item_id: str) -> None:
        item = get_item(item_id)
        if not item.usable_in_dungeon:
            self.message = f"{item.name} can't be used here (yet)."
            return
        if item.effects and "heal_hp" in item.effects:
            if STATE.hp >= STATE.max_hp_total():
                self.message = "HP already full."
                self.app.audio.play_sfx(PATHS.sfx / "error.wav", volume=0.40)
                return
            if not STATE.remove_item(item_id, 1):
                return
            heal = int(item.effects["heal_hp"])
            STATE.hp = min(STATE.max_hp_total(), STATE.hp + heal)
            self.message = f"Used {item.name} (+{heal} HP)."
            self.app.audio.play_sfx(PATHS.sfx / "heal.wav", volume=0.35)
            return
        if item.effects and "cure_poison" in item.effects:
            if STATE.poison_turns <= 0:
                self.message = "No poison to cure."
                self.app.audio.play_sfx(PATHS.sfx / "error.wav", volume=0.40)
                return
            if not STATE.remove_item(item_id, 1):
                return
            STATE.poison_turns = 0
            STATE.poison_damage = 0
            self.message = f"Used {item.name} (poison cured)."
            self.app.audio.play_sfx(PATHS.sfx / "confirm.wav", volume=0.35)
            return
        self.message = f"Used {item.name}."

    def _check_missions_progress(self) -> bool:
        mission_id = STATE.active_mission
        if not mission_id:
            return False
        if not is_mission_complete(STATE, mission_id, dungeon_id=self.run.dungeon_id, floor=self.run.floor):
            return False
        STATE.completed_missions.add(mission_id)
        STATE.active_mission = None
        STATE.mission_kill_baseline = {}
        self.message = f"Mission complete: {MISSIONS.get(mission_id).name if mission_id in MISSIONS else mission_id}! Return to the Guild."
        self.app.audio.play_sfx(PATHS.sfx / "mission.wav", volume=0.45)
        self.pending_scene = self._summary_scene(reason="Mission complete")
        return True

    def _mission_hud_text(self) -> str:
        mission_id = STATE.active_mission
        if not mission_id:
            return ""
        mission = MISSIONS.get(mission_id)
        if mission is None:
            return f"Mission: {mission_id}"
        return f"Mission: {mission.name} — {mission_objective_text(mission_id)}"

    def _return_scene(self) -> Scene:
        if self.return_to == "outskirts":
            from game.scenes.outskirts import OutskirtsScene

            return OutskirtsScene(self.app, spawn=(GRID_WIDTH - 4, GRID_HEIGHT // 2))
        from game.scenes.town import TownScene

        return TownScene(self.app, spawn=(GRID_WIDTH - 4, GRID_HEIGHT // 2))

    def _summary_scene(self, *, reason: str) -> Scene:
        from game.scenes.run_summary import RunSummaryScene

        next_scene = self._return_scene()
        lines = [
            f"Reason: {reason}",
            f"Turns: {self.turn}",
            f"Enemies defeated: {self.kills}",
            f"Gold gained: {self.gold_gained}",
        ]
        if self.items_gained:
            lines.append("Items gained:")
            for item_id, count in sorted(self.items_gained.items()):
                lines.append(f"- {item_id} x{count}")
        return RunSummaryScene(self.app, title="Dungeon Run Summary", lines=lines, next_scene=next_scene)

    def _reveal(self) -> None:
        r = 3
        for yy in range(max(0, self.player.y - r), min(GRID_HEIGHT, self.player.y + r + 1)):
            for xx in range(max(0, self.player.x - r), min(GRID_WIDTH, self.player.x + r + 1)):
                if abs(xx - self.player.x) + abs(yy - self.player.y) <= r:
                    self.seen[yy][xx] = True

    def _draw_minimap(self, surface: pygame.Surface) -> None:
        scale = 4
        w = GRID_WIDTH * scale
        h = GRID_HEIGHT * scale
        ox = surface.get_width() - w - 10
        oy = 45
        bg = pygame.Surface((w + 4, h + 4), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 160))
        surface.blit(bg, (ox - 2, oy - 2))
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if not self.seen[y][x]:
                    continue
                cell = self.grid[y][x]
                if cell == TILE_WALL:
                    color = (90, 95, 110)
                elif cell == TILE_STAIRS_DOWN:
                    color = (120, 160, 230)
                elif cell == TILE_STAIRS_UP:
                    color = (170, 230, 150)
                elif cell == TILE_DUNGEON_EXIT:
                    color = (240, 230, 120)
                else:
                    color = (45, 48, 58)
                pygame.draw.rect(surface, color, pygame.Rect(ox + x * scale, oy + y * scale, scale, scale))
        pygame.draw.rect(
            surface,
            (240, 210, 80),
            pygame.Rect(ox + self.player.x * scale, oy + self.player.y * scale, scale, scale),
        )

    def _draw_inventory(self, surface: pygame.Surface) -> None:
        width, height = surface.get_size()
        rect = pygame.Rect(40, 70, width - 80, height - 120)

        overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, rect.topleft)
        pygame.draw.rect(surface, (255, 255, 255), rect, 2)

        title = self.font.render("Inventory (Enter/E to use, I/Esc to close)", True, COLOR_TEXT)
        surface.blit(title, (rect.left + 12, rect.top + 10))

        items = self._inventory_items()
        if not items:
            empty = self.font.render("Empty", True, COLOR_TEXT)
            surface.blit(empty, (rect.left + 12, rect.top + 40))
            return

        y = rect.top + 44
        for idx, item_id in enumerate(items[:14]):
            item = get_item(item_id)
            count = STATE.item_count(item_id)
            prefix = "> " if idx == self.inventory_index else "  "
            line = self.font.render(f"{prefix}{item.name} x{count}", True, COLOR_TEXT)
            surface.blit(line, (rect.left + 12, y))
            y += 22


def _find_tile(grid: list[list[int]], tile: int) -> tuple[int, int] | None:
    for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            if cell == tile:
                return (x, y)
    return None


def _all_floor_like(grid: list[list[int]]) -> list[tuple[int, int]]:
    cells: list[tuple[int, int]] = []
    for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            if cell != TILE_WALL:
                cells.append((x, y))
    return cells
