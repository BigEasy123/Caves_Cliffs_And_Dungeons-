import sys

import pygame


SCREEN_WIDTH = 800
SCREEN_HEIGHT = 450
FPS = 60
TILE_SIZE = 40

GRAVITY = 1800
PLAYER_SPEED = 240
JUMP_VELOCITY = -600


class Player:
    def __init__(self, x, y, width=32, height=48):
        self.rect = pygame.Rect(x, y, width, height)
        self.velocity_x = 0
        self.velocity_y = 0
        self.on_ground = False

    def handle_input(self, keys):
        self.velocity_x = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.velocity_x = -PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.velocity_x = PLAYER_SPEED

        if (keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]) and self.on_ground:
            self.velocity_y = JUMP_VELOCITY
            self.on_ground = False

    def apply_gravity(self, dt):
        self.velocity_y += GRAVITY * dt

    def move_and_collide(self, dt, solids):
        self.rect.x += int(self.velocity_x * dt)
        self.resolve_collisions(solids, axis="x")

        self.rect.y += int(self.velocity_y * dt)
        self.on_ground = False
        self.resolve_collisions(solids, axis="y")

    def resolve_collisions(self, solids, axis):
        for solid in solids:
            if self.rect.colliderect(solid):
                if axis == "x":
                    if self.velocity_x > 0:
                        self.rect.right = solid.left
                    elif self.velocity_x < 0:
                        self.rect.left = solid.right
                else:
                    if self.velocity_y > 0:
                        self.rect.bottom = solid.top
                        self.velocity_y = 0
                        self.on_ground = True
                    elif self.velocity_y < 0:
                        self.rect.top = solid.bottom
                        self.velocity_y = 0

    def draw(self, surface):
        pygame.draw.rect(surface, (255, 255, 255), self.rect)


class Level:
    def __init__(self):
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
        self.solids = self.build_solids()

    def build_solids(self):
        solids = []
        for row_index, row in enumerate(self.map_data):
            for col_index, cell in enumerate(row):
                if cell == "#":
                    solids.append(
                        pygame.Rect(
                            col_index * TILE_SIZE,
                            row_index * TILE_SIZE,
                            TILE_SIZE,
                            TILE_SIZE,
                        )
                    )
        return solids

    def draw(self, surface):
        for solid in self.solids:
            pygame.draw.rect(surface, (80, 90, 100), solid)


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Caves, Cliffs, and Dungeons! - Prototype")
        self.clock = pygame.time.Clock()
        self.running = True

        self.level = Level()
        self.player = Player(80, 40)

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            self.handle_events()
            self.update(dt)
            self.draw()

        pygame.quit()
        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)
        self.player.apply_gravity(dt)
        self.player.move_and_collide(dt, self.level.solids)

    def draw(self):
        self.screen.fill((15, 18, 24))
        self.level.draw(self.screen)
        self.player.draw(self.screen)
        pygame.display.flip()


if __name__ == "__main__":
    Game().run() put this as the main.py