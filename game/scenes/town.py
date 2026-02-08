from pathlib import Path

import pygame

from game.anim import DirectionalStepAnimator
from game.assets import load_sprite_variants, pick_variant, try_load_sprite
from game.assets_manifest import PATHS
from game.constants import (
    COLOR_BG,
    COLOR_DOOR,
    COLOR_EXIT,
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
    TILE_EXIT_HOME,
    TILE_EXIT_OUTSKIRTS,
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
    def __init__(self, app, *, spawn: tuple[int, int] | None = None) -> None:
        super().__init__(app)
        self.font = pygame.font.SysFont(None, 22)
        self.app.audio.play_music(PATHS.music / "town.ogg", volume=0.45)

        self.grid = _town_layout(GRID_WIDTH, GRID_HEIGHT)
        self.ground = _town_ground(GRID_WIDTH, GRID_HEIGHT)
        sx, sy = spawn if spawn is not None else (12, 10)
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
        self.floor_stone = load_sprite_variants(PATHS.tiles, prefix="floor_stone", size=(TILE_SIZE, TILE_SIZE)) or load_sprite_variants(
            PATHS.tiles, prefix="floor", size=(TILE_SIZE, TILE_SIZE)
        )
        self.floor_grass = load_sprite_variants(PATHS.tiles, prefix="floor_grass", size=(TILE_SIZE, TILE_SIZE)) or self.floor_stone
        self.floor_gravel = load_sprite_variants(PATHS.tiles, prefix="floor_gravel", size=(TILE_SIZE, TILE_SIZE)) or self.floor_stone
        self.wall_rock = load_sprite_variants(PATHS.tiles, prefix="wall_rock", size=(TILE_SIZE, TILE_SIZE)) or load_sprite_variants(
            PATHS.tiles, prefix="wall", size=(TILE_SIZE, TILE_SIZE)
        )
        self.special_tiles = {
            TILE_EXIT_HOME: try_load_sprite(PATHS.tiles / "door.png", size=(TILE_SIZE, TILE_SIZE)),
            TILE_EXIT_OUTSKIRTS: try_load_sprite(PATHS.tiles / "door.png", size=(TILE_SIZE, TILE_SIZE)),
            TILE_SHOP_DOOR: try_load_sprite(PATHS.tiles / "shop.png", size=(TILE_SIZE, TILE_SIZE)),
            TILE_GUILD_DOOR: try_load_sprite(PATHS.tiles / "guild.png", size=(TILE_SIZE, TILE_SIZE)),
            TILE_HEALER_DOOR: try_load_sprite(PATHS.tiles / "healer.png", size=(TILE_SIZE, TILE_SIZE)),
        }
        self.visual_seed = 202

        self.npcs = [
            Npc("mayor", "Mayor", x=7, y=4),
            Npc("archivist", "Archivist", x=12, y=8),
        ]
        self.npc_sprites = {
            "mayor": _try_load_npc(PATHS.sprites / "npcs", "mayor", size=(TILE_SIZE, TILE_SIZE)),
            "archivist": _try_load_npc(PATHS.sprites / "npcs", "archivist", size=(TILE_SIZE, TILE_SIZE)),
        }
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
            next_scene = self._try_move_player(dx, dy)
            if next_scene is not None:
                return next_scene
        return None

    def update(self, dt: float) -> Scene | None:
        return None

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        _draw_grid(
            surface,
            self.grid,
            self.ground,
            floor_stone=self.floor_stone,
            floor_grass=self.floor_grass,
            floor_gravel=self.floor_gravel,
            wall_variants=self.wall_rock,
            special_tiles=self.special_tiles,
            seed=self.visual_seed,
        )

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

        hint = "Town: move WASD/arrows  E: talk/enter  Walk onto exits  I: status  B: inventory  Esc: title"
        if self._interactable_npc() is not None:
            hint = "Town: E to talk"
        elif _adjacent_tile(
            self.grid,
            self.player.x,
            self.player.y,
            {TILE_SHOP_DOOR, TILE_GUILD_DOOR, TILE_HEALER_DOOR},
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

    def _try_move_player(self, dx: int, dy: int) -> Scene | None:
        nx = self.player.x + dx
        ny = self.player.y + dy
        if any(npc.x == nx and npc.y == ny for npc in self.npcs):
            return None
        prev = (self.player.x, self.player.y)
        self.player.try_move(dx, dy, self.grid, walls={TILE_WALL})
        if (self.player.x, self.player.y) != prev and self.player_anim is not None:
            self.player_anim.on_step(dx, dy)
        tile = self.grid[self.player.y][self.player.x]
        if tile == TILE_SHOP_DOOR:
            from game.scenes.shop import ShopScene

            return ShopScene(self.app)
        if tile == TILE_GUILD_DOOR:
            from game.scenes.guild_hall import GuildHallScene

            return GuildHallScene(self.app, spawn=(GRID_WIDTH // 2, GRID_HEIGHT - 4))
        if tile == TILE_HEALER_DOOR:
            from game.scenes.healer import HealerScene

            return HealerScene(self.app)
        if tile == TILE_EXIT_HOME:
            from game.scenes.home import HomeBaseScene

            return HomeBaseScene(self.app)
        if tile == TILE_EXIT_OUTSKIRTS:
            from game.scenes.outskirts import OutskirtsScene

            return OutskirtsScene(self.app, spawn=(3, GRID_HEIGHT // 2))
        return None


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

    # Exits: west to Home Base, east to Outskirts (dungeon entrances)
    grid[height // 2][1] = TILE_EXIT_HOME
    grid[height // 2][width - 2] = TILE_EXIT_OUTSKIRTS
    return grid


def _draw_grid(
    surface: pygame.Surface,
    grid: list[list[int]],
    ground: list[list[str]],
    *,
    floor_stone: list[pygame.Surface],
    floor_grass: list[pygame.Surface],
    floor_gravel: list[pygame.Surface],
    wall_variants: list[pygame.Surface],
    special_tiles: dict[int, pygame.Surface | None],
    seed: int,
) -> None:
    for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            if cell == TILE_FLOOR:
                theme = ground[y][x]
                variants = floor_stone if theme == "stone" else (floor_grass if theme == "grass" else floor_gravel)
                sprite = pick_variant(variants, x=x, y=y, seed=seed)
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
            elif cell in (TILE_EXIT_HOME, TILE_EXIT_OUTSKIRTS):
                color = COLOR_EXIT
            elif cell == TILE_SHOP_DOOR:
                color = COLOR_SHOP
            elif cell == TILE_GUILD_DOOR:
                color = COLOR_GUILD
            elif cell == TILE_HEALER_DOOR:
                color = COLOR_HEALER
            else:
                color = COLOR_FLOOR
            pygame.draw.rect(surface, color, pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))


def _town_ground(width: int, height: int) -> list[list[str]]:
    """
    Per-tile ground theme for visuals only: 'stone' | 'grass' | 'gravel'
    """
    ground = [["stone" for _ in range(width)] for _ in range(height)]

    # Gravel roads: main east-west + spurs to buildings/exits
    def paint_road(x1: int, y1: int, x2: int, y2: int, width_px: int = 1) -> None:
        if x1 == x2:
            y_start, y_end = (y1, y2) if y1 <= y2 else (y2, y1)
            for y in range(y_start, y_end + 1):
                for w in range(-width_px, width_px + 1):
                    xx = x1 + w
                    if 0 <= xx < width and 0 <= y < height:
                        ground[y][xx] = "gravel"
        elif y1 == y2:
            x_start, x_end = (x1, x2) if x1 <= x2 else (x2, x1)
            for x in range(x_start, x_end + 1):
                for w in range(-width_px, width_px + 1):
                    yy = y1 + w
                    if 0 <= x < width and 0 <= yy < height:
                        ground[yy][x] = "gravel"

    mid_y = height // 2
    paint_road(1, mid_y, width - 2, mid_y, width_px=1)

    # Spurs: to exits
    paint_road(1, mid_y, 1, mid_y, width_px=1)
    paint_road(width - 2, mid_y, width - 2, mid_y, width_px=1)

    # Spurs to building doors (approx positions)
    # Shop door at (18,6), Guild door at (6,12), Healer door at (17,12)
    paint_road(18, mid_y, 18, 6, width_px=1)
    paint_road(6, mid_y, 6, 12, width_px=1)
    paint_road(17, mid_y, 17, 12, width_px=1)
    paint_road(7, mid_y, 7, 6, width_px=1)  # mayor office opening vicinity

    # Grass patches in corners
    for yy in range(1, 6):
        for xx in range(1, 7):
            ground[yy][xx] = "grass"
            ground[height - 1 - yy][width - 1 - xx] = "grass"

    return ground


def _try_load_npc(npcs_dir, npc_id: str, *, size: tuple[int, int]) -> pygame.Surface | None:
    # Default to facing down idle
    return try_load_sprite(Path(npcs_dir) / f"{npc_id}_down.png", size=size)


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
