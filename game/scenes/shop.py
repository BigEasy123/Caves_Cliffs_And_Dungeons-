import pygame

from game.assets_manifest import PATHS
from game.constants import COLOR_BG, COLOR_TEXT
from game.items import ITEMS, get_item
from game.scenes.base import Scene
from game.state import STATE


class ShopScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.app.audio.play_music(PATHS.music / "town.ogg", volume=0.45)
        self.font_title = pygame.font.SysFont(None, 42)
        self.font = pygame.font.SysFont(None, 24)
        self.index = 0
        self.mode = "buy"  # buy | sell
        self.message = ""

    def handle_event(self, event: pygame.event.Event) -> Scene | None:
        if event.type != pygame.KEYDOWN:
            return None

        if event.key == pygame.K_ESCAPE:
            from game.scenes.town import TownScene

            return TownScene(self.app)

        if event.key == pygame.K_TAB:
            self.mode = "sell" if self.mode == "buy" else "buy"
            self.index = 0
            self.message = ""
            return None

        items = self._items()
        if not items:
            return None

        if event.key in (pygame.K_UP, pygame.K_w):
            self.index = (self.index - 1) % len(items)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.index = (self.index + 1) % len(items)
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_e):
            item_id = items[self.index]
            if self.mode == "buy":
                self._buy(item_id)
            else:
                self._sell(item_id)
        return None

    def update(self, dt: float) -> Scene | None:
        return None

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        title = self.font_title.render("Shop", True, COLOR_TEXT)
        surface.blit(title, (40, 50))

        header = self.font.render(
            f"Gold: {STATE.gold} | Tab: {self.mode.upper()} | Enter/E: confirm | Esc: back",
            True,
            COLOR_TEXT,
        )
        surface.blit(header, (40, 95))

        y = 135
        for idx, item_id in enumerate(self._items()[:12]):
            item = get_item(item_id)
            price = item.buy_price if self.mode == "buy" else item.sell_price
            count = STATE.item_count(item_id)
            prefix = "> " if idx == self.index else "  "
            suffix = f" ({count})" if self.mode == "sell" else ""
            line = self.font.render(f"{prefix}{item.name} - {price}g{suffix}", True, COLOR_TEXT)
            surface.blit(line, (40, y))
            y += 26

        if self.message:
            msg = self.font.render(self.message, True, (220, 190, 120))
            surface.blit(msg, (40, 450))

    def _items(self) -> list[str]:
        if self.mode == "buy":
            return [item_id for item_id, item in ITEMS.items() if item.buy_price > 0]
        return [item_id for item_id, count in STATE.inventory.items() if count > 0 and item_id in ITEMS]

    def _buy(self, item_id: str) -> None:
        item = get_item(item_id)
        if STATE.gold < item.buy_price:
            self.message = "Not enough gold."
            return
        STATE.gold -= item.buy_price
        STATE.add_item(item_id, 1)
        self.message = f"Bought {item.name}."

    def _sell(self, item_id: str) -> None:
        item = get_item(item_id)
        if item.sell_price <= 0:
            self.message = "Can't sell that."
            return
        if not STATE.remove_item(item_id, 1):
            return
        STATE.gold += item.sell_price
        self.message = f"Sold {item.name}."

