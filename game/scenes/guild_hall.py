import pygame

from game.assets import try_load_sprite
from game.assets_manifest import PATHS
from game.constants import (
    COLOR_BG,
    COLOR_BED,
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
from game.ui.dialogue_box import DialogueBox
from game.ui.status_menu import StatusMenu


class GuildHallScene(Scene):
    def __init__(self, app, *, spawn: tuple[int, int] | None = None) -> None:
        super().__init__(app)
        self.font = pygame.font.SysFont(None, 22)
        self.app.audio.play_music(PATHS.music / "town.ogg", volume=0.45)

        self.grid = _guild_layout(GRID_WIDTH, GRID_HEIGHT)
        sx, sy = spawn if spawn is not None else (GRID_WIDTH // 2, GRID_HEIGHT - 4)
        self.player = GridPlayer(sx, sy)
        self.player_sprite = try_load_sprite(PATHS.sprites / "player.png", size=(TILE_SIZE, TILE_SIZE))

        self.tiles = {
            TILE_FLOOR: try_load_sprite(PATHS.tiles / "floor.png", size=(TILE_SIZE, TILE_SIZE)),
            TILE_WALL: try_load_sprite(PATHS.tiles / "wall.png", size=(TILE_SIZE, TILE_SIZE)),
            TILE_DOOR: try_load_sprite(PATHS.tiles / "guild.png", size=(TILE_SIZE, TILE_SIZE)),
        }

        self.npcs = [
            Npc("guild_clerk", "Clerk", x=GRID_WIDTH // 2, y=4),
            Npc("guild_captain", "Captain", x=GRID_WIDTH // 2 - 6, y=7),
            Npc("guild_quartermaster", "Quartermaster", x=GRID_WIDTH // 2 + 6, y=7),
        ]
        self.npc_sprites = {
            npc.npc_id: try_load_sprite(PATHS.sprites / "npcs" / f"{npc.npc_id}_down.png", size=(TILE_SIZE, TILE_SIZE))
            for npc in self.npcs
        }

        self.dialogue = DialogueBox()
        self.active_lines: list[str] | None = None
        self.active_speaker = ""
        self.active_index = 0
        self.on_finish = None

        self.status_menu = StatusMenu()
        self.status_open = False

    def handle_event(self, event: pygame.event.Event) -> Scene | None:
        if event.type != pygame.KEYDOWN:
            return None

        if event.key == pygame.K_ESCAPE:
            if self.status_open:
                self.status_open = False
                return None
            if self.active_lines is not None:
                self._close_dialogue()
                return None
            from game.scenes.town import TownScene

            return TownScene(self.app, spawn=(6, GRID_HEIGHT // 2))

        if event.key == pygame.K_i:
            self.status_open = not self.status_open
            return None

        if self.status_open:
            return None

        if event.key == pygame.K_b:
            from game.scenes.inventory import InventoryScene

            return InventoryScene(self.app, return_scene=self)

        if self.active_lines is not None:
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
            npc = self._interactable_npc()
            if npc is not None:
                self._start_npc_dialogue(npc.npc_id, npc.name)
            return None

        if dx != 0 or dy != 0:
            return self._try_move(dx, dy)
        return None

    def update(self, dt: float) -> Scene | None:
        return None

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        _draw_grid(surface, self.grid, self.tiles)

        for npc in self.npcs:
            spr = self.npc_sprites.get(npc.npc_id)
            if spr is not None:
                surface.blit(spr, (npc.x * TILE_SIZE, npc.y * TILE_SIZE))
            else:
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

        hint = "Guild Hall: move WASD/arrows  E: talk  B: inventory  I: status  Esc: town"
        if self._interactable_npc() is not None:
            hint = "Guild Hall: E to talk"
        hud = self.font.render(hint, True, COLOR_TEXT)
        surface.blit(hud, (10, 8))

        if self.active_lines is not None:
            self.dialogue.draw(surface, speaker=self.active_speaker, line=self.active_lines[self.active_index])

        if self.status_open:
            self.status_menu.draw(surface, STATE)

    def _try_move(self, dx: int, dy: int) -> Scene | None:
        nx = self.player.x + dx
        ny = self.player.y + dy
        if any(n.x == nx and n.y == ny for n in self.npcs):
            return None
        self.player.try_move(dx, dy, self.grid, walls={TILE_WALL})
        if self.grid[self.player.y][self.player.x] == TILE_DOOR:
            from game.scenes.town import TownScene

            self.app.audio.play_sfx(PATHS.sfx / "door.wav", volume=0.4)
            return TownScene(self.app, spawn=(6, GRID_HEIGHT // 2))
        return None

    def _interactable_npc(self) -> Npc | None:
        for npc in self.npcs:
            if abs(npc.x - self.player.x) + abs(npc.y - self.player.y) <= 1:
                return npc
        return None

    def _start_npc_dialogue(self, npc_id: str, name: str) -> None:
        if npc_id == "guild_clerk":
            lines = [
                "Need work? The board is open.",
                "I'll show you the available missions.",
            ]
            self._start_dialogue(name, lines, on_finish=self._open_board)
            return
        if npc_id == "guild_captain":
            if STATE.active_mission:
                lines = [
                    "Eyes up out there.",
                    "Finish your contract, then report back for your reward.",
                ]
            else:
                lines = [
                    "We take contracts seriously.",
                    "Pick a mission from the clerk when you're ready.",
                ]
            self._start_dialogue(name, lines)
            return
        if npc_id == "guild_quartermaster":
            lines = [
                "If you're low on supplies, check the shop.",
                "And don't forget—gear matters. A good jacket can save your life.",
            ]
            self._start_dialogue(name, lines)
            return

    def _start_dialogue(self, speaker: str, lines: list[str], *, on_finish=None) -> None:
        self.active_speaker = speaker
        self.active_lines = lines if lines else ["..."]
        self.active_index = 0
        self.on_finish = on_finish

    def _advance_dialogue(self) -> None:
        if self.active_lines is None:
            return
        self.active_index += 1
        if self.active_index < len(self.active_lines):
            return
        on_finish = self.on_finish
        self._close_dialogue()
        if on_finish is not None:
            on_finish()

    def _close_dialogue(self) -> None:
        self.active_lines = None
        self.active_speaker = ""
        self.active_index = 0
        self.on_finish = None

    def _open_board(self) -> None:
        from game.scenes.guild import GuildScene

        self.app.audio.play_sfx(PATHS.sfx / "confirm.wav", volume=0.35)
        self.app.set_scene(GuildScene(self.app))


def _guild_layout(width: int, height: int) -> list[list[int]]:
    grid = [[TILE_FLOOR for _ in range(width)] for _ in range(height)]
    for x in range(width):
        grid[0][x] = TILE_WALL
        grid[height - 1][x] = TILE_WALL
    for y in range(height):
        grid[y][0] = TILE_WALL
        grid[y][width - 1] = TILE_WALL

    # Interior walls (simple room-within-room feel)
    for x in range(4, width - 4):
        grid[3][x] = TILE_WALL
    grid[3][width // 2] = TILE_FLOOR  # opening behind clerk

    # Exit door at bottom center
    grid[height - 2][width // 2] = TILE_DOOR
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
            else:
                color = COLOR_FLOOR
            pygame.draw.rect(surface, color, pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
