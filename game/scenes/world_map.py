import pygame

from game.assets_manifest import PATHS
from game.constants import COLOR_BG, COLOR_TEXT
from game.scenes.base import Scene
from game.state import STATE
from game.story.flags import FLAG_GOT_TEMPLE_PASS
from game.ui.status_menu import StatusMenu


class WorldMapScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.font_title = pygame.font.SysFont(None, 46)
        self.font_body = pygame.font.SysFont(None, 26)
        self.message = ""
        self.app.audio.play_music(PATHS.music / "world_map.ogg", volume=0.45)
        self.status_menu = StatusMenu()
        self.status_open = False

    def handle_event(self, event: pygame.event.Event) -> Scene | None:
        if event.type != pygame.KEYDOWN:
            return None

        self.message = ""

        if event.key == pygame.K_i:
            self.status_open = not self.status_open
            self.app.audio.play_sfx(
                PATHS.sfx / ("ui_open.wav" if self.status_open else "ui_close.wav"),
                volume=0.35,
            )
            return None

        if event.key == pygame.K_ESCAPE and self.status_open:
            self.status_open = False
            self.app.audio.play_sfx(PATHS.sfx / "ui_close.wav", volume=0.35)
            return None

        if self.status_open:
            return None

        if event.key == pygame.K_ESCAPE:
            from game.scenes.title import TitleScene

            return TitleScene(self.app)

        if event.key == pygame.K_1:
            from game.scenes.home import HomeBaseScene

            return HomeBaseScene(self.app)

        if event.key == pygame.K_2:
            from game.scenes.town import TownScene

            return TownScene(self.app)

        if event.key == pygame.K_3:
            if not STATE.has(FLAG_GOT_TEMPLE_PASS):
                self.message = "Temple Ruins is locked. Talk to the Mayor in town."
                self.app.audio.play_sfx(PATHS.sfx / "error.wav", volume=0.40)
                return None
            from game.world.dungeon_run import DungeonRun
            from game.scenes.dungeon import DungeonScene

            run = DungeonRun(dungeon_id="temple_ruins", dungeon_name="Temple Ruins", max_floor=5)
            return DungeonScene(self.app, run)

        if event.key == pygame.K_4:
            if "relic_shard" not in STATE.completed_missions:
                self.message = "Jungle Cavern is locked. Complete a guild mission."
                return None
            from game.world.dungeon_run import DungeonRun
            from game.scenes.dungeon import DungeonScene

            run = DungeonRun(dungeon_id="jungle_cavern", dungeon_name="Jungle Cavern", max_floor=7)
            return DungeonScene(self.app, run)

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
            "4: Dungeon - Jungle Cavern (Floors 1-7)",
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

        if self.status_open:
            self.status_menu.draw(surface, STATE)
