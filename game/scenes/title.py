import pygame

from game.constants import COLOR_BG, COLOR_TEXT, TITLE
from game.scenes.base import Scene


class TitleScene(Scene):
    def __init__(self) -> None:
        self.font_title = pygame.font.SysFont(None, 56)
        self.font_body = pygame.font.SysFont(None, 26)

    def handle_event(self, event: pygame.event.Event) -> Scene | None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                from game.scenes.dungeon import DungeonScene

                return DungeonScene()
            if event.key == pygame.K_p:
                from game.scenes.platformer import PlatformerScene

                return PlatformerScene()
            if event.key == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
        return None

    def update(self, dt: float) -> Scene | None:
        return None

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)

        title_surf = self.font_title.render(TITLE, True, COLOR_TEXT)
        body1 = self.font_body.render("Enter: Start Dungeon (turn-based)", True, COLOR_TEXT)
        body2 = self.font_body.render("P: Play platformer prototype", True, COLOR_TEXT)
        body3 = self.font_body.render("Esc: Quit", True, COLOR_TEXT)

        surface.blit(title_surf, (40, 70))
        surface.blit(body1, (40, 170))
        surface.blit(body2, (40, 205))
        surface.blit(body3, (40, 240))
