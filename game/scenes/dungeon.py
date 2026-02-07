import pygame

from game.constants import (
    COLOR_BG,
    COLOR_FLOOR,
    COLOR_PLAYER,
    COLOR_TEXT,
    COLOR_WALL,
    GRID_HEIGHT,
    GRID_WIDTH,
    TILE_SIZE,
)
from game.entities.player import GridPlayer
from game.scenes.base import Scene
from game.world.dungeon_gen import generate_dungeon


class DungeonScene(Scene):
    def __init__(self) -> None:
        self.font = pygame.font.SysFont(None, 22)
        self.grid = generate_dungeon(GRID_WIDTH, GRID_HEIGHT)
        self.player = GridPlayer.spawn_on_floor(self.grid)

    def handle_event(self, event: pygame.event.Event) -> Scene | None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                from game.scenes.title import TitleScene

                return TitleScene()

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
                self.grid = generate_dungeon(GRID_WIDTH, GRID_HEIGHT)
                self.player = GridPlayer.spawn_on_floor(self.grid)
                return None

            if dx != 0 or dy != 0:
                self.player.try_move(dx, dy, self.grid)

        return None

    def update(self, dt: float) -> Scene | None:
        return None

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)

        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                color = COLOR_FLOOR if cell == 0 else COLOR_WALL
                pygame.draw.rect(
                    surface,
                    color,
                    pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE),
                )

        pygame.draw.rect(
            surface,
            COLOR_PLAYER,
            pygame.Rect(
                self.player.x * TILE_SIZE,
                self.player.y * TILE_SIZE,
                TILE_SIZE,
                TILE_SIZE,
            ),
        )

        hud = self.font.render("Arrows/WASD: move  R: regen  Esc: back", True, COLOR_TEXT)
        surface.blit(hud, (10, 8))
