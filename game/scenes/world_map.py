import pygame

from game.constants import COLOR_BG, COLOR_TEXT
from game.scenes.base import Scene
from game.state import STATE
from game.story.flags import FLAG_GOT_TEMPLE_PASS


class WorldMapScene(Scene):
    def __init__(self) -> None:
        self.font_title = pygame.font.SysFont(None, 46)
        self.font_body = pygame.font.SysFont(None, 26)
        self.message = ""

    def handle_event(self, event: pygame.event.Event) -> Scene | None:
        if event.type != pygame.KEYDOWN:
            return None

        if event.key == pygame.K_ESCAPE:
            from game.scenes.title import TitleScene

            return TitleScene()

        if event.key == pygame.K_1:
            from game.scenes.home import HomeBaseScene

            return HomeBaseScene()

        if event.key == pygame.K_2:
            from game.scenes.town import TownScene

            return TownScene()

        if event.key == pygame.K_3:
            if not STATE.has(FLAG_GOT_TEMPLE_PASS):
                self.message = "Temple Ruins is locked. Talk to the Mayor in town."
                return None
            from game.world.dungeon_run import DungeonRun
            from game.scenes.dungeon import DungeonScene

            run = DungeonRun(dungeon_id="temple_ruins", dungeon_name="Temple Ruins", max_floor=5)
            return DungeonScene(run)

        return None

    def update(self, dt: float) -> Scene | None:
        return None

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)

        title = self.font_title.render("World Map", True, COLOR_TEXT)
        surface.blit(title, (40, 55))

        items = [
            "1: Home Base",
            "2: Town",
            "3: Dungeon - Temple Ruins (Floors 1-5)",
            "Esc: Back to title",
        ]
        y = 140
        for item in items:
            surf = self.font_body.render(item, True, COLOR_TEXT)
            surface.blit(surf, (40, y))
            y += 34

        if self.message:
            msg = self.font_body.render(self.message, True, (220, 190, 120))
            surface.blit(msg, (40, y + 10))
