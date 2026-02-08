from __future__ import annotations

import pygame

from game.assets_manifest import PATHS
from game.scenes.base import Scene
from game.state import STATE


class NameEntryScene(Scene):
    def __init__(self, app, *, next_scene: Scene | None = None, prompt: str | None = None, autosave_slot: int | None = None) -> None:
        super().__init__(app)
        self.font_title = pygame.font.SysFont(None, 54)
        self.font = pygame.font.SysFont(None, 26)
        self.font_small = pygame.font.SysFont(None, 22)
        self.next_scene = next_scene
        self.prompt = prompt or "Enter your name"
        self.autosave_slot = autosave_slot
        self.name = (STATE.player_name or "").strip()
        if not self.name:
            self.name = ""
        self._blink = 0.0
        self.app.audio.play_music(PATHS.music / "title.ogg", volume=0.45)

    def handle_event(self, event: pygame.event.Event) -> Scene | None:
        if event.type != pygame.KEYDOWN:
            return None

        if event.key == pygame.K_ESCAPE:
            from game.scenes.startup import StartupScene

            return StartupScene(self.app)

        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            cleaned = " ".join(self.name.strip().split())
            if not cleaned:
                self.app.audio.play_sfx(PATHS.sfx / "error.wav", volume=0.40)
                return None
            STATE.player_name = cleaned[:24]
            if self.autosave_slot is not None:
                from game.save import save_slot

                save_slot(self.autosave_slot)
                self.app.toast(f"Saved name: {STATE.player_name} (slot {self.autosave_slot})")
            else:
                self.app.toast(f"Name set: {STATE.player_name}")
            self.app.audio.play_sfx(PATHS.sfx / "confirm.wav", volume=0.35)
            if self.next_scene is not None:
                return self.next_scene
            from game.scenes.title import TitleScene

            return TitleScene(self.app)

        if event.key == pygame.K_BACKSPACE:
            self.name = self.name[:-1]
            return None

        if event.key == pygame.K_SPACE:
            if len(self.name) < 24 and (not self.name.endswith(" ")):
                self.name += " "
            return None

        ch = getattr(event, "unicode", "")
        if ch and ch.isprintable():
            # Allow letters/numbers/basic punctuation; keep it safe for filenames even if we don't use it as one.
            if ch.isalnum() or ch in ("-", "_", ".", "'"):
                if len(self.name) < 24:
                    self.name += ch
        return None

    def update(self, dt: float) -> Scene | None:
        self._blink += dt
        return None

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((10, 12, 18))

        title = self.font_title.render(self.prompt, True, (240, 240, 245))
        surface.blit(title, (40, 70))

        y = 160
        surface.blit(self.font.render("Type your character name, then press Enter to confirm.", True, (220, 220, 230)), (40, y))
        y += 34
        surface.blit(self.font_small.render("Esc: back | Max 24 chars | Allowed: letters, numbers, - _ . '", True, (200, 200, 210)), (40, y))

        box = pygame.Rect(40, 250, surface.get_width() - 80, 54)
        pygame.draw.rect(surface, (0, 0, 0), box)
        pygame.draw.rect(surface, (255, 255, 255), box, 2)

        shown = self.name
        cursor = "_" if int(self._blink * 2) % 2 == 0 else " "
        line = self.font.render(shown + cursor, True, (245, 245, 245))
        surface.blit(line, (box.left + 12, box.top + 14))
