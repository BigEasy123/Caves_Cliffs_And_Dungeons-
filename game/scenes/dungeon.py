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
    TILE_DUNGEON_EXIT,
    GRID_HEIGHT,
    GRID_WIDTH,
    TILE_FLOOR,
    TILE_STAIRS_DOWN,
    TILE_STAIRS_UP,
    TILE_WALL,
    TILE_SIZE,
)
from game.assets import try_load_sprite
from game.enemies import enemy_table_for_dungeon, spawn_enemy
from game.entities.enemy import Enemy
from game.entities.pickup import Pickup
from game.entities.player import GridPlayer
from game.items import ITEMS, get_item
from game.scenes.base import Scene
from game.state import STATE
from game.story.missions import MISSIONS
from game.world.dungeon_gen import generate_dungeon
from game.world.dungeon_run import DungeonRun


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
        self.player_sprite = try_load_sprite("assets/sprites/player.png", size=(TILE_SIZE, TILE_SIZE))
        self.enemy_sprite = try_load_sprite("assets/sprites/enemy.png", size=(TILE_SIZE, TILE_SIZE))
        self.tiles = {
            TILE_FLOOR: try_load_sprite(PATHS.tiles / "floor.png", size=(TILE_SIZE, TILE_SIZE)),
            TILE_WALL: try_load_sprite(PATHS.tiles / "wall.png", size=(TILE_SIZE, TILE_SIZE)),
            TILE_STAIRS_DOWN: try_load_sprite(PATHS.tiles / "stairs_down.png", size=(TILE_SIZE, TILE_SIZE)),
            TILE_STAIRS_UP: try_load_sprite(PATHS.tiles / "stairs_up.png", size=(TILE_SIZE, TILE_SIZE)),
            TILE_DUNGEON_EXIT: try_load_sprite(PATHS.tiles / "exit.png", size=(TILE_SIZE, TILE_SIZE)),
        }
        self.message = ""
        self.inventory_open = False
        self.inventory_index = 0
        self.pending_scene: Scene | None = None
        self.turn = 0

    def _generate_floor(self) -> list[list[int]]:
        self.rng = random.Random(self.run.seed_for_floor(self.run.floor))
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
        table = enemy_table_for_dungeon(self.run.dungeon_id, self.run.floor)
        for _ in range(enemy_count):
            if not floor_cells:
                break
            x, y = floor_cells.pop()
            if (x, y) == (self.player.x, self.player.y):
                continue
            if self.grid[y][x] in (TILE_STAIRS_DOWN, TILE_STAIRS_UP):
                continue
            enemy_id = self.rng.choice(table)
            self.enemies.append(spawn_enemy(enemy_id, x=x, y=y, floor=self.run.floor, rng=self.rng))

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
        if self.pending_scene is not None:
            return self.pending_scene

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.message = "You can't leave mid-run. Finish the mission or reach the bottom."
                return None

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
        if self.pending_scene is not None:
            return self.pending_scene
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

        mission_line = self._mission_hud_text()
        if mission_line:
            mission = self.font.render(mission_line, True, (200, 200, 210))
            surface.blit(mission, (10, 32))

        if self.message:
            msg = self.font.render(self.message, True, COLOR_TEXT)
            surface.blit(msg, (10, 56))

        if self.inventory_open:
            self._draw_inventory(surface)

    def _try_use_stairs(self) -> Scene | None:
        tile = self.grid[self.player.y][self.player.x]

        if tile == TILE_DUNGEON_EXIT:
            self.message = "You escape the dungeon!"
            return self._return_scene()

        if tile == TILE_STAIRS_DOWN:
            if self.run.floor >= self.run.max_floor:
                self.message = "This is as deep as it goes (for now)."
                return None
            self.run.floor += 1
            self.grid = self._generate_floor()
            pos = _find_tile(self.grid, TILE_STAIRS_UP)
            self.player = GridPlayer(*(pos if pos is not None else (1, 1)))
            self._populate_floor()
            if self._check_missions_progress():
                return self.pending_scene
            self.message = ""
            return None

        if tile == TILE_STAIRS_UP:
            if self.run.floor <= 1:
                self.message = "No turning back now."
                return None
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

        self.turn += 1
        for enemy in self.enemies:
            if not enemy.is_alive():
                continue
            self._update_aggro(enemy)
            if enemy.aggro_turns <= 0:
                # Idle wander sometimes
                if enemy.should_move(self.turn) and self.rng.random() < 0.35:
                    self._enemy_wander(enemy)
                continue

            if abs(enemy.x - self.player.x) + abs(enemy.y - self.player.y) == 1 and enemy.should_attack(self.turn):
                damage = max(1, enemy.attack)
                STATE.hp = max(0, STATE.hp - damage)
                self.message = f"{enemy.name} hits you for {damage}."
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

    def _player_attack(self, enemy: Enemy) -> None:
        damage = max(1, 4 - getattr(enemy, "defense", 0))
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
        STATE.hp = STATE.max_hp
        from game.scenes.home import HomeBaseScene

        self.pending_scene = HomeBaseScene(self.app)

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

    def _check_missions_progress(self) -> bool:
        completed = False
        if STATE.active_mission == "relic_shard" and STATE.item_count("relic_shard") > 0:
            STATE.completed_missions.add("relic_shard")
            STATE.active_mission = None
            self.message = "Mission complete: Found a Relic Shard!"
            completed = True
        if STATE.active_mission == "reach_floor_3" and self.run.dungeon_id == "temple_ruins" and self.run.floor >= 3:
            STATE.completed_missions.add("reach_floor_3")
            STATE.active_mission = None
            self.message = "Mission complete: Reached Floor 3!"
            completed = True

        if completed:
            self.pending_scene = self._return_scene()
        return completed

    def _mission_hud_text(self) -> str:
        mission_id = STATE.active_mission
        if not mission_id:
            return ""
        mission = MISSIONS.get(mission_id)
        if mission is None:
            return f"Mission: {mission_id}"
        return f"Mission: {mission.name} — {mission.description}"

    def _return_scene(self) -> Scene:
        if self.return_to == "outskirts":
            from game.scenes.outskirts import OutskirtsScene

            return OutskirtsScene(self.app, spawn=(GRID_WIDTH - 4, GRID_HEIGHT // 2))
        from game.scenes.town import TownScene

        return TownScene(self.app, spawn=(GRID_WIDTH - 4, GRID_HEIGHT // 2))

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
