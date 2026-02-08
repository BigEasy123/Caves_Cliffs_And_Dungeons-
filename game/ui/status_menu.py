from __future__ import annotations

import pygame

from game.constants import COLOR_TEXT
from game.items import ITEMS, get_item
from game.state import GameState
from game.story.chapters import chapter_title
from game.story.quest_manager import mission_objective_text


class StatusMenu:
    def __init__(self) -> None:
        self.font_title = pygame.font.SysFont(None, 40)
        self.font = pygame.font.SysFont(None, 24)

    def draw(self, surface: pygame.Surface, state: GameState) -> None:
        width, height = surface.get_size()
        rect = pygame.Rect(60, 60, width - 120, height - 120)

        overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        surface.blit(overlay, rect.topleft)
        pygame.draw.rect(surface, (255, 255, 255), rect, 2)

        title = self.font_title.render("Status", True, COLOR_TEXT)
        surface.blit(title, (rect.left + 16, rect.top + 14))

        left_x = rect.left + 16
        y = rect.top + 60

        lines = [
            f"Name: {(state.player_name or '').strip() or '-'}",
            f"HP: {state.hp}/{state.max_hp_total()}",
            f"ATK: {state.attack()}  DEF: {state.defense()}",
            f"Gold: {state.gold}",
            f"Combat Lv: {state.combat_level}  XP: {state.combat_xp}/{state.combat_xp_to_next(state.combat_level)}",
            f"Guild Rank: {state.guild_rank}  XP: {state.guild_xp}/{state.guild_xp_to_next(state.guild_rank)}",
            f"Story: Chapter {state.chapter} — {chapter_title(state.chapter)}",
            f"Active mission: {state.active_mission or 'None'}",
            (f"Objective: {mission_objective_text(state.active_mission)}" if state.active_mission else "Objective: -"),
            f"Completed missions: {len(state.completed_missions)}",
        ]
        for line in lines:
            surf = self.font.render(line, True, COLOR_TEXT)
            surface.blit(surf, (left_x, y))
            y += 26

        y += 10
        inv_title = self.font.render("Items:", True, (210, 210, 220))
        surface.blit(inv_title, (left_x, y))
        y += 26

        items = _sorted_inventory(state)
        if not items:
            empty = self.font.render("(empty)", True, COLOR_TEXT)
            surface.blit(empty, (left_x, y))
        else:
            for item_id, count in items[:12]:
                name = get_item(item_id).name if item_id in ITEMS else item_id
                surf = self.font.render(f"- {name} x{count}", True, COLOR_TEXT)
                surface.blit(surf, (left_x, y))
                y += 22

        hint = self.font.render("I/Esc: close", True, (200, 200, 210))
        surface.blit(hint, (rect.left + 16, rect.bottom - 16 - hint.get_height()))


def _sorted_inventory(state: GameState) -> list[tuple[str, int]]:
    pairs = [(item_id, count) for item_id, count in state.inventory.items() if count > 0]
    pairs.sort(key=lambda p: get_item(p[0]).name if p[0] in ITEMS else p[0])
    return pairs
