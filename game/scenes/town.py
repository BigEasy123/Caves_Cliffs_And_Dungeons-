import pygame

from game.assets import try_load_sprite
from game.assets_manifest import PATHS
from game.constants import (
    COLOR_BG,
    COLOR_DOOR,
    COLOR_FLOOR,
    COLOR_GUILD,
    COLOR_HEALER,
    COLOR_PLAYER,
    COLOR_SHOP,
    COLOR_TEXT,
    COLOR_WALL,
    GRID_HEIGHT,
    GRID_WIDTH,
    TILE_DOOR,
    TILE_FLOOR,
    TILE_GUILD_DOOR,
    TILE_HEALER_DOOR,
    TILE_SHOP_DOOR,
    TILE_SIZE,
    TILE_WALL,
)
from game.entities.npc import Npc
from game.entities.player import GridPlayer
from game.scenes.base import Scene
from game.state import STATE
from game.story.scripts import script_for_npc
from game.ui.dialogue_box import DialogueBox
from game.ui.status_menu import StatusMenu


class TownScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.font = pygame.font.SysFont(None, 22)
        self.app.audio.play_music(PATHS.music / "town.ogg", volume=0.45)

        self.grid = _town_layout(GRID_WIDTH, GRID_HEIGHT)
        self.player = GridPlayer(12, 10)
        self.player_sprite = try_load_sprite("assets/sprites/player.png", size=(TILE_SIZE, TILE_SIZE))
        self.tiles = {
            TILE_FLOOR: try_load_sprite(PATHS.tiles / "floor.png", size=(TILE_SIZE, TILE_SIZE)),
            TILE_WALL: try_load_sprite(PATHS.tiles / "wall.png", size=(TILE_SIZE, TILE_SIZE)),
            TILE_DOOR: try_load_sprite(PATHS.tiles / "door.png", size=(TILE_SIZE, TILE_SIZE)),
            TILE_SHOP_DOOR: try_load_sprite(PATHS.tiles / "shop.png", size=(TILE_SIZE, TILE_SIZE)),
            TILE_GUILD_DOOR: try_load_sprite(PATHS.tiles / "guild.png", size=(TILE_SIZE, TILE_SIZE)),
            TILE_HEALER_DOOR: try_load_sprite(PATHS.tiles / "healer.png", size=(TILE_SIZE, TILE_SIZE)),
        }

        self.npcs = [
            Npc("mayor", "Mayor", x=7, y=4),
            Npc("archivist", "Archivist", x=12, y=8),
        ]
        self.dialogue = DialogueBox()
        self.status_menu = StatusMenu()
        self.status_open = False
        self.active_script = None
        self.active_line_index = 0

    def handle_event(self, event: pygame.event.Event) -> Scene | None:
        if event.type != pygame.KEYDOWN:
            return None

        if event.key == pygame.K_ESCAPE:
            if self.status_open:
                self.status_open = False
                return None
            if self.active_script is not None:
                self.active_script = None
                self.active_line_index = 0
                return None
            from game.scenes.title import TitleScene

            return TitleScene(self.app)

        if event.key == pygame.K_i:
            self.status_open = not self.status_open
            return None

        if self.status_open:
            return None

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
            door_tile = _adjacent_tile(
                self.grid,
                self.player.x,
                self.player.y,
                {TILE_DOOR, TILE_SHOP_DOOR, TILE_GUILD_DOOR, TILE_HEALER_DOOR},
            )
            if door_tile == TILE_SHOP_DOOR:
                from game.scenes.shop import ShopScene

                return ShopScene(self.app)
            if door_tile == TILE_GUILD_DOOR:
                from game.scenes.guild import GuildScene

                return GuildScene(self.app)
            if door_tile == TILE_HEALER_DOOR:
                from game.scenes.healer import HealerScene

                return HealerScene(self.app)
            if door_tile == TILE_DOOR:
                from game.scenes.world_map import WorldMapScene

                return WorldMapScene(self.app)
            return None

        if dx != 0 or dy != 0:
            self._try_move_player(dx, dy)
        return None

    def update(self, dt: float) -> Scene | None:
        return None

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        _draw_grid(surface, self.grid, self.tiles)

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

        hint = "Town: move WASD/arrows  E: talk/exit  Esc: title"
        if self._interactable_npc() is not None:
            hint = "Town: E to talk"
        elif _adjacent_tile(
            self.grid,
            self.player.x,
            self.player.y,
            {TILE_DOOR, TILE_SHOP_DOOR, TILE_GUILD_DOOR, TILE_HEALER_DOOR},
        ) is not None:
            hint = "Town: E to enter"
        hud = self.font.render(hint, True, COLOR_TEXT)
        surface.blit(hud, (10, 8))

        if self.active_script is not None:
            line = self.active_script.lines[self.active_line_index]
            self.dialogue.draw(surface, speaker=self.active_script.speaker, line=line)

        if self.status_open:
            self.status_menu.draw(surface, STATE)

    def _try_start_dialogue(self) -> bool:
        npc = self._interactable_npc()
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

    def _interactable_npc(self) -> Npc | None:
        for npc in self.npcs:
            if abs(npc.x - self.player.x) + abs(npc.y - self.player.y) <= 1:
                return npc
        return None

    def _try_move_player(self, dx: int, dy: int) -> None:
        nx = self.player.x + dx
        ny = self.player.y + dy
        if any(npc.x == nx and npc.y == ny for npc in self.npcs):
            return
        self.player.try_move(dx, dy, self.grid, walls={TILE_WALL})


