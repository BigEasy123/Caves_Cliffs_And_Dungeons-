import sys

import pygame

from game.constants import FPS, SCREEN_HEIGHT, SCREEN_WIDTH, TITLE
from game.audio import Audio
from game.save import load_state, reset_state, save_state
from game.scenes.base import Scene
from game.scenes.home import HomeBaseScene
from game.scenes.title import TitleScene


class GameApp:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()

        self.audio = Audio()

        self.running = True
        self.scene: Scene = TitleScene(self)

    def set_scene(self, scene: Scene) -> None:
        self.scene = scene

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F5:
                        save_state()
                    elif event.key == pygame.K_F9:
                        if load_state():
                            self.set_scene(HomeBaseScene(self))
                    elif event.key == pygame.K_F8:
                        reset_state()
                        self.set_scene(TitleScene(self))

                next_scene = self.scene.handle_event(event)
                if next_scene is not None:
                    self.set_scene(next_scene)

            next_scene = self.scene.update(dt)
            if next_scene is not None:
                self.set_scene(next_scene)

            self.scene.draw(self.screen)
            pygame.display.flip()

        pygame.quit()
        sys.exit()
