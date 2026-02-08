import pygame

from game.anim import DirectionalStepAnimator
from game.assets import load_sprite_variants, pick_variant, try_load_sprite
from game.assets_manifest import PATHS
from game.constants import (
    COLOR_BG,
    COLOR_DOOR,
    COLOR_BED,
    COLOR_FLOOR,
    COLOR_PLAYER,
    COLOR_TEXT,
    COLOR_WALL,
    GRID_HEIGHT,
    GRID_WIDTH,
    TILE_BED_BL,
    TILE_BED_BR,
    TILE_BED_TL,
    TILE_BED_TR,
    TILE_DOOR,
    TILE_FLOOR,
    TILE_SIZE,
    TILE_WALL,
)
from game.entities.player import GridPlayer
from game.save import save_slot
from game.scenes.base import Scene
from game.state import STATE
from game.ui.status_menu import StatusMenu


class HomeBaseScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.font = pygame.font.SysFont(None, 22)
        self.app.audio.play_music(PATHS.music / "home.ogg", volume=0.45)
        self.status_menu = StatusMenu()
        self.status_open = False

        self.grid = _home_layout(GRID_WIDTH, GRID_HEIGHT)
        self.player = GridPlayer(4, 6)
        self.player_idle = {
            "down": try_load_sprite(PATHS.sprites / "player_down.png", size=(TILE_SIZE, TILE_SIZE)),
            "up": try_load_sprite(PATHS.sprites / "player_up.png", size=(TILE_SIZE, TILE_SIZE)),
            "left": try_load_sprite(PATHS.sprites / "player_left.png", size=(TILE_SIZE, TILE_SIZE)),
            "right": try_load_sprite(PATHS.sprites / "player_right.png", size=(TILE_SIZE, TILE_SIZE)),
        }
        self.player_walk = {
            "down": [
                try_load_sprite(PATHS.sprites / f"player_walk{i}_down.png", size=(TILE_SIZE, TILE_SIZE)) for i in range(3)
            ],
            "up": [try_load_sprite(PATHS.sprites / f"player_walk{i}_up.png", size=(TILE_SIZE, TILE_SIZE)) for i in range(3)],
            "left": [
                try_load_sprite(PATHS.sprites / f"player_walk{i}_left.png", size=(TILE_SIZE, TILE_SIZE)) for i in range(3)
            ],
            "right": [
                try_load_sprite(PATHS.sprites / f"player_walk{i}_right.png", size=(TILE_SIZE, TILE_SIZE)) for i in range(3)
            ],
        }
        # Back-compat (older single-file sprite)
        self.player_sprite = try_load_sprite(PATHS.sprites / "player.png", size=(TILE_SIZE, TILE_SIZE))
        if not any(self.player_idle.values()):
            # Use legacy sprite if directional idles are missing.
            self.player_idle["down"] = self.player_sprite
        frames_by_dir = {}
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
        self.floor_variants = (
            load_sprite_variants(PATHS.tiles, prefix="floor_gravel", size=(TILE_SIZE, TILE_SIZE))
            or load_sprite_variants(PATHS.tiles, prefix="floor", size=(TILE_SIZE, TILE_SIZE))
        )
        self.wall_variants = (
            load_sprite_variants(PATHS.tiles, prefix="wall_rock", size=(TILE_SIZE, TILE_SIZE))
            or load_sprite_variants(PATHS.tiles, prefix="wall", size=(TILE_SIZE, TILE_SIZE))
        )
        self.special_tiles = {
            TILE_DOOR: try_load_sprite(PATHS.tiles / "door.png", size=(TILE_SIZE, TILE_SIZE)),
            TILE_BED_TL: try_load_sprite(PATHS.tiles / "bed_tl.png", size=(TILE_SIZE, TILE_SIZE)),
            TILE_BED_TR: try_load_sprite(PATHS.tiles / "bed_tr.png", size=(TILE_SIZE, TILE_SIZE)),
            TILE_BED_BL: try_load_sprite(PATHS.tiles / "bed_bl.png", size=(TILE_SIZE, TILE_SIZE)),
            TILE_BED_BR: try_load_sprite(PATHS.tiles / "bed_br.png", size=(TILE_SIZE, TILE_SIZE)),
        }
        self.visual_seed = 101
        self._last_pos = (self.player.x, self.player.y)

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

        if event.key == pygame.K_b:
            from game.scenes.inventory import InventoryScene

            return InventoryScene(self.app, return_scene=self)

        dx, dy = 0, 0
        if event.key in (pygame.K_LEFT, pygame.K_a):
            dx = -1
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            dx = 1
        elif event.key in (pygame.K_UP, pygame.K_w):
            dy = -1
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            dy = 1

        if dx != 0 or dy != 0:
            prev = (self.player.x, self.player.y)
            self.player.try_move(dx, dy, self.grid, walls={TILE_WALL})
            if (self.player.x, self.player.y) != prev:
                if self.player_anim is not None:
                    self.player_anim.on_step(dx, dy)
                tile = self.grid[self.player.y][self.player.x]
                if tile == TILE_DOOR:
                    from game.scenes.town import TownScene

                    return TownScene(self.app, spawn=(2, GRID_HEIGHT // 2))
                if tile in (TILE_BED_TL, TILE_BED_TR, TILE_BED_BL, TILE_BED_BR):
                    save_slot(1)
                    self.app.toast("Saved at bed (slot 1)")
                    self.app.audio.play_sfx(PATHS.sfx / "confirm.wav", volume=0.35)
            self._last_pos = (self.player.x, self.player.y)
        return None

    def update(self, dt: float) -> Scene | None:
        return None

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        _draw_grid(
            surface,
            self.grid,
            floor_variants=self.floor_variants,
            wall_variants=self.wall_variants,
            special_tiles=self.special_tiles,
            seed=self.visual_seed,
        )

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

        hud = self.font.render(
            "Home Base: move WASD/arrows  Walk onto door to exit  Walk onto bed to save  I: status  B: inventory  Esc: title",
            True,
            COLOR_TEXT,
        )
        surface.blit(hud, (10, 8))

        if self.status_open:
            self.status_menu.draw(surface, STATE)


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

    # Bed (save point) - 2x2 (four tiles for nicer look)
    bed_x = ox + 2
    bed_y = oy + 2
    grid[bed_y][bed_x] = TILE_BED_TL
    grid[bed_y][bed_x + 1] = TILE_BED_TR
    grid[bed_y + 1][bed_x] = TILE_BED_BL
    grid[bed_y + 1][bed_x + 1] = TILE_BED_BR
    return grid


def _draw_grid(
    surface: pygame.Surface,
    grid: list[list[int]],
    *,
    floor_variants: list[pygame.Surface],
    wall_variants: list[pygame.Surface],
    special_tiles: dict[int, pygame.Surface | None],
    seed: int,
) -> None:
    for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            if cell == TILE_FLOOR:
                sprite = pick_variant(floor_variants, x=x, y=y, seed=seed)
                if sprite is not None:
                    surface.blit(sprite, (x * TILE_SIZE, y * TILE_SIZE))
                    continue
            if cell == TILE_WALL:
                sprite = pick_variant(wall_variants, x=x, y=y, seed=seed)
                if sprite is not None:
                    surface.blit(sprite, (x * TILE_SIZE, y * TILE_SIZE))
                    continue
            sprite = special_tiles.get(cell)
            if sprite is not None:
                surface.blit(sprite, (x * TILE_SIZE, y * TILE_SIZE))
                continue
            if cell == TILE_WALL:
                color = COLOR_WALL
            elif cell == TILE_DOOR:
                color = COLOR_DOOR
            elif cell in (TILE_BED_TL, TILE_BED_TR, TILE_BED_BL, TILE_BED_BR):
                color = COLOR_BED
            else:
                color = COLOR_FLOOR
            pygame.draw.rect(surface, color, pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))


def _is_on_or_adjacent(grid: list[list[int]], x: int, y: int, tile: int) -> bool:
    # Kept for future interactions; exits are collision-based now.
    if grid[y][x] == tile:
        return True
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nx, ny = x + dx, y + dy
        if 0 <= ny < len(grid) and 0 <= nx < len(grid[0]) and grid[ny][nx] == tile:
            return True
    return False
