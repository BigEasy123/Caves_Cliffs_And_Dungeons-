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
from game.entities.npc import Npc
from game.entities.player import GridPlayer
from game.scenes.base import Scene
from game.state import STATE
from game.story.scripts import script_for_npc
from game.ui.dialogue_box import DialogueBox


class TownScene(Scene):
    def __init__(self) -> None:
        self.font = pygame.font.SysFont(None, 22)

        self.grid = _town_layout(GRID_WIDTH, GRID_HEIGHT)
        self.player = GridPlayer(5, 10)
        self.player_sprite = try_load_sprite("assets/sprites/player.png", size=(TILE_SIZE, TILE_SIZE))

        self.npcs = [
            Npc("mayor", "Mayor", x=10, y=8),
            Npc("archivist", "Archivist", x=18, y=12),
        ]
        self.dialogue = DialogueBox()
        self.active_script = None
        self.active_line_index = 0

    def handle_event(self, event: pygame.event.Event) -> Scene | None:
        if event.type != pygame.KEYDOWN:
            return None

        if event.key == pygame.K_ESCAPE:
            if self.active_script is not None:
                self.active_script = None
                self.active_line_index = 0
                return None
            from game.scenes.title import TitleScene

            return TitleScene()

        if self.active_script is not None:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_e, pygame.K_SPACE):
                self._advance_dialogue()
            return None

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
            if self._try_start_dialogue():
                return None
            if self.grid[self.player.y][self.player.x] == TILE_DOOR:
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

        for npc in self.npcs:
            pygame.draw.rect(
                surface,
                (180, 110, 210),
                pygame.Rect(npc.x * TILE_SIZE, npc.y * TILE_SIZE, TILE_SIZE, TILE_SIZE),
            )

        px = self.player.x * TILE_SIZE
        py = self.player.y * TILE_SIZE
        if self.player_sprite is not None:
            surface.blit(self.player_sprite, (px, py))
        else:
            pygame.draw.rect(surface, COLOR_PLAYER, pygame.Rect(px, py, TILE_SIZE, TILE_SIZE))

        hud = self.font.render(
            "Town: move WASD/arrows  E: talk/exit  Esc: title",
            True,
            COLOR_TEXT,
        )
        surface.blit(hud, (10, 8))

        if self.active_script is not None:
            line = self.active_script.lines[self.active_line_index]
            self.dialogue.draw(surface, speaker=self.active_script.speaker, line=line)

    def _try_start_dialogue(self) -> bool:
        npc = self._adjacent_npc()
        if npc is None:
            return False
        script = script_for_npc(npc.npc_id, STATE)
        if script is None:
            return False
        self.active_script = script
        self.active_line_index = 0
        return True

    def _advance_dialogue(self) -> None:
        if self.active_script is None:
            return
        self.active_line_index += 1
        if self.active_line_index < len(self.active_script.lines):
            return
        if self.active_script.on_finish is not None:
            self.active_script.on_finish(STATE)
        self.active_script = None
        self.active_line_index = 0

    def _adjacent_npc(self) -> Npc | None:
        for npc in self.npcs:
            if abs(npc.x - self.player.x) + abs(npc.y - self.player.y) == 1:
                return npc
        return None


def _town_layout(width: int, height: int) -> list[list[int]]:
    grid = [[TILE_FLOOR for _ in range(width)] for _ in range(height)]

    for x in range(width):
        grid[0][x] = TILE_WALL
        grid[height - 1][x] = TILE_WALL
    for y in range(height):
        grid[y][0] = TILE_WALL
        grid[y][width - 1] = TILE_WALL

    for x in range(6, 14):
        grid[6][x] = TILE_WALL
        grid[9][x] = TILE_WALL
    for y in range(6, 10):
        grid[y][6] = TILE_WALL
        grid[y][13] = TILE_WALL

    grid[height // 2][1] = TILE_DOOR
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
