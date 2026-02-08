import pygame

from game.constants import COLOR_BG, COLOR_TEXT
from game.items import ITEMS, get_item
from game.scenes.base import Scene
from game.state import STATE


class InventoryScene(Scene):
    def __init__(self, app, *, return_scene: Scene) -> None:
        super().__init__(app)
        self.return_scene = return_scene
        self.font_title = pygame.font.SysFont(None, 42)
        self.font = pygame.font.SysFont(None, 24)
        self.index = 0
        self.message = ""

    def handle_event(self, event: pygame.event.Event) -> Scene | None:
        if event.type != pygame.KEYDOWN:
            return None

        if event.key in (pygame.K_ESCAPE, pygame.K_b):
            return self.return_scene

        items = self._items()
        if not items:
            return None

        if event.key in (pygame.K_UP, pygame.K_w):
            self.index = (self.index - 1) % len(items)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.index = (self.index + 1) % len(items)
        elif event.key == pygame.K_d:
            item_id = items[self.index]
            if STATE.remove_item(item_id, 1):
                self.message = f"Dropped 1x {get_item(item_id).name if item_id in ITEMS else item_id}."
                if self.index >= len(self._items()):
                    self.index = max(0, len(self._items()) - 1)
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_e):
            item_id = items[self.index]
            self._equip_or_use(item_id)
        return None

    def update(self, dt: float) -> Scene | None:
        return None

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        title = self.font_title.render("Inventory", True, COLOR_TEXT)
        surface.blit(title, (40, 40))

        header = self.font.render(
            "Up/Down select  Enter/E equip/use  D drop  Esc/B back",
            True,
            COLOR_TEXT,
        )
        surface.blit(header, (40, 85))

        surface.blit(self.font.render(f"Gold: {STATE.gold}", True, COLOR_TEXT), (40, 115))
        surface.blit(self.font.render(f"ATK: {STATE.attack()}  DEF: {STATE.defense()}", True, COLOR_TEXT), (40, 140))
        surface.blit(self.font.render(f"Weapon: {STATE.equipment.get('weapon') or '-'}", True, COLOR_TEXT), (40, 165))
        surface.blit(self.font.render(f"Armor: {STATE.equipment.get('armor') or '-'}", True, COLOR_TEXT), (40, 190))

        items = self._items()
        y = 230
        for idx, item_id in enumerate(items[:12]):
            item = get_item(item_id) if item_id in ITEMS else None
            count = STATE.item_count(item_id)
            prefix = "> " if idx == self.index else "  "
            name = item.name if item else item_id
            line = self.font.render(f"{prefix}{name} x{count}", True, COLOR_TEXT)
            surface.blit(line, (40, y))
            y += 24

        if items:
            item_id = items[self.index]
            item = get_item(item_id) if item_id in ITEMS else None
            desc = item.description if item else ""
            surface.blit(self.font.render(desc, True, (200, 200, 210)), (40, 520))

        if self.message:
            surface.blit(self.font.render(self.message, True, (220, 190, 120)), (40, 490))

    def _items(self) -> list[str]:
        return [item_id for item_id, count in STATE.inventory.items() if count > 0]

    def _equip_or_use(self, item_id: str) -> None:
        if item_id not in ITEMS:
            return
        item = get_item(item_id)
        if item.slot in ("weapon", "armor"):
            STATE.equip(item.slot, item_id)
            self.message = f"Equipped {item.name}."
            return
        if item.effects and "heal_hp" in item.effects:
            if STATE.hp >= STATE.max_hp:
                self.message = "HP already full."
                return
            if STATE.remove_item(item_id, 1):
                heal = int(item.effects["heal_hp"])
                STATE.hp = min(STATE.max_hp, STATE.hp + heal)
                self.message = f"Used {item.name} (+{heal} HP)."

