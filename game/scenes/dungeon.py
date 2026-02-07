import random

import pygame

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
    GRID_HEIGHT,
    GRID_WIDTH,
    TILE_FLOOR,
    TILE_STAIRS_DOWN,
    TILE_STAIRS_UP,
    TILE_WALL,
    TILE_SIZE,
)
from game.assets import try_load_sprite
from game.entities.enemy import Enemy
from game.entities.pickup import Pickup
from game.entities.player import GridPlayer
from game.items import ITEMS, get_item
from game.scenes.base import Scene
from game.state import STATE
from game.world.dungeon_gen import generate_dungeon
from game.world.dungeon_run import DungeonRun


class DungeonScene(Scene):
    def __init__(self, app, run: DungeonRun) -> None:
        super().__init__(app)
        self.font = pygame.font.SysFont(None, 22)
        self.run = run
        self.app.audio.play_music(PATHS.music / "dungeon.ogg", volume=0.45)
        self.rng = random.Random(self.run.seed_for_floor(self.run.floor))

        self.grid: list[list[int]] = []
        self.player: GridPlayer
        self.enemies: list[Enemy] = []
        self.pickups: list[Pickup] = []

        self.grid = self._generate_floor()
        self.player = self._spawn_player()
        self._populate_floor()
        self.player_sprite = try_load_sprite("assets/sprites/player.png", size=(TILE_SIZE, TILE_SIZE))
        self.enemy_sprite = try_load_sprite("assets/sprites/enemy.png", size=(TILE_SIZE, TILE_SIZE))
        self.tiles = {
            TILE_FLOOR: try_load_sprite(PATHS.tiles / "floor.png", size=(TILE_SIZE, TILE_SIZE)),
            TILE_WALL: try_load_sprite(PATHS.tiles / "wall.png", size=(TILE_SIZE, TILE_SIZE)),
            TILE_STAIRS_DOWN: try_load_sprite(PATHS.tiles / "stairs_down.png", size=(TILE_SIZE, TILE_SIZE)),
            TILE_STAIRS_UP: try_load_sprite(PATHS.tiles / "stairs_up.png", size=(TILE_SIZE, TILE_SIZE)),
        }
        self.message = ""
        self.inventory_open = False
        self.inventory_index = 0

    def _generate_floor(self) -> list[list[int]]:
        self.rng = random.Random(self.run.seed_for_floor(self.run.floor))
        return generate_dungeon(
            GRID_WIDTH,
            GRID_HEIGHT,
            seed=self.run.seed_for_floor(self.run.floor),
            place_stairs_up=self.run.floor > 1,
            place_stairs_down=self.run.floor < self.run.max_floor,
        )

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
        for _ in range(enemy_count):
            if not floor_cells:
                break
            x, y = floor_cells.pop()
            if (x, y) == (self.player.x, self.player.y):
                continue
            if self.grid[y][x] in (TILE_STAIRS_DOWN, TILE_STAIRS_UP):
                continue
            self.enemies.append(
                Enemy(
                    enemy_id="raider",
                    name="Ruins Raider",
                    x=x,
                    y=y,
                    max_hp=6 + self.run.floor * 2,
                    hp=6 + self.run.floor * 2,
                    attack=2 + self.run.floor // 2,
                )
            )

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

    def handle_event(self, event: pygame.event.Event) -> Scene | None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                from game.scenes.world_map import WorldMapScene

                return WorldMapScene(self.app)

            if event.key == pygame.K_i:
                self.inventory_open = not self.inventory_open
                self.message = ""
                return None

            if self.inventory_open:
                return self._handle_inventory_keys(event)

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
                return None
            elif event.key == pygame.K_e:
                next_scene = self._try_use_stairs()
                if next_scene is None:
                    self._enemy_turn()
                return next_scene

            if dx != 0 or dy != 0:
                acted = self._try_player_step(dx, dy)
                if acted:
                    self._enemy_turn()

        return None

    def update(self, dt: float) -> Scene | None:
        return None

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)

        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                sprite = self.tiles.get(cell)
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
            pygame.draw.rect(
                surface,
                COLOR_PICKUP,
                pygame.Rect(pickup.x * TILE_SIZE + 8, pickup.y * TILE_SIZE + 8, TILE_SIZE - 16, TILE_SIZE - 16),
            )

        for enemy in self.enemies:
            if not enemy.is_alive():
                continue
            ex = enemy.x * TILE_SIZE
            ey = enemy.y * TILE_SIZE
            if self.enemy_sprite is not None:
                surface.blit(self.enemy_sprite, (ex, ey))
            else:
                pygame.draw.rect(surface, COLOR_ENEMY, pygame.Rect(ex, ey, TILE_SIZE, TILE_SIZE))

        px = self.player.x * TILE_SIZE
        py = self.player.y * TILE_SIZE
        if self.player_sprite is not None:
            surface.blit(self.player_sprite, (px, py))
        else:
            pygame.draw.rect(surface, COLOR_PLAYER, pygame.Rect(px, py, TILE_SIZE, TILE_SIZE))

        hud = self.font.render(
            f"{self.run.dungeon_name} - Floor {self.run.floor}/{self.run.max_floor} | "
            f"HP {STATE.hp}/{STATE.max_hp}  Gold {STATE.gold} | "
            "Move: WASD/arrows  E: stairs  I: inventory  R: regen  Esc: map",
            True,
            COLOR_TEXT,
        )
        surface.blit(hud, (10, 8))
        if self.message:
            msg = self.font.render(self.message, True, COLOR_TEXT)
            surface.blit(msg, (10, 32))

        if self.inventory_open:
            self._draw_inventory(surface)

    def _try_use_stairs(self) -> Scene | None:
        tile = self.grid[self.player.y][self.player.x]

        if tile == TILE_STAIRS_DOWN:
            if self.run.floor >= self.run.max_floor:
                self.message = "This is as deep as it goes (for now)."
                return None
            self.run.floor += 1
            self.grid = self._generate_floor()
            pos = _find_tile(self.grid, TILE_STAIRS_UP)
            self.player = GridPlayer(*(pos if pos is not None else (1, 1)))
            self._populate_floor()
            self._check_missions_progress()
            self.message = ""
            return None

        if tile == TILE_STAIRS_UP:
            if self.run.floor <= 1:
                from game.scenes.world_map import WorldMapScene

                return WorldMapScene(self.app)
            self.run.floor -= 1
            self.grid = self._generate_floor()
            pos = _find_tile(self.grid, TILE_STAIRS_DOWN) or _find_tile(self.grid, TILE_FLOOR)
            self.player = GridPlayer(*(pos if pos is not None else (1, 1)))
            self._populate_floor()
            self.message = ""
            return None

        self.message = "No stairs here."
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

        self.player.try_move(dx, dy, self.grid, walls={TILE_WALL})
        self._pickup_if_present()
        self.message = ""
        return True

    def _enemy_turn(self) -> None:
        if STATE.hp <= 0:
            return

        for enemy in self.enemies:
            if not enemy.is_alive():
                continue
            if abs(enemy.x - self.player.x) + abs(enemy.y - self.player.y) == 1:
                STATE.hp = max(0, STATE.hp - enemy.attack)
                self.message = f"{enemy.name} hits you for {enemy.attack}."
                if STATE.hp <= 0:
                    self.message = "You collapse... (Returned to Home Base)"
                    self._handle_player_death()
                continue

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

    def _player_attack(self, enemy: Enemy) -> None:
        damage = 4
        enemy.hp = max(0, enemy.hp - damage)
        if enemy.hp <= 0:
            self.message = f"You defeat {enemy.name}!"
            STATE.gold += 5 + self.run.floor
            if self.rng.random() < 0.25:
                STATE.add_item("potion_small", 1)
                self.message += " Found a Small Potion."
        else:
            self.message = f"You hit {enemy.name} for {damage}."

    def _pickup_if_present(self) -> None:
        for idx, pickup in enumerate(list(self.pickups)):
            if pickup.x == self.player.x and pickup.y == self.player.y:
                STATE.add_item(pickup.item_id, pickup.amount)
                item = get_item(pickup.item_id)
                self.message = f"Picked up {item.name}."
                self.pickups.pop(idx)
                if pickup.item_id == "relic_shard":
                    self._check_missions_progress()
                break

    def _enemy_at(self, x: int, y: int) -> Enemy | None:
        for enemy in self.enemies:
            if enemy.is_alive() and enemy.x == x and enemy.y == y:
                return enemy
        return None

    def _handle_player_death(self) -> None:
        # Reset player to a safe state; scene switch happens on next input (Esc or stairs up).
        STATE.hp = STATE.max_hp

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
        if item_id == "potion_small":
            if STATE.hp >= STATE.max_hp:
                self.message = "HP already full."
                return
            if not STATE.remove_item(item_id, 1):
                return
            heal = 6
            STATE.hp = min(STATE.max_hp, STATE.hp + heal)
            self.message = f"Used {item.name} (+{heal} HP)."
            return
        self.message = f"Used {item.name}."

    def _check_missions_progress(self) -> None:
        if STATE.active_mission == "relic_shard" and STATE.item_count("relic_shard") > 0:
            STATE.completed_missions.add("relic_shard")
            STATE.active_mission = None
            self.message = "Mission complete: Found a Relic Shard!"
        if STATE.active_mission == "reach_floor_3" and self.run.dungeon_id == "temple_ruins" and self.run.floor >= 3:
            STATE.completed_missions.add("reach_floor_3")
            STATE.active_mission = None
            self.message = "Mission complete: Reached Floor 3!"

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
