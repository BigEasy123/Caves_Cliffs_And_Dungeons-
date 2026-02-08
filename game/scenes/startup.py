import pygame

from pathlib import Path

from game.assets_manifest import PATHS
from game.save import load_slot, reset_state
from game.scenes.base import Scene
from game.state import STATE


class StartupScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.font_title = pygame.font.SysFont(None, 54)
        self.font = pygame.font.SysFont(None, 26)
        self.app.audio.play_music(PATHS.music / "title.ogg", volume=0.45)

        self.available = {slot: (Path("saves") / f"save{slot}.json").exists() for slot in (1, 2, 3)}

    def handle_event(self, event: pygame.event.Event) -> Scene | None:
        if event.type != pygame.KEYDOWN:
            return None

        if event.key == pygame.K_ESCAPE:
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            return None

        if any(self.available.values()):
            if event.key == pygame.K_1 and self.available[1]:
                return self._load_then_home(1)
            if event.key == pygame.K_2 and self.available[2]:
                return self._load_then_home(2)
            if event.key == pygame.K_3 and self.available[3]:
                return self._load_then_home(3)
            if event.key in (pygame.K_n, pygame.K_RETURN, pygame.K_KP_ENTER):
                reset_state()
                from game.scenes.name_entry import NameEntryScene
                from game.scenes.title import TitleScene

                return NameEntryScene(self.app, next_scene=TitleScene(self.app))
        else:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                reset_state()
                from game.scenes.name_entry import NameEntryScene
                from game.scenes.title import TitleScene

                return NameEntryScene(self.app, next_scene=TitleScene(self.app))

        return None

    def update(self, dt: float) -> Scene | None:
        return None

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((10, 12, 18))

        title = self.font_title.render("Continue?", True, (240, 240, 245))
        surface.blit(title, (40, 70))

        y = 170
        if any(self.available.values()):
            surface.blit(self.font.render("Press 1/2/3 to load a save slot, or N/Enter for new game.", True, (220, 220, 230)), (40, y))
            y += 40
            for slot in (1, 2, 3):
                label = f"{slot}: {'Save present' if self.available[slot] else '—'}"
                surface.blit(self.font.render(label, True, (200, 200, 210)), (60, y))
                y += 30
        else:
            surface.blit(self.font.render("No saves found. Press Enter to start.", True, (220, 220, 230)), (40, y))

        surface.blit(self.font.render("Esc: Quit", True, (200, 200, 210)), (40, 440))

    def _load_then_home(self, slot: int) -> Scene:
        ok = load_slot(slot)
        if ok:
            self.app.toast(f"Loaded (slot {slot})")
            if not (STATE.player_name or "").strip():
                from game.scenes.name_entry import NameEntryScene
                from game.scenes.home import HomeBaseScene

                return NameEntryScene(
                    self.app,
                    next_scene=HomeBaseScene(self.app),
                    prompt="Enter your name (save was missing it)",
                    autosave_slot=slot,
                )
            from game.scenes.home import HomeBaseScene

            return HomeBaseScene(self.app)
        self.app.toast(f"No save in slot {slot}")
        from game.scenes.title import TitleScene

        return TitleScene(self.app)
