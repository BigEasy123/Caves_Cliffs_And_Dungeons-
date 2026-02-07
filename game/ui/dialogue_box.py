from __future__ import annotations

import pygame

from game.constants import COLOR_TEXT


class DialogueBox:
    def __init__(self) -> None:
        self.font = pygame.font.SysFont(None, 24)
        self.font_speaker = pygame.font.SysFont(None, 28)
        self.padding = 14

    def draw(self, surface: pygame.Surface, *, speaker: str, line: str) -> None:
        width, height = surface.get_size()
        box_h = int(height * 0.32)
        rect = pygame.Rect(0, height - box_h, width, box_h)

        overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        surface.blit(overlay, rect.topleft)

        pygame.draw.rect(surface, (255, 255, 255), rect, 2)

        y = rect.top + self.padding
        speaker_surf = self.font_speaker.render(speaker, True, COLOR_TEXT)
        surface.blit(speaker_surf, (rect.left + self.padding, y))
        y += speaker_surf.get_height() + 10

        for wrapped in _wrap_text(self.font, line, rect.width - self.padding * 2):
            surf = self.font.render(wrapped, True, COLOR_TEXT)
            surface.blit(surf, (rect.left + self.padding, y))
            y += surf.get_height() + 4

        hint = self.font.render("Enter/E: next   Esc: close", True, (200, 200, 210))
        surface.blit(hint, (rect.left + self.padding, rect.bottom - self.padding - hint.get_height()))


def _wrap_text(font: pygame.font.Font, text: str, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]

    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines

