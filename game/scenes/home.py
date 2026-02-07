import pygame

from game.assets import try_load_sprite
from game.constants import (
    COLOR_BG,
    COLOR_DOOR,
    COLOR_FLOOR,
    COLOR_PLAYER,
    COLOR_TEXT,
    COLOR_WALL,
    GRID_HEIGHT,
    GRID_WIDTH,
    TILE_DOOR,
    TILE_FLOOR,
    TILE_SIZE,
    TILE_WALL,
)
from game.entities.player import GridPlayer
from game.scenes.base import Scene


class HomeBaseScene(Scene):
    def __init__(self) -> None:
        self.font = pygame.font.SysFont(None, 22)

        self.grid = _home_layout(GRID_WIDTH, GRID_HEIGHT)
        self.player = GridPlayer(4, 6)
        self.player_sprite = try_load_sprite("assets/sprites/player.png", size=(TILE_SIZE, TILE_SIZE))

    def handle_event(self, event: pygame.event.Event) -> Scene | None:
        if event.type != pygame.KEYDOWN:
            return None

        if event.key == pygame.K_ESCAPE:
            from game.scenes.title import TitleScene

            return TitleScene()

        if event.key == pygame.K_m:
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
        elif event.key == pygame.K_e:
            if _is_on_or_adjacent(self.grid, self.player.x, self.player.y, TILE_DOOR):
                from game.scenes.world_map import WorldMapScene

                return WorldMapScene()
            return None

        if dx != 0 or dy != 0:
            self.player.try_move(dx, dy, self.grid, walls={TILE_WALL})
        return None

    def update(self, dt: float) -> Scene | None:
        return None

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        _draw_grid(surface, self.grid)

        px = self.player.x * TILE_SIZE
        py = self.player.y * TILE_SIZE
        if self.player_sprite is not None:
            surface.blit(self.player_sprite, (px, py))
        else:
            pygame.draw.rect(surface, COLOR_PLAYER, pygame.Rect(px, py, TILE_SIZE, TILE_SIZE))

        hud = self.font.render(
            "Home Base: move WASD/arrows  E: exit (at door)  M: World Map  Esc: title",
            True,
            COLOR_TEXT,
        )
        surface.blit(hud, (10, 8))


def _home_layout(width: int, height: int) -> list[list[int]]:
    grid = [[TILE_WALL for _ in range(width)] for _ in range(height)]

    room_w, room_h = 12, 9
    ox, oy = 2, 3
    for y in range(oy, oy + room_h):
        for x in range(ox, ox + room_w):
            grid[y][x] = TILE_FLOOR

    door_x = ox + room_w - 1
    door_y = oy + room_h // 2
    grid[door_y][door_x] = TILE_DOOR
    return grid


def _draw_grid(surface: pygame.Surface, grid: list[list[int]]) -> None:
    for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            if cell == TILE_WALL:
                color = COLOR_WALL
            elif cell == TILE_DOOR:
                color = COLOR_DOOR
            else:
                color = COLOR_FLOOR
            pygame.draw.rect(surface, color, pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))


def _is_on_or_adjacent(grid: list[list[int]], x: int, y: int, tile: int) -> bool:
    if grid[y][x] == tile:
        return True
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nx, ny = x + dx, y + dy
        if 0 <= ny < len(grid) and 0 <= nx < len(grid[0]) and grid[ny][nx] == tile:
            return True
    return False
