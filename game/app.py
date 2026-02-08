import sys

import pygame

from game.constants import FPS, SCREEN_HEIGHT, SCREEN_WIDTH, TITLE
from game.audio import Audio
from game.save import load_slot, reset_state, save_slot
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

        self.toast_text = ""
        self.toast_time_left = 0.0

        self.running = True
        self.scene: Scene = TitleScene(self)

    def set_scene(self, scene: Scene) -> None:
        self.scene = scene

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            if self.toast_time_left > 0:
                self.toast_time_left = max(0.0, self.toast_time_left - dt)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F5:
                        save_slot(1)
                        self.toast("Saved (slot 1)")
                    elif event.key == pygame.K_F6:
                        save_slot(2)
                        self.toast("Saved (slot 2)")
                    elif event.key == pygame.K_F7:
                        save_slot(3)
                        self.toast("Saved (slot 3)")
                    elif event.key == pygame.K_F9:
                        if load_slot(1):
                            self.set_scene(HomeBaseScene(self))
                            self.toast("Loaded (slot 1)")
                        else:
                            self.toast("No save in slot 1")
                    elif event.key == pygame.K_F10:
                        if load_slot(2):
                            self.set_scene(HomeBaseScene(self))
                            self.toast("Loaded (slot 2)")
                        else:
                            self.toast("No save in slot 2")
                    elif event.key == pygame.K_F11:
                        if load_slot(3):
                            self.set_scene(HomeBaseScene(self))
                            self.toast("Loaded (slot 3)")
                        else:
                            self.toast("No save in slot 3")
                    elif event.key == pygame.K_F8:
                        reset_state()
                        self.set_scene(TitleScene(self))
                        self.toast("Reset state")

                next_scene = self.scene.handle_event(event)
                if next_scene is not None:
                    self.set_scene(next_scene)

            next_scene = self.scene.update(dt)
            if next_scene is not None:
                self.set_scene(next_scene)

            self.scene.draw(self.screen)
            self.draw_toast(self.screen)
            pygame.display.flip()

        pygame.quit()
        sys.exit()

    def toast(self, text: str, *, seconds: float = 2.0) -> None:
        self.toast_text = text
        self.toast_time_left = seconds

    def draw_toast(self, surface: pygame.Surface) -> None:
        if self.toast_time_left <= 0 or not self.toast_text:
            return
        font = pygame.font.SysFont(None, 24)
        text_surf = font.render(self.toast_text, True, (245, 245, 245))
        padding = 10
        rect = text_surf.get_rect()
        rect.topleft = (10, SCREEN_HEIGHT - rect.height - 10)
        bg = pygame.Surface((rect.width + padding * 2, rect.height + padding * 2), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 180))
        surface.blit(bg, (rect.left - padding, rect.top - padding))
        surface.blit(text_surf, rect.topleft)
