import pygame

from game.assets import try_load_sprite
from game.assets_manifest import PATHS
from game.constants import (
    COLOR_BG,
    COLOR_DUNGEON_JUNGLE,
    COLOR_DUNGEON_TEMPLE,
    COLOR_EXIT,
    COLOR_FLOOR,
    COLOR_PLAYER,
    COLOR_TEXT,
    COLOR_WALL,
    GRID_HEIGHT,
    GRID_WIDTH,
    TILE_DUNGEON_JUNGLE,
    TILE_DUNGEON_TEMPLE,
    TILE_EXIT_HOME,
    TILE_FLOOR,
    TILE_SIZE,
    TILE_WALL,
)
from game.scenes.base import Scene
from game.state import STATE
from game.story.flags import FLAG_GOT_TEMPLE_PASS
from game.ui.status_menu import StatusMenu
from game.world.dungeon_run import DungeonRun


class OutskirtsScene(Scene):
    def __init__(self, app, *, spawn: tuple[int, int] | None = None) -> None:
        super().__init__(app)
        self.font = pygame.font.SysFont(None, 22)
        self.app.audio.play_music(PATHS.music / "world_map.ogg", volume=0.45)
        self.status_menu = StatusMenu()
        self.status_open = False

        self.grid = _layout(GRID_WIDTH, GRID_HEIGHT)
        sx, sy = spawn if spawn is not None else (3, GRID_HEIGHT // 2)
        from game.entities.player import GridPlayer

        self.player = GridPlayer(sx, sy)
        self.player_sprite = try_load_sprite(PATHS.sprites / "player.png", size=(TILE_SIZE, TILE_SIZE))
        self.tiles = {
            TILE_FLOOR: try_load_sprite(PATHS.tiles / "floor.png", size=(TILE_SIZE, TILE_SIZE)),
            TILE_WALL: try_load_sprite(PATHS.tiles / "wall.png", size=(TILE_SIZE, TILE_SIZE)),
            TILE_EXIT_HOME: try_load_sprite(PATHS.tiles / "door.png", size=(TILE_SIZE, TILE_SIZE)),
            TILE_DUNGEON_TEMPLE: try_load_sprite(PATHS.tiles / "temple.png", size=(TILE_SIZE, TILE_SIZE)),
            TILE_DUNGEON_JUNGLE: try_load_sprite(PATHS.tiles / "jungle.png", size=(TILE_SIZE, TILE_SIZE)),
        }

        self.message = ""

    def handle_event(self, event: pygame.event.Event) -> Scene | None:
        if event.type != pygame.KEYDOWN:
            return None

        if event.key == pygame.K_ESCAPE:
            if self.status_open:
                self.status_open = False
                return None
            from game.scenes.title import TitleScene

            return TitleScene(self.app)

        if event.key == pygame.K_i:
            self.status_open = not self.status_open
            return None

        if self.status_open:
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
            return self._try_enter()

        if dx != 0 or dy != 0:
            self._try_move(dx, dy)
        return None

    def update(self, dt: float) -> Scene | None:
        return None

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        _draw_grid(surface, self.grid, self.tiles)

        px = self.player.x * TILE_SIZE
        py = self.player.y * TILE_SIZE
        if self.player_sprite is not None:
            surface.blit(self.player_sprite, (px, py))
        else:
            pygame.draw.rect(surface, COLOR_PLAYER, pygame.Rect(px, py, TILE_SIZE, TILE_SIZE))

        hud = self.font.render("Outskirts: move WASD/arrows  E: enter  I: status  Esc: title", True, COLOR_TEXT)
        surface.blit(hud, (10, 8))

        if self.message:
            msg = self.font.render(self.message, True, (220, 190, 120))
            surface.blit(msg, (10, 32))

        if self.status_open:
            self.status_menu.draw(surface, STATE)

    def _try_move(self, dx: int, dy: int) -> None:
        from game.entities.player import GridPlayer

        self.player.try_move(dx, dy, self.grid, walls={TILE_WALL})
        self.message = ""

    def _try_enter(self) -> Scene | None:
        tile = _adjacent_tile(self.grid, self.player.x, self.player.y)
        if tile == TILE_EXIT_HOME:
            from game.scenes.town import TownScene

            return TownScene(self.app, spawn=(GRID_WIDTH - 3, GRID_HEIGHT // 2))

        if tile == TILE_DUNGEON_TEMPLE:
            if not STATE.has(FLAG_GOT_TEMPLE_PASS):
                self.message = "Temple Ruins is locked. Talk to the Mayor in town."
                return None
            from game.scenes.dungeon import DungeonScene

            run = DungeonRun(dungeon_id="temple_ruins", dungeon_name="Temple Ruins", max_floor=5)
            return DungeonScene(self.app, run, return_to="outskirts")

        if tile == TILE_DUNGEON_JUNGLE:
            if "relic_shard" not in STATE.completed_missions:
                self.message = "Jungle Cavern is locked. Complete a guild mission."
                return None
            from game.scenes.dungeon import DungeonScene

            run = DungeonRun(dungeon_id="jungle_cavern", dungeon_name="Jungle Cavern", max_floor=7)
            return DungeonScene(self.app, run, return_to="outskirts")

        self.message = "Nothing to enter here."
        return None


def _layout(width: int, height: int) -> list[list[int]]:
    grid = [[TILE_FLOOR for _ in range(width)] for _ in range(height)]

    for x in range(width):
        grid[0][x] = TILE_WALL
        grid[height - 1][x] = TILE_WALL
    for y in range(height):
        grid[y][0] = TILE_WALL
        grid[y][width - 1] = TILE_WALL

    # Path area
    for y in range(3, height - 3):
        grid[y][2] = TILE_WALL
        grid[y][width - 3] = TILE_WALL

    # Entrance back to town on the left
    grid[height // 2][1] = TILE_EXIT_HOME

    # Temple Ruins entrance (upper)
    grid[5][width - 6] = TILE_DUNGEON_TEMPLE
    # Jungle Cavern entrance (lower)
    grid[height - 6][width - 6] = TILE_DUNGEON_JUNGLE
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
            elif cell == TILE_EXIT_HOME:
                color = COLOR_EXIT
            elif cell == TILE_DUNGEON_TEMPLE:
                color = COLOR_DUNGEON_TEMPLE
            elif cell == TILE_DUNGEON_JUNGLE:
                color = COLOR_DUNGEON_JUNGLE
            else:
                color = COLOR_FLOOR
            pygame.draw.rect(surface, color, pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))


def _adjacent_tile(grid: list[list[int]], x: int, y: int) -> int | None:
    for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
        nx, ny = x + dx, y + dy
        if 0 <= ny < len(grid) and 0 <= nx < len(grid[0]):
            cell = grid[ny][nx]
            if cell != TILE_FLOOR and cell != TILE_WALL:
                return cell
    return None