def _town_layout(width: int, height: int) -> list[list[int]]:
    grid = [[TILE_FLOOR for _ in range(width)] for _ in range(height)]

    for x in range(width):
        grid[0][x] = TILE_WALL
        grid[height - 1][x] = TILE_WALL
    for y in range(height):
        grid[y][0] = TILE_WALL
        grid[y][width - 1] = TILE_WALL

    # Mayor's office (walk-in, no scene transition)
    _rect_walls(grid, x1=4, y1=2, x2=11, y2=6)
    grid[6][7] = TILE_FLOOR  # entrance opening

    # Shop (door tile triggers ShopScene)
    _rect_walls(grid, x1=14, y1=2, x2=22, y2=6)
    grid[6][18] = TILE_SHOP_DOOR

    # Guild (door tile triggers GuildScene)
    _rect_walls(grid, x1=3, y1=8, x2=10, y2=12)
    grid[12][6] = TILE_GUILD_DOOR

    # Healer (door tile triggers HealerScene)
    _rect_walls(grid, x1=14, y1=8, x2=21, y2=12)
    grid[12][17] = TILE_HEALER_DOOR

    grid[height // 2][1] = TILE_DOOR
    return grid


def _draw_grid(surface: pygame.Surface, grid: list[list[int]], tiles: dict[int, pygame.Surface | None]) -> None:
    for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            sprite = tiles.get(cell)
            if sprite is not None:
                surface.blit(sprite, (x * TILE_SIZE, y * TILE_SIZE))
                continue
            if cell == TILE_WALL:
                color = COLOR_WALL
            elif cell == TILE_DOOR:
                color = COLOR_DOOR
            elif cell == TILE_SHOP_DOOR:
                color = COLOR_SHOP
            elif cell == TILE_GUILD_DOOR:
                color = COLOR_GUILD
            elif cell == TILE_HEALER_DOOR:
                color = COLOR_HEALER
            else:
                color = COLOR_FLOOR
            pygame.draw.rect(surface, color, pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))


def _adjacent_tile(grid: list[list[int]], x: int, y: int, tiles: set[int]) -> int | None:
    if grid[y][x] in tiles:
        return grid[y][x]
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nx, ny = x + dx, y + dy
        if 0 <= ny < len(grid) and 0 <= nx < len(grid[0]) and grid[ny][nx] in tiles:
            return grid[ny][nx]
    return None


def _rect_walls(grid: list[list[int]], *, x1: int, y1: int, x2: int, y2: int) -> None:
    for x in range(x1, x2 + 1):
        grid[y1][x] = TILE_WALL
        grid[y2][x] = TILE_WALL
    for y in range(y1, y2 + 1):
        grid[y][x1] = TILE_WALL
        grid[y][x2] = TILE_WALL
