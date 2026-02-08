import pygame

from game.anim import DirectionalStepAnimator
from game.assets import load_sprite_variants, pick_variant, try_load_sprite
from game.assets_manifest import PATHS
from game.constants import (
    COLOR_BG,
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
from game.story.flags import FLAG_RIVAL_KIDNAPPED
from game.story.flags import FLAG_BOW_STOLEN
from game.ui.status_menu import StatusMenu
from game.world.dungeon_run import DungeonRun
from game.save import save_slot


class OutskirtsScene(Scene):
    def __init__(self, app, *, spawn: tuple[int, int] | None = None) -> None:
        super().__init__(app)
        self.font = pygame.font.SysFont(None, 22)
        self.app.audio.play_music(PATHS.music / "world_map.ogg", volume=0.45)
        self.status_menu = StatusMenu()
        self.status_open = False

        self.grid = _layout(GRID_WIDTH, GRID_HEIGHT)
        self.ground = _outskirts_ground(GRID_WIDTH, GRID_HEIGHT)
        sx, sy = spawn if spawn is not None else (3, GRID_HEIGHT // 2)
        from game.entities.player import GridPlayer

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
        self.floor_grass = load_sprite_variants(PATHS.tiles, prefix="floor_grass", size=(TILE_SIZE, TILE_SIZE)) or load_sprite_variants(
            PATHS.tiles, prefix="floor", size=(TILE_SIZE, TILE_SIZE)
        )
        self.floor_gravel = load_sprite_variants(PATHS.tiles, prefix="floor_gravel", size=(TILE_SIZE, TILE_SIZE)) or self.floor_grass
        self.wall_rock = load_sprite_variants(PATHS.tiles, prefix="wall_rock", size=(TILE_SIZE, TILE_SIZE)) or load_sprite_variants(
            PATHS.tiles, prefix="wall", size=(TILE_SIZE, TILE_SIZE)
        )
        self.special_tiles = {
            TILE_EXIT_HOME: try_load_sprite(PATHS.tiles / "door.png", size=(TILE_SIZE, TILE_SIZE)),
            TILE_DUNGEON_TEMPLE: try_load_sprite(PATHS.tiles / "temple.png", size=(TILE_SIZE, TILE_SIZE)),
        }
        self.visual_seed = 303

        self.message = ""
        self.dungeon_menu_open = False
        self.dungeon_menu_index = 0

    def handle_event(self, event: pygame.event.Event) -> Scene | None:
        if event.type != pygame.KEYDOWN:
            return None

        if event.key == pygame.K_ESCAPE:
            if self.status_open:
                self.status_open = False
                self.app.audio.play_sfx(PATHS.sfx / "ui_close.wav", volume=0.35)
                return None
            from game.scenes.title import TitleScene

            return TitleScene(self.app)

        if event.key == pygame.K_i:
            self.status_open = not self.status_open
            self.app.audio.play_sfx(
                PATHS.sfx / ("ui_open.wav" if self.status_open else "ui_close.wav"),
                volume=0.35,
            )
            return None

        if self.status_open:
            return None

        if event.key == pygame.K_b:
            from game.scenes.inventory import InventoryScene

            return InventoryScene(self.app, return_scene=self)

        if self.dungeon_menu_open:
            return self._handle_dungeon_menu_keys(event)

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
            next_scene = self._try_move(dx, dy)
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
            floor_grass=self.floor_grass,
            floor_gravel=self.floor_gravel,
            wall_variants=self.wall_rock,
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
            "Outskirts: move WASD/arrows  Walk onto gate/exit  I: status  B: inventory  Esc: title",
            True,
            COLOR_TEXT,
        )
        surface.blit(hud, (10, 8))

        if self.message:
            msg = self.font.render(self.message, True, (220, 190, 120))
            surface.blit(msg, (10, 32))

        if self.dungeon_menu_open:
            self._draw_dungeon_menu(surface)

        if self.status_open:
            self.status_menu.draw(surface, STATE)

    def _try_move(self, dx: int, dy: int) -> Scene | None:
        prev = (self.player.x, self.player.y)
        self.player.try_move(dx, dy, self.grid, walls={TILE_WALL})
        if (self.player.x, self.player.y) != prev:
            if self.player_anim is not None:
                self.player_anim.on_step(dx, dy)
            self.app.audio.play_sfx(PATHS.sfx / "step.wav", volume=0.18)
        tile = self.grid[self.player.y][self.player.x]
        if tile == TILE_EXIT_HOME:
            from game.scenes.town import TownScene

            return TownScene(self.app, spawn=(GRID_WIDTH - 3, GRID_HEIGHT // 2))
        if tile == TILE_DUNGEON_TEMPLE:
            self.dungeon_menu_open = True
            self.dungeon_menu_index = 0
            self.message = ""
            self.app.audio.play_sfx(PATHS.sfx / "ui_open.wav", volume=0.35)
            return None
        self.message = ""
        return None

    def _dungeon_options(self) -> list[dict]:
        return [
            {
                "name": "Temple Ruins",
                "dungeon_id": "temple_ruins",
                "max_floor": 5,
                "locked": (not STATE.has(FLAG_GOT_TEMPLE_PASS)),
                "lock_reason": "Talk to the Mayor in town to get the pass.",
            },
            {
                "name": "Jungle Cavern",
                "dungeon_id": "jungle_cavern",
                "max_floor": 7,
                "locked": ("relic_shard" not in STATE.completed_missions),
                "lock_reason": "Complete a guild mission to unlock.",
            },
            {
                "name": "Nephil Dunes",
                "dungeon_id": "nephil_dunes",
                "max_floor": 4,
                "locked": (STATE.chapter < 2),
                "lock_reason": "Reach Chapter 2 (Guild Rank 2) to unlock.",
            },
            {
                "name": "Nephil Oasis Ruins",
                "dungeon_id": "nephil_oasis",
                "max_floor": 5,
                "locked": (STATE.chapter < 2),
                "lock_reason": "Reach Chapter 2 (Guild Rank 2) to unlock.",
            },
            {
                "name": "Nephil Sunken Tomb",
                "dungeon_id": "nephil_tomb",
                "max_floor": 6,
                "locked": (STATE.chapter < 2 or "nephil_relic_ankh" not in STATE.completed_missions or "nephil_relic_map" not in STATE.completed_missions),
                "lock_reason": "Complete the first two Nephil relic missions to unlock.",
            },
            {
                "name": "Collapsed Mines",
                "dungeon_id": "collapsed_mines",
                "max_floor": 6,
                "locked": (STATE.chapter < 3),
                "lock_reason": "Reach Chapter 3 (Guild Rank 3) to unlock.",
            },
            {
                "name": "Deepest Shaft",
                "dungeon_id": "deep_shaft",
                "max_floor": 8,
                "locked": (STATE.chapter < 3 or STATE.rescued_miners_total < 10),
                "lock_reason": "Rescue more miners from the Collapsed Mines to unlock.",
            },
            {
                "name": "Children Hideout",
                "dungeon_id": "children_hideout",
                "max_floor": 5,
                "locked": (STATE.chapter < 4 or not STATE.has(FLAG_RIVAL_KIDNAPPED)),
                "lock_reason": "Accept the Rivalry mission to reveal the hideout.",
            },
            {
                "name": "Tower of Babel",
                "dungeon_id": "babel_tower",
                "max_floor": 9,
                "locked": (STATE.chapter < 5),
                "lock_reason": "Reach Chapter 5 (Guild Rank 5) to unlock.",
            },
            {
                "name": "Children Vault",
                "dungeon_id": "children_vault",
                "max_floor": 6,
                "locked": (STATE.chapter < 6 or not STATE.has(FLAG_BOW_STOLEN)),
                "lock_reason": "After the bow is stolen (Chapter 6), the vault becomes accessible.",
            },
        ]

    def _handle_dungeon_menu_keys(self, event: pygame.event.Event) -> Scene | None:
        if event.key == pygame.K_ESCAPE:
            self.dungeon_menu_open = False
            self.app.audio.play_sfx(PATHS.sfx / "ui_close.wav", volume=0.35)
            return None

        options = self._dungeon_options()
        if not options:
            return None

        if event.key in (pygame.K_UP, pygame.K_w):
            self.dungeon_menu_index = (self.dungeon_menu_index - 1) % len(options)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.dungeon_menu_index = (self.dungeon_menu_index + 1) % len(options)
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_e):
            opt = options[self.dungeon_menu_index]
            if opt["locked"]:
                self.message = f"Locked: {opt['lock_reason']}"
                self.dungeon_menu_open = False
                self.app.audio.play_sfx(PATHS.sfx / "error.wav", volume=0.40)
                return None

            from game.scenes.dungeon import DungeonScene

            run = DungeonRun(dungeon_id=opt["dungeon_id"], dungeon_name=opt["name"], max_floor=opt["max_floor"])
            self.dungeon_menu_open = False
            self.app.audio.play_sfx(PATHS.sfx / "confirm.wav", volume=0.35)
            save_slot(1)
            self.app.toast("Autosaved (slot 1)")
            return DungeonScene(self.app, run, return_to="outskirts")
        return None

    def _draw_dungeon_menu(self, surface: pygame.Surface) -> None:
        width, height = surface.get_size()
        rect = pygame.Rect(60, 80, width - 120, height - 160)

        overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        surface.blit(overlay, rect.topleft)
        pygame.draw.rect(surface, (255, 255, 255), rect, 2)

        title = self.font.render("Choose a Dungeon (Up/Down, Enter/E, Esc)", True, COLOR_TEXT)
        surface.blit(title, (rect.left + 14, rect.top + 14))

        options = self._dungeon_options()
        y = rect.top + 54
        for idx, opt in enumerate(options):
            prefix = "> " if idx == self.dungeon_menu_index else "  "
            locked = " (LOCKED)" if opt["locked"] else ""
            line = self.font.render(f"{prefix}{opt['name']}{locked}", True, COLOR_TEXT)
            surface.blit(line, (rect.left + 14, y))
            y += 28

        if options:
            opt = options[self.dungeon_menu_index]
            info = opt["lock_reason"] if opt["locked"] else f"Floors: 1-{opt['max_floor']}"
            hint = self.font.render(info, True, (200, 200, 210))
            surface.blit(hint, (rect.left + 14, rect.bottom - 18 - hint.get_height()))


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

    # Single dungeon gate on the right
    grid[height // 2][width - 6] = TILE_DUNGEON_TEMPLE
    return grid


def _draw_grid(
    surface: pygame.Surface,
    grid: list[list[int]],
    ground: list[list[str]],
    *,
    floor_grass: list[pygame.Surface],
    floor_gravel: list[pygame.Surface],
    wall_variants: list[pygame.Surface],
    special_tiles: dict[int, pygame.Surface | None],
    seed: int,
) -> None:
    for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            if cell == TILE_FLOOR:
                variants = floor_grass if ground[y][x] == "grass" else floor_gravel
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
            elif cell == TILE_EXIT_HOME:
                color = COLOR_EXIT
            elif cell == TILE_DUNGEON_TEMPLE:
                color = COLOR_DUNGEON_TEMPLE
            else:
                color = COLOR_FLOOR
            pygame.draw.rect(surface, color, pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))

def _outskirts_ground(width: int, height: int) -> list[list[str]]:
    ground = [["grass" for _ in range(width)] for _ in range(height)]
    # Gravel-ish road down the middle
    cx = width // 2
    for y in range(1, height - 1):
        ground[y][cx] = "gravel"
        if cx - 1 >= 0:
            ground[y][cx - 1] = "gravel"
        if cx + 1 < width:
            ground[y][cx + 1] = "gravel"
    return ground

def _adjacent_tile(grid: list[list[int]], x: int, y: int) -> int | None:
    for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
        nx, ny = x + dx, y + dy
        if 0 <= ny < len(grid) and 0 <= nx < len(grid[0]):
            cell = grid[ny][nx]
            if cell != TILE_FLOOR and cell != TILE_WALL:
                return cell
    return None
