import pygame

from game.assets_manifest import PATHS
from game.constants import COLOR_BG, COLOR_TEXT
from game.scenes.base import Scene
from game.state import STATE
from game.story.missions import MISSIONS


class GuildScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.app.audio.play_music(PATHS.music / "town.ogg", volume=0.45)
        self.font_title = pygame.font.SysFont(None, 42)
        self.font = pygame.font.SysFont(None, 24)
        self.index = 0
        self.message = ""

    def handle_event(self, event: pygame.event.Event) -> Scene | None:
        if event.type != pygame.KEYDOWN:
            return None

        if event.key == pygame.K_ESCAPE:
            from game.scenes.town import TownScene

            return TownScene(self.app)

        missions = self._available_missions()
        if not missions:
            return None

        if event.key in (pygame.K_UP, pygame.K_w):
            self.index = (self.index - 1) % len(missions)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.index = (self.index + 1) % len(missions)
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_e):
            mission_id = missions[self.index]
            STATE.active_mission = mission_id
            self.message = f"Accepted mission: {MISSIONS[mission_id].name}"
        return None

    def update(self, dt: float) -> Scene | None:
        return None

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        title = self.font_title.render("Guild", True, COLOR_TEXT)
        surface.blit(title, (40, 50))

        header = self.font.render("Up/Down select  Enter/E accept  Esc back", True, COLOR_TEXT)
        surface.blit(header, (40, 95))

        y = 135
        missions = self._available_missions()
        if not missions:
            none = self.font.render("No missions available.", True, COLOR_TEXT)
            surface.blit(none, (40, y))
        else:
            for idx, mission_id in enumerate(missions[:12]):
                mission = MISSIONS[mission_id]
                prefix = "> " if idx == self.index else "  "
                active = " (ACTIVE)" if STATE.active_mission == mission_id else ""
                completed = " (DONE)" if mission_id in STATE.completed_missions else ""
                line = self.font.render(f"{prefix}{mission.name}{active}{completed}", True, COLOR_TEXT)
                surface.blit(line, (40, y))
                y += 26

            if 0 <= self.index < len(missions):
                mission = MISSIONS[missions[self.index]]
                desc = self.font.render(mission.description, True, (200, 200, 210))
                surface.blit(desc, (40, 450))

        if self.message:
            msg = self.font.render(self.message, True, (220, 190, 120))
            surface.blit(msg, (40, 420))

    def _available_missions(self) -> list[str]:
        return [mid for mid in MISSIONS.keys() if mid not in STATE.completed_missions]
