import pygame

from game.anim import DirectionalStepAnimator
from game.assets import load_sprite_variants, pick_variant, try_load_sprite
from game.assets_manifest import PATHS
from game.constants import (
    COLOR_BG,
    COLOR_PLAYER,
    COLOR_TEXT,
    COLOR_WALL,
    GRID_HEIGHT,
    GRID_WIDTH,
    TILE_FLOOR,
    TILE_SIZE,
    TILE_WALL,
)
from game.entities.npc import Npc
from game.entities.player import GridPlayer
from game.scenes.base import Scene
from game.state import STATE
from game.story.scripts import format_dialogue_script, script_for_npc
from game.ui.dialogue_box import DialogueBox
from game.ui.status_menu import StatusMenu


class BaseCampScene(Scene):
    def __init__(self, app, *, spawn: tuple[int, int] | None = None) -> None:
        super().__init__(app)
        self.font = pygame.font.SysFont(None, 22)
        self.app.audio.play_music(PATHS.music / "world_map.ogg", volume=0.45)
        self.status_menu = StatusMenu()
        self.status_open = False

        self.grid = _layout(GRID_WIDTH, GRID_HEIGHT)
        sx, sy = spawn if spawn is not None else (GRID_WIDTH // 2, GRID_HEIGHT - 4)
        self.player = GridPlayer(sx, sy)

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
            self.player_anim = DirectionalStepAnimator(frames_by_dir) if any(frames_by_dir.values()) else None
        except Exception:
            self.player_anim = None

        self.floor = load_sprite_variants(PATHS.tiles, prefix="floor_snow", size=(TILE_SIZE, TILE_SIZE)) or load_sprite_variants(
            PATHS.tiles, prefix="floor_gravel", size=(TILE_SIZE, TILE_SIZE)
        )
        self.wall = load_sprite_variants(PATHS.tiles, prefix="wall_ice", size=(TILE_SIZE, TILE_SIZE)) or load_sprite_variants(
            PATHS.tiles, prefix="wall_rock", size=(TILE_SIZE, TILE_SIZE)
        )

        self.npcs = [
            Npc("professor", "Professor", x=GRID_WIDTH // 2, y=3),
            Npc("ta_ren", "Ren (TA)", x=GRID_WIDTH // 2 - 4, y=6),
            Npc("ta_lena", "Lena (TA)", x=GRID_WIDTH // 2 + 4, y=6),
            Npc("guild_clerk", "Clerk", x=GRID_WIDTH // 2, y=8),
        ]
        self.npc_sprites = {npc.npc_id: _try_load_npc(npc.npc_id) for npc in self.npcs}

        self.dialogue = DialogueBox()
        self.active_script = None
        self.active_line_index = 0

        # Force mission board to camp while you are here.
        STATE.mission_board = "ice_camp"

    def handle_event(self, event: pygame.event.Event) -> Scene | None:
        if event.type != pygame.KEYDOWN:
            return None

        if event.key == pygame.K_ESCAPE:
            if self.status_open:
                self.status_open = False
                self.app.audio.play_sfx(PATHS.sfx / "ui_close.wav", volume=0.35)
                return None
            if self.active_script is not None:
                self.active_script = None
                self.active_line_index = 0
                return None
            # Leaving camp returns you to town/outskirts; re-enable main guild board.
            STATE.mission_board = "guild"
            from game.scenes.outskirts import OutskirtsScene

            return OutskirtsScene(self.app, spawn=(GRID_WIDTH - 4, GRID_HEIGHT // 2))

        if event.key == pygame.K_i:
            self.status_open = not self.status_open
            self.app.audio.play_sfx(PATHS.sfx / ("ui_open.wav" if self.status_open else "ui_close.wav"), volume=0.35)
            return None

        if self.status_open:
            return None

        if event.key == pygame.K_b:
            from game.scenes.inventory import InventoryScene

            return InventoryScene(self.app, return_scene=self)

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
            return None

        if dx != 0 or dy != 0:
            self._try_move(dx, dy)
        return None

    def update(self, dt: float) -> Scene | None:
        return None

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        _draw_grid(surface, self.grid, floor=self.floor, wall=self.wall, seed=707)

        for npc in self.npcs:
            spr = self.npc_sprites.get(npc.npc_id)
            if spr is not None:
                surface.blit(spr, (npc.x * TILE_SIZE, npc.y * TILE_SIZE))
            else:
                pygame.draw.rect(surface, (200, 160, 220), pygame.Rect(npc.x * TILE_SIZE, npc.y * TILE_SIZE, TILE_SIZE, TILE_SIZE))

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

        hint = "Base Camp: move WASD/arrows  E: talk  I: status  B: inventory  Esc: leave camp"
        if self._interactable_npc() is not None:
            hint = "Base Camp: E to talk"
        surface.blit(self.font.render(hint, True, COLOR_TEXT), (10, 8))

        if self.active_script is not None:
            line = self.active_script.lines[self.active_line_index]
            self.dialogue.draw(surface, speaker=self.active_script.speaker, line=line)

        if self.status_open:
            self.status_menu.draw(surface, STATE)

    def _try_move(self, dx: int, dy: int) -> None:
        nx = self.player.x + dx
        ny = self.player.y + dy
        if any(npc.x == nx and npc.y == ny for npc in self.npcs):
            return
        prev = (self.player.x, self.player.y)
        self.player.try_move(dx, dy, self.grid, walls={TILE_WALL})
        if (self.player.x, self.player.y) != prev:
            if self.player_anim is not None:
                self.player_anim.on_step(dx, dy)
            self.app.audio.play_sfx(PATHS.sfx / "step.wav", volume=0.18)

    def _interactable_npc(self) -> Npc | None:
        for npc in self.npcs:
            if abs(npc.x - self.player.x) + abs(npc.y - self.player.y) <= 1:
                return npc
        return None

    def _try_start_dialogue(self) -> bool:
        npc = self._interactable_npc()
        if npc is None:
            return False
        if npc.npc_id == "guild_clerk":
            from game.scenes.guild import GuildScene

            STATE.mission_board = "ice_camp"
            self.app.audio.play_sfx(PATHS.sfx / "confirm.wav", volume=0.35)
            self.app.set_scene(GuildScene(self.app))
            return True
        script = script_for_npc(npc.npc_id, STATE)
        if script is None:
            return False
        self.active_script = format_dialogue_script(script, STATE)
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


def _layout(width: int, height: int) -> list[list[int]]:
    grid = [[TILE_WALL for _ in range(width)] for _ in range(height)]
    for y in range(2, height - 2):
        for x in range(2, width - 2):
            grid[y][x] = TILE_FLOOR
    # A few tent-like wall chunks
    for x in range(6, width - 6):
        if x % 4 == 0:
            grid[4][x] = TILE_WALL
    return grid


def _draw_grid(surface: pygame.Surface, grid: list[list[int]], *, floor: list[pygame.Surface], wall: list[pygame.Surface], seed: int) -> None:
    for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            if cell == TILE_WALL:
                spr = pick_variant(wall, x=x, y=y, seed=seed)
                if spr is not None:
                    surface.blit(spr, (x * TILE_SIZE, y * TILE_SIZE))
                    continue
                pygame.draw.rect(surface, COLOR_WALL, pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
                continue
            spr = pick_variant(floor, x=x, y=y, seed=seed)
            if spr is not None:
                surface.blit(spr, (x * TILE_SIZE, y * TILE_SIZE))
            else:
                pygame.draw.rect(surface, (40, 40, 44), pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))


def _try_load_npc(npc_id: str) -> pygame.Surface | None:
    return try_load_sprite(PATHS.sprites / "npcs" / f"{npc_id}_down.png", size=(TILE_SIZE, TILE_SIZE))

