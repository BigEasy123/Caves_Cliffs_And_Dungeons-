from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.assets_manifest import PATHS
from game.constants import COLOR_BG, COLOR_TEXT
from game.scenes.base import Scene
from game.state import STATE


@dataclass(frozen=True)
class CutscenePage:
    title: str
    body: str


def _wrap_text(font: pygame.font.Font, text: str, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    cur = words[0]
    for w in words[1:]:
        test = cur + " " + w
        if font.size(test)[0] <= max_width:
            cur = test
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def _format(text: str) -> str:
    player = (getattr(STATE, "player_name", "") or "").strip() or "Adventurer"
    return text.format(player=player)


class CutsceneScene(Scene):
    def __init__(
        self,
        app,
        *,
        pages: list[CutscenePage],
        next_scene: Scene,
        music: str = "title.ogg",
    ) -> None:
        super().__init__(app)
        self.pages = pages or [CutscenePage(title="", body="...")]
        self.next_scene = next_scene
        self.index = 0
        self.font_title = pygame.font.SysFont(None, 46)
        self.font = pygame.font.SysFont(None, 26)
        self.font_small = pygame.font.SysFont(None, 20)
        self._reflow_cache: dict[tuple[int, int], list[str]] = {}

        # Keep volume slightly low; these are narrative beats between gameplay loops.
        try:
            self.app.audio.play_music(PATHS.music / music, volume=0.35)
        except Exception:
            pass

    def handle_event(self, event: pygame.event.Event) -> Scene | None:
        if event.type != pygame.KEYDOWN:
            return None

        if event.key == pygame.K_ESCAPE:
            self.app.audio.play_sfx(PATHS.sfx / "ui_close.wav", volume=0.35)
            return self.next_scene

        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_e):
            self.index += 1
            self.app.audio.play_sfx(PATHS.sfx / "confirm.wav", volume=0.30)
            if self.index >= len(self.pages):
                return self.next_scene
        return None

    def update(self, dt: float) -> Scene | None:
        return None

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        w, h = surface.get_size()

        page = self.pages[min(self.index, len(self.pages) - 1)]
        title = self.font_title.render(_format(page.title), True, COLOR_TEXT)
        surface.blit(title, (40, 60))

        body_rect = pygame.Rect(40, 120, w - 80, h - 200)
        pygame.draw.rect(surface, (0, 0, 0), body_rect)
        pygame.draw.rect(surface, (255, 255, 255), body_rect, 2)

        max_width = body_rect.width - 28
        cache_key = (self.index, max_width)
        if cache_key not in self._reflow_cache:
            raw = _format(page.body).replace("\r\n", "\n").replace("\r", "\n")
            out: list[str] = []
            for para in raw.split("\n"):
                if not para.strip():
                    out.append("")
                    continue
                out.extend(_wrap_text(self.font, para.strip(), max_width))
            self._reflow_cache[cache_key] = out

        y = body_rect.top + 16
        for line in self._reflow_cache[cache_key]:
            if y > body_rect.bottom - 28:
                break
            if not line:
                y += self.font.get_height()
                continue
            surf = self.font.render(line, True, (235, 235, 240))
            surface.blit(surf, (body_rect.left + 14, y))
            y += self.font.get_height() + 4

        hint = "Enter/Space: next  |  Esc: skip"
        if self.index >= len(self.pages) - 1:
            hint = "Enter/Space: continue  |  Esc: continue"
        hint_surf = self.font_small.render(hint, True, (200, 200, 210))
        surface.blit(hint_surf, (40, h - 44))

