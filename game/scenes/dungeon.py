import pygame

from game.constants import (
    COLOR_BG,
    COLOR_FLOOR,
    COLOR_PLAYER,
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
from game.entities.player import GridPlayer
from game.scenes.base import Scene
from game.world.dungeon_gen import generate_dungeon
from game.world.dungeon_run import DungeonRun


class DungeonScene(Scene):
    def __init__(self, run: DungeonRun) -> None:
        self.font = pygame.font.SysFont(None, 22)
        self.run = run
        self.grid = self._generate_floor()
        self.player = self._spawn_player()
        self.player_sprite = try_load_sprite("assets/sprites/player.png", size=(TILE_SIZE, TILE_SIZE))
        self.message = ""

    def _generate_floor(self) -> list[list[int]]:
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

    def handle_event(self, event: pygame.event.Event) -> Scene | None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                from game.scenes.world_map import WorldMapScene

                return WorldMapScene()

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
                return None
            elif event.key == pygame.K_e:
                return self._try_use_stairs()

            if dx != 0 or dy != 0:
                self.player.try_move(dx, dy, self.grid, walls={TILE_WALL})

        return None

    def update(self, dt: float) -> Scene | None:
        return None

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)

        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
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

        px = self.player.x * TILE_SIZE
        py = self.player.y * TILE_SIZE
        if self.player_sprite is not None:
            surface.blit(self.player_sprite, (px, py))
        else:
            pygame.draw.rect(surface, COLOR_PLAYER, pygame.Rect(px, py, TILE_SIZE, TILE_SIZE))

        hud = self.font.render(
            f"{self.run.dungeon_name} - Floor {self.run.floor}/{self.run.max_floor} | "
            "Move: WASD/arrows  E: stairs  R: regen  Esc: title",
            True,
            COLOR_TEXT,
        )
        surface.blit(hud, (10, 8))
        if self.message:
            msg = self.font.render(self.message, True, COLOR_TEXT)
            surface.blit(msg, (10, 32))

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
            self.message = ""
            return None

        if tile == TILE_STAIRS_UP:
            if self.run.floor <= 1:
                from game.scenes.world_map import WorldMapScene

                return WorldMapScene()
            self.run.floor -= 1
            self.grid = self._generate_floor()
            pos = _find_tile(self.grid, TILE_STAIRS_DOWN) or _find_tile(self.grid, TILE_FLOOR)
            self.player = GridPlayer(*(pos if pos is not None else (1, 1)))
            self.message = ""
            return None

        self.message = "No stairs here."
        return None


def _find_tile(grid: list[list[int]], tile: int) -> tuple[int, int] | None:
    for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            if cell == tile:
                return (x, y)
    return None
