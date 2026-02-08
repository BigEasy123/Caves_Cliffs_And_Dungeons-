from __future__ import annotations

import pygame

from game.assets_manifest import PATHS
from game.constants import COLOR_BG, COLOR_TEXT
from game.scenes.base import Scene
from game.state import STATE
from game.story.flags import FLAG_SEEN_INTRO_CUTSCENE


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


class IntroCutsceneScene(Scene):
    def __init__(self, app, *, next_scene: Scene) -> None:
        super().__init__(app)
        self.next_scene = next_scene
        self.font_title = pygame.font.SysFont(None, 46)
        self.font = pygame.font.SysFont(None, 26)
        self.font_small = pygame.font.SysFont(None, 20)
        self.index = 0

        self.app.audio.play_music(PATHS.music / "title.ogg", volume=0.35)

        player = (STATE.player_name or "").strip() or "Adventurer"
        self.pages: list[dict[str, str]] = [
            {
                "title": "Origins",
                "body": (
                    f"{player} should have been failing out.\n\n"
                    "Most classes felt like noise. Nights blurred into the same loopâ€”"
                    "cheap light, stale air, and the weight of being stuck.\n\n"
                    "Except for one thing: history. Archaeology. The feeling that the past still had teeth."
                ),
            },
            {
                "title": "The Offer",
                "body": (
                    "Your professor calls you in after hours.\n\n"
                    "\"I read your work twice,\" he says. \"You're not dull. You're starving.\"\n\n"
                    "He offers a deal: stay enrolledâ€¦ if you study abroad with a research guild."
                ),
            },
            {
                "title": "The Truth",
                "body": (
                    "Officially, the Guild funds expeditions.\n\n"
                    "Unofficiallyâ€¦ it protects the timeline from a rising society calling itself the "
                    "Children of the Nephil.\n\n"
                    "\"They want to corrupt history,\" the Professor warns. "
                    "\"To send humanity backward, one fracture at a time.\""
                ),
            },
            {
                "title": "Arrival",
                "body": (
                    "You arrive in a small town that pretends itâ€™s ordinary.\n\n"
                    "But the ground has been trembling. Old ruins have reopened. "
                    "Strangers in red move like they already own the story.\n\n"
                    "The Guild doesnâ€™t need a hero.\n"
                    "It needs someone who can go downâ€”and come back up."
                ),
            },
        ]

        self._reflow_cache: dict[tuple[int, int], list[str]] = {}

    def handle_event(self, event: pygame.event.Event) -> Scene | None:
        if event.type != pygame.KEYDOWN:
            return None

        if event.key == pygame.K_ESCAPE:
            STATE.set(FLAG_SEEN_INTRO_CUTSCENE)
            self.app.audio.play_sfx(PATHS.sfx / "ui_close.wav", volume=0.35)
            return self.next_scene

        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_e):
            self.index += 1
            self.app.audio.play_sfx(PATHS.sfx / "confirm.wav", volume=0.30)
            if self.index >= len(self.pages):
                STATE.set(FLAG_SEEN_INTRO_CUTSCENE)
                return self.next_scene
        return None

    def update(self, dt: float) -> Scene | None:
        return None

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        w, h = surface.get_size()

        page = self.pages[min(self.index, len(self.pages) - 1)]
        title = self.font_title.render(page["title"], True, COLOR_TEXT)
        surface.blit(title, (40, 60))

        body_rect = pygame.Rect(40, 120, w - 80, h - 200)
        pygame.draw.rect(surface, (0, 0, 0), body_rect)
        pygame.draw.rect(surface, (255, 255, 255), body_rect, 2)

        max_width = body_rect.width - 28
        cache_key = (self.index, max_width)
        if cache_key not in self._reflow_cache:
            raw = page["body"].replace("\r\n", "\n").replace("\r", "\n")
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
            hint = "Enter/Space: begin  |  Esc: begin"
        hint_surf = self.font_small.render(hint, True, (200, 200, 210))
        surface.blit(hint_surf, (40, h - 44))

