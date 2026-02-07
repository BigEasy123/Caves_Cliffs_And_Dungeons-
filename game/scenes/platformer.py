import pygame

from game.constants import COLOR_BG
from game.scenes.base import Scene
from game.scenes.title import TitleScene


TILE_SIZE = 40
GRAVITY = 1800
PLAYER_SPEED = 240
JUMP_VELOCITY = -600


class Player:
    def __init__(self, x: int, y: int, width: int = 32, height: int = 48) -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.on_ground = False

    def handle_input(self, keys) -> None:
        self.velocity_x = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.velocity_x = -PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.velocity_x = PLAYER_SPEED

        if (keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]) and self.on_ground:
            self.velocity_y = JUMP_VELOCITY
            self.on_ground = False

    def apply_gravity(self, dt: float) -> None:
        self.velocity_y += GRAVITY * dt

    def move_and_collide(self, dt: float, solids: list[pygame.Rect]) -> None:
        self.rect.x += int(self.velocity_x * dt)
        self._resolve(solids, axis="x")

        self.rect.y += int(self.velocity_y * dt)
        self.on_ground = False
        self._resolve(solids, axis="y")

    def _resolve(self, solids: list[pygame.Rect], *, axis: str) -> None:
        for solid in solids:
            if not self.rect.colliderect(solid):
                continue
            if axis == "x":
                if self.velocity_x > 0:
                    self.rect.right = solid.left
                elif self.velocity_x < 0:
                    self.rect.left = solid.right
            else:
                if self.velocity_y > 0:
                    self.rect.bottom = solid.top
                    self.velocity_y = 0.0
                    self.on_ground = True
                elif self.velocity_y < 0:
                    self.rect.top = solid.bottom
                    self.velocity_y = 0.0

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, (255, 255, 255), self.rect)


class Level:
    def __init__(self) -> None:
        self.map_data = [
            "........................",
            "........................",
            "........................",
            "...............####.....",
            "........................",
            "...........####.........",
            "........................",
            ".....####...............",
            "........................",
            "########################",
        ]
        self.solids = self._build_solids()

    def _build_solids(self) -> list[pygame.Rect]:
        solids: list[pygame.Rect] = []
        for row_index, row in enumerate(self.map_data):
            for col_index, cell in enumerate(row):
                if cell != "#":
                    continue
                solids.append(
                    pygame.Rect(
                        col_index * TILE_SIZE,
                        row_index * TILE_SIZE,
                        TILE_SIZE,
                        TILE_SIZE,
                    )
                )
        return solids

    def draw(self, surface: pygame.Surface) -> None:
        for solid in self.solids:
            pygame.draw.rect(surface, (80, 90, 100), solid)


class PlatformerScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.level = Level()
        self.player = Player(80, 40)

    def handle_event(self, event: pygame.event.Event) -> Scene | None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return TitleScene(self.app)
        return None

    def update(self, dt: float) -> Scene | None:
        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)
        self.player.apply_gravity(dt)
        self.player.move_and_collide(dt, self.level.solids)
        return None

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        self.level.draw(surface)
        self.player.draw(surface)
