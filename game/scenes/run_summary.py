import pygame

from game.constants import COLOR_BG, COLOR_TEXT
from game.scenes.base import Scene


class RunSummaryScene(Scene):
    def __init__(self, app, *, title: str, lines: list[str], next_scene: Scene) -> None:
        super().__init__(app)
        self.title = title
        self.lines = lines
        self.next_scene = next_scene
        self.font_title = pygame.font.SysFont(None, 44)
        self.font = pygame.font.SysFont(None, 26)

    def handle_event(self, event: pygame.event.Event) -> Scene | None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_e, pygame.K_ESCAPE, pygame.K_SPACE):
                return self.next_scene
        return None

    def update(self, dt: float) -> Scene | None:
        return None

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        surface.blit(self.font_title.render(self.title, True, COLOR_TEXT), (40, 50))
        y = 130
        for line in self.lines[:14]:
            surface.blit(self.font.render(line, True, COLOR_TEXT), (40, y))
            y += 30
        hint = self.font.render("Enter/E/Esc: continue", True, (200, 200, 210))
        surface.blit(hint, (40, 440))

