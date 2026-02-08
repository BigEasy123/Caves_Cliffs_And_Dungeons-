import pygame

from game.constants import COLOR_BG, COLOR_TEXT, TITLE
from game.assets_manifest import PATHS
from game.scenes.base import Scene
from game.state import STATE
from game.story.flags import FLAG_SEEN_INTRO_CUTSCENE


class TitleScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.font_title = pygame.font.SysFont(None, 56)
        self.font_body = pygame.font.SysFont(None, 26)
        self.app.audio.play_music(PATHS.music / "title.ogg", volume=0.45)

    def handle_event(self, event: pygame.event.Event) -> Scene | None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if not (STATE.player_name or "").strip():
                    from game.scenes.name_entry import NameEntryScene

                    return NameEntryScene(self.app, next_scene=self)
                if int(getattr(STATE, "chapter", 1)) == 1 and not STATE.has(FLAG_SEEN_INTRO_CUTSCENE):
                    from game.scenes.home import HomeBaseScene
                    from game.scenes.intro_cutscene import IntroCutsceneScene

                    return IntroCutsceneScene(self.app, next_scene=HomeBaseScene(self.app))
                from game.scenes.home import HomeBaseScene

                return HomeBaseScene(self.app)
            if event.key == pygame.K_p:
                from game.scenes.platformer import PlatformerScene

                return PlatformerScene(self.app)
            if event.key == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
        return None

    def update(self, dt: float) -> Scene | None:
        return None

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)

        title_surf = self.font_title.render(TITLE, True, COLOR_TEXT)
        body1 = self.font_body.render("Enter: Start Adventure (Home Base)", True, COLOR_TEXT)
        body2 = self.font_body.render("P: Play platformer prototype", True, COLOR_TEXT)
        body3 = self.font_body.render("Esc: Quit", True, COLOR_TEXT)

        surface.blit(title_surf, (40, 70))
        surface.blit(body1, (40, 170))
        surface.blit(body2, (40, 205))
        surface.blit(body3, (40, 240))
