import pygame

from game.assets_manifest import PATHS
from game.constants import COLOR_BG, COLOR_TEXT
from game.scenes.base import Scene
from game.state import STATE
from game.ui.status_menu import StatusMenu


class HealerScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.app.audio.play_music(PATHS.music / "town.ogg", volume=0.45)
        self.font_title = pygame.font.SysFont(None, 42)
        self.font = pygame.font.SysFont(None, 24)
        self.message = ""
        self.status_menu = StatusMenu()
        self.status_open = False

    def handle_event(self, event: pygame.event.Event) -> Scene | None:
        if event.type != pygame.KEYDOWN:
            return None

        if event.key == pygame.K_ESCAPE:
            if self.status_open:
                self.status_open = False
                return None
            from game.scenes.town import TownScene

            return TownScene(self.app)

        if event.key == pygame.K_i:
            self.status_open = not self.status_open
            return None

        if self.status_open:
            return None

        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_e):
            cost = 10
            if STATE.hp >= STATE.max_hp:
                self.message = "You're already at full health."
                return None
            if STATE.gold < cost:
                self.message = "Not enough gold."
                return None
            STATE.gold -= cost
            STATE.hp = STATE.max_hp
            self.message = "All patched up."
        return None

    def update(self, dt: float) -> Scene | None:
        return None

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        title = self.font_title.render("Healer", True, COLOR_TEXT)
        surface.blit(title, (40, 50))

        body = [
            f"HP: {STATE.hp}/{STATE.max_hp}",
            f"Gold: {STATE.gold}",
            "Press Enter/E to heal to full for 10g.",
            "Esc to return to town.",
        ]
        y = 130
        for line in body:
            surf = self.font.render(line, True, COLOR_TEXT)
            surface.blit(surf, (40, y))
            y += 28

        if self.message:
            msg = self.font.render(self.message, True, (220, 190, 120))
            surface.blit(msg, (40, 450))

        if self.status_open:
            self.status_menu.draw(surface, STATE)
